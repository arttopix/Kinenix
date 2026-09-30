import json
import logging
import platform
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import psutil
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.models.flow import FlowDefinition

logger = logging.getLogger("kinenix_worker")


class WorkerRunner:
    """
    Execution engine for unattended worker nodes (e.g. Raspberry Pi, VMs).
    Handles bundle resolution, sandbox workspace isolation, and execution telemetry.
    """

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),  # e.g., aarch64 on Raspberry Pi
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory_total_mb": round(vm.total / (1024 * 1024), 1),
            "memory_available_mb": round(vm.available / (1024 * 1024), 1),
            "memory_used_percent": vm.percent,
        }

    def execute_flow(
        self,
        flow_path_or_alias: str,
        extra_vars: Optional[Dict[str, Any]] = None,
        use_sandbox: bool = False,
        log_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        target_path = Path(flow_path_or_alias).resolve()
        if target_path.is_dir():
            if (target_path / "flow.json").is_file():
                target_path = target_path / "flow.json"
            elif (target_path / "flow.md").is_file():
                target_path = target_path / "flow.md"

        if not target_path.is_file():
            raise FileNotFoundError(f"Flow file not found at: {flow_path_or_alias}")

        flow_dir = target_path.parent
        work_dir = flow_dir
        job_id = f"job_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        if use_sandbox:
            sandbox_dir = Path.home() / ".kinenix" / "workspaces" / job_id
            sandbox_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(flow_dir, sandbox_dir, dirs_exist_ok=True)
            work_dir = sandbox_dir
            target_path = sandbox_dir / target_path.name

        if target_path.suffix.lower() == ".md":
            from kinenix.engine.markdown import compile_markdown_to_json
            compiled_json = work_dir / "flow.json"
            compile_markdown_to_json(target_path, compiled_json)
            target_path = compiled_json

        flow_data = json.loads(target_path.read_text(encoding="utf-8"))
        flow_def = FlowDefinition(**flow_data)

        # Auto-load config.json if present in the bundle directory
        config_file = work_dir / "config" / "config.json"
        if not config_file.is_file():
            config_file = work_dir / "config.json"
        if config_file.is_file():
            try:
                cfg_data = json.loads(config_file.read_text(encoding="utf-8"))
                flow_def.variables.setdefault("config", {})
                if isinstance(flow_def.variables["config"], dict) and isinstance(cfg_data, dict):
                    flow_def.variables["config"].update(cfg_data)
            except Exception as e:
                logger.warning(f"Could not load bundle config file: {e}")

        # Inject runtime environment variables and worker system info
        system_info = self.get_system_info()
        flow_def.variables["__worker_info__"] = system_info
        flow_def.variables["__job_id__"] = job_id
        flow_def.variables["__flow_dir__"] = str(work_dir)

        if extra_vars:
            flow_def.variables.update(extra_vars)

        actual_log_dir = Path(log_dir) if log_dir else None
        exec_logger = ExecutionLogger(log_dir=actual_log_dir)

        interpreter = FlowInterpreter(logger=exec_logger)

        start_time = time.time()
        ctx = interpreter.run_flow(flow_def, initial_vars={"__flow_dir__": str(work_dir)})
        duration = round(time.time() - start_time, 2)

        result = {
            "job_id": job_id,
            "flow_name": flow_def.name,
            "status": "failed" if ctx.has_error else "success",
            "duration_seconds": duration,
            "steps_total": len(flow_def.steps),
            "steps_executed": len(ctx.step_results),
            "has_error": ctx.has_error,
            "error": ctx.error_message if ctx.has_error else None,
            "worker_system": system_info
        }

        return result
