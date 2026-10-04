import json
from pathlib import Path
import pytest
from kinenix.models.flow import FlowDefinition, Step
from kinenix.models.context import ExecutionContext
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.evaluator import VariableEvaluator


def test_variable_evaluator():
    vars_ctx = {"name": "BAT", "details": {"version": "1.0"}}
    val = VariableEvaluator.evaluate_value("Hello ${name} v${details.version}", vars_ctx)
    assert val == "Hello BAT v1.0"


def test_interpreter_basic_run():
    flow = FlowDefinition(
        name="Test Flow",
        variables={"msg": "hello"},
        steps=[
            Step(
                id="s1",
                name="Set Variable",
                action="logic.set_variable",
                parameters={"name": "res", "value": "${msg}_world"},
                output_var="res"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)

    assert ctx.is_completed is True
    assert ctx.has_error is False
    assert ctx.get_variable("res") == "hello_world"
    assert len(ctx.step_results) == 1
    assert ctx.step_results[0].status == "success"


def test_interpreter_load_sample_flow_json():
    json_path = Path(__file__).parent.parent / "examples" / "sample_flow.json"
    assert json_path.exists()

    content = json_path.read_text(encoding="utf-8")
    raw_json = json.loads(content)
    flow_def = FlowDefinition.model_validate(raw_json)

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow_def)

    assert ctx.is_completed is True
    assert ctx.has_error is False
    assert len(ctx.step_results) == 3


def test_logger_safe_serialization_with_custom_objects(tmp_path):
    from kinenix.models.context import ExecutionContext
    from kinenix.engine.logger import ExecutionLogger

    class NonSerializableClass:
        def __repr__(self):
            return "<CustomObject>"

    ctx = ExecutionContext(flow_name="Test Safe Serialization")
    ctx.set_variable("__internal_obj__", NonSerializableClass())
    ctx.set_variable("normal_var", 123)
    ctx.set_variable("custom_obj", NonSerializableClass())

    logger = ExecutionLogger(log_dir=str(tmp_path))
    # Should not raise PydanticSerializationError
    logger.log_execution_summary(ctx)

    log_files = list(tmp_path.glob("*/*/*.json"))
    assert len(log_files) == 1
    content = json.loads(log_files[0].read_text(encoding="utf-8"))
    assert "__internal_obj__" not in content["variables"]
    assert content["variables"]["normal_var"] == 123
    assert content["variables"]["custom_obj"] == "<CustomObject>"


def test_resolve_log_dir(tmp_path):
    from kinenix.engine.logger import resolve_log_dir

    # 1. Custom log dir explicitly specified
    custom = resolve_log_dir(str(tmp_path / "my_logs"))
    assert custom == (tmp_path / "my_logs").resolve()

    # 2. Inside project structure (containing .git or kinenix-core)
    # The current repo has root at Kinenix
    resolved = resolve_log_dir()
    assert (resolved.parent / "kinenix-core").exists() or (resolved.parent / ".git").exists()
    assert resolved.name == "logs"


def test_logic_if_action():
    # 1. True condition
    flow_true = FlowDefinition(
        name="Test If True",
        variables={"role": "Programmer", "result": "initial"},
        steps=[
            Step(
                id="step_check",
                name="Check Role",
                action="logic.if",
                parameters={
                    "left": "${role}",
                    "operator": "equals",
                    "right": "Programmer"
                },
                sub_steps=[
                    Step(
                        id="sub_set",
                        name="Set Success",
                        action="logic.set_variable",
                        parameters={"name": "result", "value": "is_programmer"},
                        output_var="result"
                    )
                ]
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx_true = interpreter.run_flow(flow_true)
    assert ctx_true.get_variable("result") == "is_programmer"
    assert ctx_true.step_results[0].status == "success"

    # 2. False condition
    flow_false = FlowDefinition(
        name="Test If False",
        variables={"role": "Manager", "result": "initial"},
        steps=[
            Step(
                id="step_check",
                name="Check Role",
                action="logic.if",
                parameters={
                    "left": "${role}",
                    "operator": "equals",
                    "right": "Programmer"
                },
                sub_steps=[
                    Step(
                        id="sub_set",
                        name="Set Success",
                        action="logic.set_variable",
                        parameters={"name": "result", "value": "is_programmer"},
                        output_var="result"
                    )
                ]
            )
        ]
    )

    ctx_false = interpreter.run_flow(flow_false)
    assert ctx_false.get_variable("result") == "initial"
    assert ctx_false.step_results[0].status == "skipped"


def test_step_condition():
    flow = FlowDefinition(
        name="Test Step Condition",
        variables={"role": "Manager", "result": "initial"},
        steps=[
            Step(
                id="step_skip",
                name="Skip If Not Programmer",
                action="logic.set_variable",
                condition="${role} == Programmer",
                parameters={"name": "result", "value": "modified"},
                output_var="result"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)
    assert ctx.get_variable("result") == "initial"
    assert ctx.step_results[0].status == "skipped"


def test_logic_if_else_and_append():
    flow = FlowDefinition(
        name="Test If Else and Append",
        variables={"role": "Analyst", "name": "John", "skipped": []},
        steps=[
            Step(
                id="step_check",
                name="Check Role",
                action="logic.if",
                parameters={
                    "left": "${role}",
                    "operator": "equals",
                    "right": "Programmer"
                },
                sub_steps=[
                    Step(
                        id="sub_pos",
                        name="Set Processed",
                        action="logic.set_variable",
                        parameters={"name": "status", "value": "processed"}
                    )
                ],
                else_steps=[
                    Step(
                        id="sub_else_append",
                        name="Record Non-Programmer",
                        action="logic.append",
                        parameters={
                            "target": "skipped",
                            "item": {
                                "First Name": "${name}",
                                "Role": "${role}"
                            }
                        }
                    )
                ]
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)

    assert ctx.is_completed is True
    assert ctx.has_error is False
    assert ctx.get_variable("status") is None
    skipped = ctx.get_variable("skipped")
    assert isinstance(skipped, list)
    assert len(skipped) == 1
    assert skipped[0] == {"First Name": "John", "Role": "Analyst"}
    check_result = next(r for r in ctx.step_results if r.step_id == "step_check")
    assert check_result.status == "success"
    assert check_result.output["branch_executed"] == "else"


def test_flow_failure_diagnosis():
    flow = FlowDefinition(
        name="Test Failing Flow",
        steps=[
            Step(
                id="step_fail_file",
                name="Read Missing File",
                action="excel.read",
                parameters={"file_path": "non_existent_file.xlsx"}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)

    assert ctx.is_completed is False
    assert ctx.has_error is True
    assert ctx.failure_details is not None
    assert ctx.failure_details.failed_step_id == "step_fail_file"
    assert ctx.failure_details.failed_step_name == "Read Missing File"
    assert ctx.failure_details.action == "excel.read"
    assert ctx.failure_details.exception_class == "FileNotFoundError"
    assert "not found" in ctx.failure_details.root_cause.lower()
    assert len(ctx.failure_details.suggested_fix) > 0


def test_subflow_contract_first_return(tmp_path):
    subflow_path = tmp_path / "calc_subflow.json"
    subflow_def = {
        "name": "Calculation Subflow",
        "variables": {
            "factor": 10,
            "offset": 5
        },
        "steps": [
            {
                "id": "sub_step_1",
                "name": "Compute Total",
                "action": "logic.set_variable",
                "parameters": {"name": "calculated_value", "value": "100"},
                "output_var": "calculated_value"
            },
            {
                "id": "sub_step_return",
                "name": "Return Calculation",
                "action": "flow.return",
                "parameters": {
                    "value": {
                        "total": "${calculated_value}",
                        "used_factor": "${factor}",
                        "used_offset": "${offset}"
                    }
                }
            },
            {
                "id": "sub_step_unreachable",
                "name": "Should Never Execute Due to Early Exit",
                "action": "logic.set_variable",
                "parameters": {"name": "should_not_exist", "value": "leaked"}
            }
        ]
    }
    subflow_path.write_text(json.dumps(subflow_def), encoding="utf-8")

    parent_flow = FlowDefinition(
        name="Parent Main Flow",
        variables={"base_num": 50},
        steps=[
            Step(
                id="step_invoke_subflow",
                name="Call Calculation Subflow",
                action="flow.call",
                parameters={
                    "flow": str(subflow_path),
                    "inputs": {
                        "factor": 25
                    }
                },
                output_var="calc_output"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(parent_flow)

    assert ctx.is_completed is True
    assert ctx.has_error is False

    calc_output = ctx.get_variable("calc_output")
    assert isinstance(calc_output, dict)
    assert calc_output["total"] == "100"
    assert calc_output["used_factor"] == 25  # Overridden by inputs
    assert calc_output["used_offset"] == 5   # Preserved from subflow default variables

    # Variable scope isolation: child temporary variables must not pollute parent context
    assert ctx.get_variable("calculated_value") is None
    assert ctx.get_variable("should_not_exist") is None

    # Hierarchical logging: parent step contains child steps and metrics
    parent_step_res = ctx.step_results[0]
    assert parent_step_res.status == "success"
    assert "subflow_steps" in parent_step_res.output
    assert len(parent_step_res.output["subflow_steps"]) == 2  # Step 1 and Return step (Step 3 skipped)


def test_subflow_default_variables_priority(tmp_path):
    subflow_path = tmp_path / "priority_subflow.json"
    subflow_def = {
        "name": "Priority Subflow",
        "variables": {
            "timeout": 30,
            "market": "SET",
            "send_line": True
        },
        "steps": [
            {
                "id": "ret_step",
                "name": "Return Config",
                "action": "flow.return",
                "parameters": {
                    "value": {
                        "timeout": "${timeout}",
                        "market": "${market}",
                        "send_line": "${send_line}"
                    }
                }
            }
        ]
    }
    subflow_path.write_text(json.dumps(subflow_def), encoding="utf-8")

    parent_flow = FlowDefinition(
        name="Parent Priority Flow",
        steps=[
            Step(
                id="call_p",
                name="Call Priority",
                action="flow.call",
                parameters={
                    "flow": str(subflow_path),
                    "inputs": {
                        "timeout": 60,
                        "market": "NASDAQ"
                    }
                },
                output_var="res"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(parent_flow)

    res = ctx.get_variable("res")
    assert res["timeout"] == 60       # Inputs win
    assert res["market"] == "NASDAQ"  # Inputs win
    assert res["send_line"] is True   # Default variables preserved


def test_subflow_max_depth_exceeded(tmp_path):
    subflow_path = tmp_path / "depth_subflow.json"
    subflow_def = {
        "name": "Recursive Subflow",
        "steps": [
            {
                "id": "call_self",
                "name": "Call Next",
                "action": "flow.call",
                "parameters": {"flow": str(subflow_path)}
            }
        ]
    }
    subflow_path.write_text(json.dumps(subflow_def), encoding="utf-8")

    parent_flow = FlowDefinition(
        name="Parent Flow",
        steps=[
            Step(
                id="start_call",
                name="Start Call",
                action="flow.call",
                parameters={"flow": str(subflow_path)}
            )
        ]
    )

    interpreter = FlowInterpreter(max_depth=3)
    ctx = interpreter.run_flow(parent_flow)

    assert ctx.has_error is True
    assert "circular" in ctx.failure_details.error_message.lower() or "depth" in ctx.failure_details.error_message.lower()


def test_subflow_circular_call_detection(tmp_path):
    flow_a_path = tmp_path / "flow_a.json"
    flow_b_path = tmp_path / "flow_b.json"

    flow_a_def = {
        "name": "Flow A",
        "steps": [
            {
                "id": "step_a_call_b",
                "name": "Call B",
                "action": "flow.call",
                "parameters": {"flow": str(flow_b_path)}
            }
        ]
    }

    flow_b_def = {
        "name": "Flow B",
        "steps": [
            {
                "id": "step_b_call_a",
                "name": "Call A",
                "action": "flow.call",
                "parameters": {"flow": str(flow_a_path)}
            }
        ]
    }

    flow_a_path.write_text(json.dumps(flow_a_def), encoding="utf-8")
    flow_b_path.write_text(json.dumps(flow_b_def), encoding="utf-8")

    parent_flow = FlowDefinition.model_validate(flow_a_def)
    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(parent_flow)

    assert ctx.has_error is True
    assert "circular" in ctx.failure_details.error_message.lower()


def test_subflow_shared_browser_safeguard():
    from kinenix.actions.web_playwright import WebCloseAction

    ctx = ExecutionContext(flow_name="Subflow Context")
    ctx.set_variable("__shared_browser__", True)

    close_action = WebCloseAction()
    result = close_action.execute({}, ctx)

    assert result["status"] == "skipped"
    assert result["reason"] == "protected_shared_browser"


def test_subflow_shared_component_send_email():
    parent_flow = FlowDefinition(
        name="Test Shared Email Caller",
        steps=[
            Step(
                id="step_call_email",
                name="Call Shared Email Component",
                action="flow.call",
                parameters={
                    "flow": "@shared/send_email.json",
                    "inputs": {
                        "to": "finance@example.com",
                        "subject": "Monthly Close Completed",
                        "body": "All 120 invoices processed.",
                        "dry_run": True
                    }
                },
                output_var="email_result"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(parent_flow)

    assert ctx.is_completed is True
    assert ctx.has_error is False

    res = ctx.get_variable("email_result")
    assert isinstance(res, dict)
    assert res["status"] == "simulated"
    assert res["channel"].startswith("SMTP ")  # host depends on SMTP_HOST in the environment
    assert res["to"] == "finance@example.com"
    assert res["subject"] == "Monthly Close Completed"


def test_email_send_action_dry_run_with_attachment(tmp_path):
    from kinenix.actions.email_smtp import EmailSendAction

    dummy_file = tmp_path / "report.csv"
    dummy_file.write_text("id,name,amount\n1,Alpha,500\n", encoding="utf-8")

    action = EmailSendAction()
    ctx = ExecutionContext(flow_name="Email Test Context")

    result = action.execute(
        {
            "to": "test@example.com, manager@example.com",
            "subject": "Automated Report",
            "body": "Please find attached report.",
            "attachments": [str(dummy_file)],
            "dry_run": True
        },
        ctx
    )

    assert result["status"] == "simulated"
    assert len(result["to"]) == 2
    assert "test@example.com" in result["to"]
    assert result["attachments_count"] == 1


def test_auto_load_flow_config_json(tmp_path):
    bundle_dir = tmp_path / "invoice_bundle"
    bundle_dir.mkdir()

    # Create config.json
    config_data = {
        "email_to": "accounting@company.com",
        "portal_url": "https://erp.internal/tax",
        "max_retries": 3,
        "dry_run": True
    }
    (bundle_dir / "config.json").write_text(json.dumps(config_data), encoding="utf-8")

    # Create flow.json that references ${config.portal_url} and ${email_to}
    flow_def = FlowDefinition(
        name="Invoice Filing Bundle",
        steps=[
            Step(
                id="step_test_cfg",
                name="Inspect Config",
                action="logic.set_variable",
                parameters={
                    "name": "captured_portal",
                    "value": "${config.portal_url}"
                },
                output_var="captured_portal"
            ),
            Step(
                id="step_test_top_level",
                name="Inspect Direct Key",
                action="logic.set_variable",
                parameters={
                    "name": "captured_email",
                    "value": "${email_to}"
                },
                output_var="captured_email"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow_def, initial_vars={"__flow_dir__": str(bundle_dir)})

    assert ctx.is_completed is True
    assert ctx.has_error is False

    # Check config namespace
    cfg = ctx.get_variable("config")
    assert isinstance(cfg, dict)
    assert cfg["email_to"] == "accounting@company.com"
    assert cfg["max_retries"] == 3

    # Check variables populated from config
    assert ctx.get_variable("captured_portal") == "https://erp.internal/tax"
    assert ctx.get_variable("captured_email") == "accounting@company.com"


def test_auto_load_flow_local_env(tmp_path):
    bundle_dir = tmp_path / "secure_bundle"
    bundle_dir.mkdir()

    # Create local .env
    (bundle_dir / ".env").write_text(
        "# Bundle Secrets\n"
        "BUNDLE_API_TOKEN=super_secret_token_abc123\n"
        "BUNDLE_ENV_NAME='production'\n",
        encoding="utf-8"
    )

    flow_def = FlowDefinition(
        name="Secure Bundle",
        steps=[
            Step(
                id="step_read_token",
                name="Read Environment Token",
                action="logic.set_variable",
                parameters={
                    "name": "token_val",
                    "value": "${env.BUNDLE_API_TOKEN}"
                },
                output_var="token_val"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow_def, initial_vars={"__flow_dir__": str(bundle_dir)})

    assert ctx.is_completed is True
    assert ctx.get_variable("token_val") == "super_secret_token_abc123"


def test_auto_load_flow_config_template_fallback(tmp_path):
    bundle_dir = tmp_path / "fallback_bundle"
    bundle_dir.mkdir()

    # Only config.template.json exists (config.json does not exist yet)
    template_data = {
        "api_endpoint": "https://api.template.example.com",
        "timeout": 45
    }
    (bundle_dir / "config.template.json").write_text(json.dumps(template_data), encoding="utf-8")

    flow_def = FlowDefinition(
        name="Fallback Template Bundle",
        steps=[
            Step(
                id="s1",
                name="Read Endpoint",
                action="logic.set_variable",
                parameters={"name": "ep", "value": "${config.api_endpoint}"},
                output_var="ep"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow_def, initial_vars={"__flow_dir__": str(bundle_dir)})

    assert ctx.is_completed is True
    assert ctx.get_variable("ep") == "https://api.template.example.com"


def test_auto_load_flow_config_from_config_subfolder(tmp_path):
    bundle_dir = tmp_path / "subfolder_config_bundle"
    bundle_dir.mkdir()
    config_dir = bundle_dir / "config"
    config_dir.mkdir()

    config_data = {
        "website": "https://rpachallenge.com/",
        "excel_path": "./assets/challenge.xlsx",
        "screenshot_path": "./output/screenshots/res.png",
        "error_dir": "./output/errors/"
    }
    (config_dir / "config.json").write_text(json.dumps(config_data), encoding="utf-8")

    flow_def = FlowDefinition(
        name="Subfolder Config Flow",
        steps=[
            Step(
                id="s1",
                name="Inspect Website",
                action="logic.set_variable",
                parameters={"name": "site", "value": "${config.website}"},
                output_var="site"
            ),
            Step(
                id="s2",
                name="Inspect Error Dir",
                action="logic.set_variable",
                parameters={"name": "err_dir", "value": "${config.error_dir}"},
                output_var="err_dir"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow_def, initial_vars={"__flow_dir__": str(bundle_dir)})

    assert ctx.is_completed is True
    assert ctx.has_error is False
    assert ctx.get_variable("site") == "https://rpachallenge.com/"
    assert ctx.get_variable("err_dir") == "./output/errors/"


def test_auto_capture_error_screenshot_on_failure(tmp_path):
    bundle_dir = tmp_path / "error_capture_bundle"
    bundle_dir.mkdir()

    # Mock Playwright Page
    class MockPlaywrightPage:
        def __init__(self):
            self.captured_path = None
            self.is_closed_flag = False

        def is_closed(self):
            return self.is_closed_flag

        def screenshot(self, path, full_page=True):
            self.captured_path = path
            Path(path).write_text("fake_screenshot_bytes", encoding="utf-8")

    mock_page = MockPlaywrightPage()

    flow_def = FlowDefinition(
        name="Failure Flow",
        steps=[
            Step(
                id="failing_step",
                name="Step That Fails",
                action="excel.read",
                parameters={"file_path": str(bundle_dir / "missing.xlsx")}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(
        flow_def,
        initial_vars={
            "__flow_dir__": str(bundle_dir),
            "__playwright_page__": mock_page
        }
    )

    assert ctx.has_error is True
    assert ctx.failure_details is not None
    assert ctx.failure_details.error_screenshot_path is not None
    assert Path(ctx.failure_details.error_screenshot_path).is_file()
    assert ctx.get_variable("__last_error_screenshot__") == ctx.failure_details.error_screenshot_path
    assert "failing_step" in ctx.failure_details.error_screenshot_path


def test_auto_capture_error_screenshot_no_browser_graceful(tmp_path):
    bundle_dir = tmp_path / "no_browser_bundle"
    bundle_dir.mkdir()

    flow_def = FlowDefinition(
        name="Failure Without Browser",
        steps=[
            Step(
                id="fail_no_web",
                name="Step That Fails Without Web",
                action="excel.read",
                parameters={"file_path": str(bundle_dir / "missing.xlsx")}
            )
        ]
    )

    interpreter = FlowInterpreter()
    # No __playwright_page__ provided
    ctx = interpreter.run_flow(flow_def, initial_vars={"__flow_dir__": str(bundle_dir)})

    assert ctx.has_error is True
    assert ctx.failure_details is not None
    assert ctx.failure_details.error_screenshot_path is None





