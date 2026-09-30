from pathlib import Path
from typing import Any, Dict
import pandas as pd

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext


@register_action("excel.read")
class ExcelReadAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        file_path = parameters.get("file_path")
        sheet_name = parameters.get("sheet_name", 0)
        clean_headers = parameters.get("clean_headers", True)
        
        raw_path = Path(file_path) if file_path else None
        target_path = None
        if raw_path and raw_path.is_file():
            target_path = raw_path
        else:
            flow_dir_str = context.get_variable("__flow_dir__")
            if flow_dir_str and file_path:
                flow_dir = Path(flow_dir_str)
                candidates = [
                    flow_dir / file_path,
                    flow_dir.parent / file_path,
                    flow_dir / raw_path.name,
                ]
                for c in candidates:
                    if c.is_file():
                        target_path = c
                        break

        if not target_path or not target_path.is_file():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        df = pd.read_excel(target_path, sheet_name=sheet_name)
        if clean_headers:
            df.columns = [str(c).strip() for c in df.columns]
        records = df.to_dict(orient="records")
        return records


@register_action("excel.write")
class ExcelWriteAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        file_path = parameters.get("file_path")
        data = parameters.get("data", [])
        sheet_name = parameters.get("sheet_name", "Sheet1")

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError("Data for excel.write must be a list of dicts or a dict.")

        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        return {"rows_written": len(df), "file_path": file_path}


@register_action("csv.write")
class CsvWriteAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        file_path = parameters.get("file_path")
        data = parameters.get("data", [])
        columns = parameters.get("columns")

        if not file_path:
            raise ValueError("Parameter 'file_path' is required for action 'csv.write'.")

        target_path = Path(file_path)
        if not target_path.is_absolute():
            flow_dir_str = context.get_variable("__flow_dir__")
            if flow_dir_str:
                target_path = Path(flow_dir_str) / file_path

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError("Data for csv.write must be a list of dicts or a dict.")

        if columns and isinstance(columns, list):
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            df = df[columns]

        df.to_csv(target_path, index=False)
        return {"rows_written": len(df), "file_path": str(target_path)}


@register_action("csv.read")
class CsvReadAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        file_path = parameters.get("file_path")
        delimiter = parameters.get("delimiter", ",")
        encoding = parameters.get("encoding", "utf-8")
        clean_headers = parameters.get("clean_headers", True)

        if not file_path:
            raise ValueError("Parameter 'file_path' is required for action 'csv.read'.")

        raw_path = Path(file_path)
        target_path = None
        if raw_path.is_file():
            target_path = raw_path
        else:
            flow_dir_str = context.get_variable("__flow_dir__")
            if flow_dir_str:
                flow_dir = Path(flow_dir_str)
                candidates = [
                    flow_dir / file_path,
                    flow_dir.parent / file_path,
                    flow_dir / raw_path.name,
                ]
                for c in candidates:
                    if c.is_file():
                        target_path = c
                        break

        if not target_path or not target_path.is_file():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            df = pd.read_csv(target_path, sep=delimiter, encoding=encoding)
        except UnicodeDecodeError:
            # Fallback to utf-8-sig or latin1 if utf-8 fails
            try:
                df = pd.read_csv(target_path, sep=delimiter, encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(target_path, sep=delimiter, encoding="latin1")

        if clean_headers:
            df.columns = [str(c).strip() for c in df.columns]
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")

