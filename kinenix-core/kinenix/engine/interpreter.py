import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .evaluator import VariableEvaluator
from .logger import ExecutionLogger
from ..actions.registry import ActionRegistry
from ..actions.flow_control import SubflowExecutionError, is_business_error
from ..models.context import ExecutionContext, StepResult, FailureDetails, local_now
from ..models.flow import FlowDefinition, Step


class FlowInterpreter:
    """
    Interpreter that parses FlowDefinition, evaluates expressions, and executes steps sequentially.
    Supports modular subflow execution (flow.call), early exit (flow.return), and hierarchical logging.
    """

    def __init__(
        self,
        logger: Optional[ExecutionLogger] = None,
        max_depth: int = 10,
        call_stack: Optional[List[str]] = None,
        auto_close_browser: bool = True
    ):
        self.logger = logger or ExecutionLogger()
        self.max_depth = max_depth
        self.call_stack: List[str] = call_stack or []
        self.auto_close_browser = auto_close_browser
        self._step_map: Dict[str, Step] = {}

    def _build_step_map(self, steps: List[Step]) -> Dict[str, Step]:
        step_map: Dict[str, Step] = {}
        for s in steps:
            step_map[s.id] = s
            if s.sub_steps:
                step_map.update(self._build_step_map(s.sub_steps))
            if s.else_steps:
                step_map.update(self._build_step_map(s.else_steps))
        return step_map

    def _cleanup_resources(self, context: ExecutionContext) -> None:
        """
        Safely closes external resources (Playwright browser, driver instances)
        to prevent zombie / orphan processes upon flow completion or failure.
        Only executed at the root flow level (not inside subflows sharing parent resources).
        """
        if self.call_stack or context.get_variable("__shared_browser__"):
            return

        if not self.auto_close_browser:
            return

        browser = context.get_variable("__playwright_browser__")
        pw = context.get_variable("__playwright_pw__")

        if browser:
            try:
                is_connected = getattr(browser, "is_connected", None)
                if is_connected is None or (callable(is_connected) and is_connected()):
                    browser.close()
                    self.logger.logger.info("Auto-cleanup: Closed active Playwright browser.")
            except Exception as e:
                self.logger.logger.debug(f"Auto-cleanup: Error closing browser: {e}")
            finally:
                context.set_variable("__playwright_browser__", None)
                context.set_variable("__playwright_page__", None)

        if pw:
            try:
                pw.stop()
                self.logger.logger.info("Auto-cleanup: Stopped Playwright instance.")
            except Exception as e:
                self.logger.logger.debug(f"Auto-cleanup: Error stopping Playwright: {e}")
            finally:
                context.set_variable("__playwright_pw__", None)

    def _try_capture_failure_screenshot(self, step: Step, context: ExecutionContext) -> Optional[str]:
        try:
            page = context.get_variable("__playwright_page__")
            if page and hasattr(page, "screenshot"):
                is_closed = getattr(page, "is_closed", lambda: False)
                if callable(is_closed) and is_closed():
                    return None

                config_data = context.get_variable("config") or {}
                error_dir_str = config_data.get("error_dir") or config_data.get("error_screenshot_dir")

                flow_dir_str = context.get_variable("__flow_dir__")
                base_dir = Path(flow_dir_str) if flow_dir_str else Path.cwd()

                if error_dir_str:
                    err_dir = Path(error_dir_str)
                    if not err_dir.is_absolute():
                        err_dir = (base_dir / error_dir_str).resolve()
                else:
                    err_dir = (base_dir / "output" / "errors").resolve()

                err_dir.mkdir(parents=True, exist_ok=True)
                timestamp_str = local_now().strftime("%Y%m%d_%H%M%S")
                clean_step_id = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in step.id)
                shot_path = err_dir / f"error_{clean_step_id}_{timestamp_str}.png"

                page.screenshot(path=str(shot_path), full_page=True)
                shot_path_str = str(shot_path.resolve())
                context.set_variable("__last_error_screenshot__", shot_path_str)
                self.logger.logger.warning(f"Auto-captured failure screenshot: {shot_path_str}")
                return shot_path_str
        except Exception as snap_err:
            self.logger.logger.debug(f"Failed to auto-capture failure screenshot: {str(snap_err)}")
        return None

    def _diagnose_failure(self, step: Step, exc: Exception, context: Optional[ExecutionContext] = None) -> FailureDetails:
        exc_class = type(exc).__name__
        err_msg = str(exc)
        error_type = "Business" if is_business_error(exc) else "Technical"

        error_screenshot_path = None
        if context:
            error_screenshot_path = self._try_capture_failure_screenshot(step, context)

        if isinstance(exc, SubflowExecutionError):
            root_cause = f"Subflow execution failed in '{exc.subflow_name}': {err_msg}"
            suggested_fix = f"Inspect child subflow '{exc.subflow_name}' definition and input parameters passed in step '{step.id}'."
        elif isinstance(exc, FileNotFoundError) or ("not found" in err_msg.lower() and "file" in err_msg.lower()):
            root_cause = f"Required file was not found during execution of step '{step.name}'."
            suggested_fix = "Verify the target file path exists and that relative paths are correctly anchored to the flow project directory."
        elif "timeout" in err_msg.lower() or "waiting for" in err_msg.lower():
            root_cause = f"Operation timed out waiting for element or network response in step '{step.name}' (Action: {step.action})."
            suggested_fix = "Verify target web page/API is reachable, inspect selector validity, or increase action timeout parameter."
        elif "locator" in err_msg.lower() or "strict mode violation" in err_msg.lower() or "selector" in err_msg.lower():
            root_cause = f"Web element could not be uniquely located on page in step '{step.name}'."
            suggested_fix = "Check DOM changes on target page and update selector/label to be more resilient."
        elif isinstance(exc, KeyError):
            root_cause = f"Referenced variable or key {err_msg} is missing from execution context."
            suggested_fix = "Ensure preceding steps initialize this variable or verify variable expression spelling."
        else:
            root_cause = f"Unhandled {exc_class} in step '{step.name}' ({step.action}): {err_msg}"
            suggested_fix = f"Inspect input parameters to step '{step.id}' ({step.action}) and verify prerequisite conditions."

        return FailureDetails(
            failed_step_id=step.id,
            failed_step_name=step.name,
            action=step.action,
            error_type=error_type,
            exception_class=exc_class,
            error_message=err_msg,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            error_screenshot_path=error_screenshot_path
        )

    def run_flow(self, flow_def: FlowDefinition, initial_vars: Optional[Dict[str, Any]] = None) -> ExecutionContext:
        context = ExecutionContext(flow_name=flow_def.name)

        # 1. Flow definition default variables (base priority)
        if flow_def.variables:
            for k, v in flow_def.variables.items():
                context.set_variable(k, v)

        # 2. Set initial caller variables (e.g. __flow_dir__)
        if initial_vars:
            for k, v in initial_vars.items():
                context.set_variable(k, v)

        # 3. Auto-load project configuration (config.json & .env) from flow bundle directory
        flow_dir_str = context.get_variable("__flow_dir__")
        if flow_dir_str:
            self._load_bundle_configs(Path(flow_dir_str), context)

        # 4. Caller explicit initial_vars take highest priority
        if initial_vars:
            for k, v in initial_vars.items():
                context.set_variable(k, v)

        # Build step map and validate any fallback_step_id upfront
        self._step_map = self._build_step_map(flow_def.steps)
        for s_id, s in self._step_map.items():
            if s.error_handler and s.error_handler.fallback_step_id:
                fb_target = s.error_handler.fallback_step_id
                if fb_target not in self._step_map:
                    raise ValueError(
                        f"Step '{s_id}' specifies fallback_step_id '{fb_target}' which does not exist in flow definition."
                    )

        start_time = local_now()

        try:
            for step in flow_def.steps:
                if context.get_variable("__early_exit__"):
                    break
                self._execute_step(step, context)
            context.is_completed = True
        except Exception as e:
            context.has_error = True
            if context.failure_details is None:
                exc_class = type(e).__name__
                context.failure_details = FailureDetails(
                    failed_step_id="flow_run",
                    failed_step_name="Flow Execution",
                    action="flow.run",
                    error_type="Technical",
                    exception_class=exc_class,
                    error_message=str(e),
                    root_cause=f"Flow execution failed with unhandled exception: {str(e)}",
                    suggested_fix="Inspect execution logs and subflow definitions."
                )
            self.logger.logger.error(f"Flow execution failed with unhandled exception: {str(e)}")
        finally:
            self._cleanup_resources(context)

        end_time = local_now()
        total_duration = (end_time - start_time).total_seconds()

        context.metrics.total_steps = len(context.step_results)
        context.metrics.successful_steps = sum(1 for r in context.step_results if r.status == "success")
        context.metrics.failed_steps = sum(1 for r in context.step_results if r.status == "failed")
        context.metrics.skipped_steps = sum(1 for r in context.step_results if r.status == "skipped")
        context.metrics.total_duration_seconds = total_duration

        self.logger.log_execution_summary(context)
        return context

    def _execute_step(self, step: Step, context: ExecutionContext) -> None:
        if context.get_variable("__early_exit__"):
            return

        self.logger.log_step_start(step.id, step.name, step.action)
        start_time = local_now()

        evaluated_params = VariableEvaluator.evaluate_value(step.parameters, context.variables)

        if step.condition and step.action == "logic.if":
            # For logic.if, `condition` chooses the branch. As a step gate it would skip the step, and Else-steps would never run
            if "condition" not in evaluated_params and "left" not in evaluated_params:
                evaluated_params = dict(evaluated_params)
                evaluated_params["condition"] = VariableEvaluator.evaluate_value(step.condition, context.variables)
        elif step.condition:
            eval_cond = VariableEvaluator.evaluate_value(step.condition, context.variables)
            if not self._evaluate_condition_expr(eval_cond):
                result = StepResult(
                    step_id=step.id,
                    step_name=step.name,
                    action=step.action,
                    status="skipped",
                    start_time=start_time,
                    end_time=local_now(),
                    duration_seconds=0.0,
                    output={"skipped_reason": f"Condition '{step.condition}' not met"}
                )
                context.step_results.append(result)
                self.logger.log_step_result(result)
                return

        if step.action == "logic.loop":
            self._handle_loop_step(step, evaluated_params, context, start_time)
            return

        if step.action == "logic.if":
            self._handle_if_step(step, evaluated_params, context, start_time)
            return

        if step.action == "flow.return":
            self._handle_flow_return_step(step, evaluated_params, context, start_time)
            return

        def _invoke_step_action() -> Any:
            if step.action == "flow.call":
                self._handle_flow_call_step(step, evaluated_params, context, start_time)
                return None
            action_cls = ActionRegistry.get(step.action)
            action_instance = action_cls()
            output = action_instance.execute(evaluated_params, context)
            if step.output_var and output is not None:
                context.set_variable(step.output_var, output)
            return output

        max_retries = 0
        retry_interval = 1.0
        if step.error_handler and step.error_handler.on_error == "retry":
            max_retries = max(0, step.error_handler.max_retries)
            retry_interval = max(0.0, step.error_handler.retry_interval)

        attempt = 0
        last_error = None
        while attempt <= max_retries:
            try:
                output = _invoke_step_action()
                end_time = local_now()
                duration = (end_time - start_time).total_seconds()

                result = StepResult(
                    step_id=step.id,
                    step_name=step.name,
                    action=step.action,
                    status="success",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    output=output
                )
                context.step_results.append(result)
                self.logger.log_step_result(result)
                return
            except Exception as e:
                last_error = e
                # Business errors (bad data, a rule not met) fail the same way on every attempt
                if attempt < max_retries and not is_business_error(e):
                    attempt += 1
                    self.logger.logger.warning(
                        f"Step '{step.id}' ({step.name}) failed attempt {attempt}/{max_retries + 1}: {e}. "
                        f"Retrying in {retry_interval}s..."
                    )
                    time.sleep(retry_interval)
                else:
                    break

        end_time = local_now()
        duration = (end_time - start_time).total_seconds()
        failure_diag = self._diagnose_failure(step, last_error, context)

        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            action=step.action,
            status="failed",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            error_message=str(last_error),
            error_type=failure_diag.error_type
        )
        context.step_results.append(result)
        self.logger.log_step_result(result)

        if context.failure_details is None:
            context.failure_details = failure_diag

        if step.error_handler and step.error_handler.fallback_step_id:
            fallback_id = step.error_handler.fallback_step_id
            fallback_step = self._step_map.get(fallback_id)
            if not fallback_step:
                raise ValueError(
                    f"Fallback step '{fallback_id}' for failed step '{step.id}' not found in flow definition."
                )

            self.logger.logger.info(
                f"Step '{step.id}' failed. Executing fallback recovery step '{fallback_id}' ({fallback_step.name})."
            )
            self._execute_step(fallback_step, context)
            return

        if step.error_handler and step.error_handler.on_error == "continue":
            return

        raise last_error

    def _handle_loop_step(self, step: Step, evaluated_params: Dict[str, Any], context: ExecutionContext, start_time: datetime) -> None:
        items = evaluated_params.get("items", [])
        item_var = evaluated_params.get("item_var", "item")
        sub_steps = step.sub_steps or []

        if not isinstance(items, list):
            items = [items]

        for index, item in enumerate(items):
            if context.get_variable("__early_exit__"):
                break
            context.set_variable(item_var, item)
            context.set_variable(f"{item_var}_index", index)
            for sub_step in sub_steps:
                if context.get_variable("__early_exit__"):
                    break
                self._execute_step(sub_step, context)

        end_time = local_now()
        duration = (end_time - start_time).total_seconds()

        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            action=step.action,
            status="success",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            output={"total_items_processed": len(items)}
        )
        context.step_results.append(result)
        self.logger.log_step_result(result)

    def _handle_if_step(self, step: Step, evaluated_params: Dict[str, Any], context: ExecutionContext, start_time: datetime) -> None:
        left = evaluated_params.get("left")
        operator = evaluated_params.get("operator", "equals")
        right = evaluated_params.get("right")

        if "condition" in evaluated_params and "left" not in evaluated_params:
            condition_met = self._evaluate_condition_expr(evaluated_params["condition"])
        else:
            condition_met = self._evaluate_condition(left, operator, right)

        sub_steps = step.sub_steps or []
        else_steps = step.else_steps or []
        executed_count = 0
        branch = "none"

        if condition_met:
            for sub_step in sub_steps:
                if context.get_variable("__early_exit__"):
                    break
                self._execute_step(sub_step, context)
            executed_count = len(sub_steps)
            branch = "then"
            status = "success"
        elif else_steps:
            for else_step in else_steps:
                if context.get_variable("__early_exit__"):
                    break
                self._execute_step(else_step, context)
            executed_count = len(else_steps)
            branch = "else"
            status = "success"
        else:
            status = "skipped"

        end_time = local_now()
        duration = (end_time - start_time).total_seconds()

        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            action=step.action,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            output={
                "condition_met": condition_met,
                "branch_executed": branch,
                "left": left,
                "operator": operator,
                "right": right,
                "executed_steps": executed_count
            }
        )
        context.step_results.append(result)
        self.logger.log_step_result(result)

    def _apply_config_data(self, config_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        # 1. Align website <-> target_url synonyms
        if "website" in config_data and "target_url" not in config_data:
            config_data["target_url"] = config_data["website"]
        elif "target_url" in config_data and "website" not in config_data:
            config_data["website"] = config_data["target_url"]

        # 2. Synchronize credentials if present in config
        if "smtp_user" in config_data and config_data["smtp_user"]:
            os.environ.setdefault("GMAIL_USER", str(config_data["smtp_user"]))
            os.environ.setdefault("SMTP_USER", str(config_data["smtp_user"]))
        if "smtp_password" in config_data and config_data["smtp_password"]:
            os.environ.setdefault("GMAIL_APP_PASSWORD", str(config_data["smtp_password"]))
            os.environ.setdefault("SMTP_PASSWORD", str(config_data["smtp_password"]))

        # 3. Merge with existing config (e.g. from flow definition default variables)
        existing_config = context.get_variable("config")
        if isinstance(existing_config, dict):
            merged_config = {**existing_config, **config_data}
        else:
            merged_config = config_data

        context.set_variable("config", merged_config)
        for k, v in merged_config.items():
            context.set_variable(k, v)
        return merged_config

    def _load_bundle_configs(self, flow_dir: Path, context: ExecutionContext) -> None:
        if not flow_dir.is_dir():
            return

        # 1. Primary Check: config/config.json then config.json
        config_candidates = [
            flow_dir / "config" / "config.json",
            flow_dir / "config.json"
        ]
        config_file = next((p for p in config_candidates if p.is_file()), None)

        template_candidates = [
            flow_dir / "config" / "config.template.json",
            flow_dir / "config.template.json"
        ]
        template_file = next((p for p in template_candidates if p.is_file()), None)

        if config_file:
            try:
                config_data = json.loads(config_file.read_text(encoding="utf-8-sig"))
                if isinstance(config_data, dict):
                    applied = self._apply_config_data(config_data, context)
                    self.logger.logger.info(f"Loaded project configuration from {config_file.name} ({len(applied)} keys)")
            except Exception as e:
                self.logger.logger.warning(f"Failed to load config from {config_file}: {str(e)}")
        elif template_file:
            self.logger.logger.warning(
                f"Configuration file 'config.json' was not found in '{flow_dir.name}'. "
                f"Falling back to default '{template_file.name}'. "
                f"(Tip: Copy '{template_file.name}' to 'config.json' to customize your project settings)."
            )
            try:
                config_data = json.loads(template_file.read_text(encoding="utf-8-sig"))
                if isinstance(config_data, dict):
                    applied = self._apply_config_data(config_data, context)
            except Exception as e:
                self.logger.logger.warning(f"Failed to load template config from {template_file}: {str(e)}")
        else:
            self.logger.logger.debug(f"No configuration file ('config.json') found in '{flow_dir.name}'.")

        # 2. Auto-load local .env (if present)
        env_file = flow_dir / ".env"
        if env_file.is_file():
            try:
                self._load_env_file(env_file)
                self.logger.logger.info(f"Loaded environment secrets from {env_file.name}")
            except Exception as e:
                self.logger.logger.warning(f"Failed to load .env from {env_file}: {str(e)}")

    def _load_env_file(self, env_path: Path) -> None:
        lines = env_path.read_text(encoding="utf-8-sig").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k and k not in os.environ:
                os.environ[k] = v

    def _resolve_subflow_path(self, flow_target: str, context: ExecutionContext) -> Path:
        target_str = str(flow_target).strip()

        # 1. Namespace @shared/
        if target_str.startswith("@shared/"):
            rel_shared = target_str[8:]
            flow_dir_str = context.get_variable("__flow_dir__")
            candidates = []
            if flow_dir_str:
                p = Path(flow_dir_str).resolve()
                for parent in [p] + list(p.parents):
                    candidates.append(parent / "flows" / "@shared" / rel_shared)
                    candidates.append(parent / "@shared" / rel_shared)
            candidates.append(Path.cwd() / "flows" / "@shared" / rel_shared)
            candidates.append(Path.home() / ".kinenix" / "flows" / "@shared" / rel_shared)
            for c in candidates:
                if c.is_file():
                    return c.resolve()
                if c.with_suffix(".json").is_file():
                    return c.with_suffix(".json").resolve()

        # 2. Relative to parent flow directory
        flow_dir_str = context.get_variable("__flow_dir__")
        if flow_dir_str:
            parent_dir = Path(flow_dir_str).resolve()
            candidates = [
                (parent_dir / target_str).resolve(),
                (parent_dir / f"{target_str}.json").resolve(),
            ]
            for c in candidates:
                if c.is_file():
                    return c

        # 3. Direct path or relative to current working directory
        direct = Path(target_str).resolve()
        if direct.is_file():
            return direct
        if Path(f"{target_str}.json").is_file():
            return Path(f"{target_str}.json").resolve()

        # 4. Fallback to CLI search
        try:
            from ..cli import resolve_flow_path
            resolved = resolve_flow_path(target_str)
            if resolved and resolved.is_file():
                return resolved.resolve()
        except Exception:
            pass

        raise FileNotFoundError(f"Subflow file not found: '{flow_target}'")

    def _handle_flow_call_step(self, step: Step, evaluated_params: Dict[str, Any], context: ExecutionContext, start_time: datetime) -> None:
        flow_target = evaluated_params.get("flow")
        if not flow_target:
            raise ValueError(f"Step '{step.id}' (flow.call) requires 'flow' parameter specifying path to target flow JSON")

        resolved_path = self._resolve_subflow_path(flow_target, context)
        canonical_key = str(resolved_path)

        # 1. Enforce max_depth recursion safety
        if len(self.call_stack) >= self.max_depth:
            raise SubflowExecutionError(
                f"Subflow call depth limit of {self.max_depth} exceeded. Current stack: {' -> '.join(self.call_stack)}",
                subflow_name=flow_target,
                failed_step_id=step.id
            )

        # 2. Prevent Circular Subflow Invocation
        if canonical_key in self.call_stack:
            raise SubflowExecutionError(
                f"Circular subflow call detected: {' -> '.join(self.call_stack)} -> {canonical_key}",
                subflow_name=flow_target,
                failed_step_id=step.id
            )

        # 3. Load child FlowDefinition
        try:
            data = json.loads(resolved_path.read_text(encoding="utf-8-sig"))
            subflow_def = FlowDefinition.model_validate(data)
        except Exception as e:
            raise RuntimeError(f"Failed to load subflow definition from '{resolved_path}': {str(e)}") from e

        # 4. Variable Priority Order:
        # 4.1 Subflow defaults
        child_vars = dict(subflow_def.variables) if subflow_def.variables else {}

        # 4.2 Inputs from parent flow (overrides defaults)
        inputs = evaluated_params.get("inputs", {})
        if isinstance(inputs, dict):
            for k, v in inputs.items():
                child_vars[k] = v

        # 4.3 System variables
        child_vars["__flow_dir__"] = str(resolved_path.parent)
        child_vars["__parent_flow__"] = context.flow_name
        child_vars["__is_subflow__"] = True

        # 4.4 Safeguard & Browser Session Propagation
        if evaluated_params.get("propagate_sessions", True):
            pw = context.get_variable("__playwright_pw__")
            browser = context.get_variable("__playwright_browser__")
            page = context.get_variable("__playwright_page__")
            if pw:
                child_vars["__playwright_pw__"] = pw
            if browser:
                child_vars["__playwright_browser__"] = browser
                child_vars["__shared_browser__"] = True  # Safeguard signal
            if page:
                child_vars["__playwright_page__"] = page

        # 5. Spawn child interpreter with incremented call stack
        new_stack = list(self.call_stack) + [canonical_key]
        child_interpreter = FlowInterpreter(
            logger=self.logger,
            max_depth=self.max_depth,
            call_stack=new_stack,
            auto_close_browser=self.auto_close_browser
        )

        child_context = child_interpreter.run_flow(subflow_def, initial_vars=child_vars)

        if child_context.has_error:
            failed_id = child_context.failure_details.failed_step_id if child_context.failure_details else "unknown"
            err_msg = child_context.failure_details.error_message if child_context.failure_details else "Child subflow failed"
            raise SubflowExecutionError(
                f"Subflow '{subflow_def.name}' failed at step '{failed_id}': {err_msg}",
                subflow_name=subflow_def.name,
                failed_step_id=failed_id,
                child_context=child_context
            )

        # 6. Method 2: Contract-First Return Payload
        child_return = child_context.get_variable("__return_value__")
        if child_return is None:
            child_return = {
                k: v for k, v in child_context.variables.items()
                if not k.startswith("__")
            }

        if step.output_var:
            context.set_variable(step.output_var, child_return)

        # Optional direct outputs mapping if configured
        outputs_map = evaluated_params.get("outputs")
        if isinstance(outputs_map, dict):
            for sub_k, parent_k in outputs_map.items():
                if sub_k in child_context.variables:
                    context.set_variable(parent_k, child_context.variables[sub_k])

        end_time = local_now()
        duration = (end_time - start_time).total_seconds()

        # 7. Hierarchical Logging: subflow steps grouped inside parent step output
        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            action=step.action,
            status="success",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            output={
                "subflow_name": subflow_def.name,
                "subflow_path": str(resolved_path),
                "return_value": child_return,
                "subflow_metrics": child_context.metrics.model_dump(),
                "subflow_steps": [r.model_dump() for r in child_context.step_results]
            }
        )
        context.step_results.append(result)
        self.logger.log_step_result(result)

    def _handle_flow_return_step(self, step: Step, evaluated_params: Dict[str, Any], context: ExecutionContext, start_time: datetime) -> None:
        value = evaluated_params.get("value")
        context.set_variable("__return_value__", value)
        context.set_variable("__early_exit__", True)

        end_time = local_now()
        duration = (end_time - start_time).total_seconds()

        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            action=step.action,
            status="success",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            output={"returned": value, "early_exit": True}
        )
        context.step_results.append(result)
        self.logger.log_step_result(result)

    def _evaluate_condition(self, left: Any, operator: str, right: Any) -> bool:
        op = (operator or "equals").lower().strip()

        if op in ["is_empty", "empty"]:
            return left is None or str(left).strip() == ""
        if op in ["is_not_empty", "not_empty"]:
            return left is not None and str(left).strip() != ""

        if op in ["greater_than", ">", "gt"]:
            try:
                return float(left) > float(right)
            except (ValueError, TypeError):
                return False
        if op in ["greater_than_or_equal", ">=", "gte"]:
            try:
                return float(left) >= float(right)
            except (ValueError, TypeError):
                return False
        if op in ["less_than", "<", "lt"]:
            try:
                return float(left) < float(right)
            except (ValueError, TypeError):
                return False
        if op in ["less_than_or_equal", "<=", "lte"]:
            try:
                return float(left) <= float(right)
            except (ValueError, TypeError):
                return False

        s_left = "" if left is None else str(left).strip()
        s_right = "" if right is None else str(right).strip()

        if op in ["equals", "==", "eq"]:
            return s_left.lower() == s_right.lower()
        if op in ["not_equals", "!=", "neq"]:
            return s_left.lower() != s_right.lower()
        if op in ["contains", "in"]:
            return s_right.lower() in s_left.lower()
        if op in ["not_contains", "not_in"]:
            return s_right.lower() not in s_left.lower()
        if op in ["starts_with", "startswith"]:
            return s_left.lower().startswith(s_right.lower())
        if op in ["ends_with", "endswith"]:
            return s_left.lower().endswith(s_right.lower())

        return s_left == s_right

    def _evaluate_condition_expr(self, expr: Any) -> bool:
        if isinstance(expr, bool):
            return expr
        s = str(expr).strip()
        if s.startswith("`") and s.endswith("`") and len(s) >= 2:
            s = s[1:-1].strip()
        for token, mapped_op in [
            ("==", "equals"),
            ("!=", "not_equals"),
            (">=", "greater_than_or_equal"),
            ("<=", "less_than_or_equal"),
            (">", "greater_than"),
            ("<", "less_than"),
            (" contains ", "contains"),
            (" in ", "in"),
        ]:
            if token in s:
                parts = s.split(token, 1)
                left = parts[0].strip().strip("'\"`")
                right = parts[1].strip().strip("'\"`")
                return self._evaluate_condition(left, mapped_op, right)

        return s.lower() in ["true", "1", "yes"]
