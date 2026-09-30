import os
import shutil
from pathlib import Path
from typing import Any, Dict

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext


def _resolve_file_path(path_str: str, context: ExecutionContext) -> Path:
    """Resolves a file/directory path, supporting relative paths against __flow_dir__."""
    p = Path(path_str)
    if not p.is_absolute():
        flow_dir = context.get_variable("__flow_dir__")
        if flow_dir:
            return (Path(flow_dir) / p).resolve()
    return p.resolve()


@register_action("file.exists")
class FileExistsAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        path_str = parameters.get("path")
        if not path_str:
            raise ValueError("Parameter 'path' is required for action 'file.exists'.")

        target = _resolve_file_path(path_str, context)
        exists = target.exists()
        return exists


@register_action("file.copy")
class FileCopyAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        src_str = parameters.get("source")
        dst_str = parameters.get("destination")
        overwrite = bool(parameters.get("overwrite", True))

        if not src_str or not dst_str:
            raise ValueError("Parameters 'source' and 'destination' are required for action 'file.copy'.")

        src = _resolve_file_path(src_str, context)
        dst = _resolve_file_path(dst_str, context)

        if not src.exists():
            raise FileNotFoundError(f"Source path not found for copy: {src}")

        if dst.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists and overwrite is false: {dst}")

        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=overwrite)
        else:
            shutil.copy2(src, dst)

        return {
            "source": str(src),
            "destination": str(dst),
            "status": "copied"
        }


@register_action("file.move")
class FileMoveAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        src_str = parameters.get("source")
        dst_str = parameters.get("destination")
        overwrite = bool(parameters.get("overwrite", True))

        if not src_str or not dst_str:
            raise ValueError("Parameters 'source' and 'destination' are required for action 'file.move'.")

        src = _resolve_file_path(src_str, context)
        dst = _resolve_file_path(dst_str, context)

        if not src.exists():
            raise FileNotFoundError(f"Source path not found for move: {src}")

        if dst.exists():
            if not overwrite:
                raise FileExistsError(f"Destination already exists and overwrite is false: {dst}")
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

        return {
            "source": str(src),
            "destination": str(dst),
            "status": "moved"
        }


@register_action("file.delete")
class FileDeleteAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        path_str = parameters.get("path")
        missing_ok = bool(parameters.get("missing_ok", True))

        if not path_str:
            raise ValueError("Parameter 'path' is required for action 'file.delete'.")

        target = _resolve_file_path(path_str, context)

        if not target.exists():
            if not missing_ok:
                raise FileNotFoundError(f"Target path not found for deletion: {target}")
            return {"target": str(target), "status": "not_found", "deleted": False}

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

        return {"target": str(target), "status": "deleted", "deleted": True}
