import csv
import math
import re
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext


_INT_TEXT = re.compile(r"-?(0|[1-9][0-9]*)")
_FLOAT_TEXT = re.compile(r"-?(0|[1-9][0-9]*)?\.[0-9]+")
_BOOL_TEXT = {"true": True, "false": False}


def _flag(value: Any, default: bool) -> bool:
    """Reads a boolean parameter; the text "false" from a config file means False."""
    if value is None or value == "":
        return default
    if isinstance(value, str):
        return value.strip().lower() not in ("false", "no", "0", "off")
    return bool(value)


def _is_blank(value: Any) -> bool:
    if value is None or value is pd.NA or value is pd.NaT:
        return True
    return isinstance(value, float) and math.isnan(value)


def _typed_column(values: List[str]) -> List[Any]:
    """
    Gives a column of CSV text one type. Whole numbers become int, decimals float, true/false bool,
    and blank cells None. A column stays text when any value does not fit, so codes with a leading
    zero (phone numbers, postal codes, policy IDs) and mixed columns keep their exact text.
    """
    filled = [v.strip() for v in values if v.strip() != ""]
    if filled and all(_INT_TEXT.fullmatch(v) for v in filled):
        convert = int
    elif filled and all(_INT_TEXT.fullmatch(v) or _FLOAT_TEXT.fullmatch(v) for v in filled):
        convert = float
    elif filled and all(v.lower() in _BOOL_TEXT for v in filled):
        convert = lambda v: _BOOL_TEXT[v.lower()]
    else:
        return [v if v != "" else None for v in values]
    return [convert(v.strip()) if v.strip() != "" else None for v in values]


def _clean_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Records with None for empty cells (never NaN, whatever the pandas version), and whole-number
    float columns turned back into int, so 2023 does not become 2023.0 because another row is blank.
    """
    records = df.astype(object).to_dict(orient="records")
    whole_columns = []
    for column in df.columns:
        values = [r[column] for r in records if not _is_blank(r[column])]
        if values and all(isinstance(v, float) and v.is_integer() for v in values):
            whole_columns.append(column)
    for record in records:
        for key, value in record.items():
            if _is_blank(value):
                record[key] = None
            elif key in whole_columns:
                record[key] = int(value)
    return records


def _decode_error(path: Path, encoding: str) -> ValueError:
    return ValueError(f"Could not read {path} as {encoding}. Thai files from older systems are often 'cp874' "
                      f"(or 'tis-620'); set the encoding parameter.")


@register_action("excel.read")
class ExcelReadAction(BaseAction):
    accepted_parameters = ('file_path', 'sheet_name', 'clean_headers', 'as_text')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        file_path = parameters.get("file_path")
        sheet_name = parameters.get("sheet_name", 0)
        clean_headers = _flag(parameters.get("clean_headers"), True)
        as_text = _flag(parameters.get("as_text"), False)
        
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

        if as_text:
            df = pd.read_excel(target_path, sheet_name=sheet_name, dtype=str).fillna("")
        else:
            df = pd.read_excel(target_path, sheet_name=sheet_name)
        if clean_headers:
            df.columns = [str(c).strip() for c in df.columns]
        if as_text:
            return df.to_dict(orient="records")
        return _clean_records(df)


@register_action("excel.write")
class ExcelWriteAction(BaseAction):
    accepted_parameters = ('file_path', 'data', 'sheet_name', 'columns')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        file_path = parameters.get("file_path")
        data = parameters.get("data", [])
        sheet_name = parameters.get("sheet_name", "Sheet1")
        columns = parameters.get("columns")

        if not file_path:
            raise ValueError("Parameter 'file_path' is required for action 'excel.write'.")

        # Relative paths belong to the flow bundle, like csv.write, not to the current directory
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
            raise ValueError("Data for excel.write must be a list of dicts or a dict.")

        if columns and isinstance(columns, list):
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            df = df[columns]

        df.to_excel(target_path, sheet_name=sheet_name, index=False)
        return {"rows_written": len(df), "file_path": str(target_path)}


@register_action("csv.write")
class CsvWriteAction(BaseAction):
    accepted_parameters = ('file_path', 'data', 'columns', 'encoding', 'append')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        file_path = parameters.get("file_path")
        data = parameters.get("data", [])
        columns = parameters.get("columns")
        # utf-8-sig adds a byte order mark, so Excel opens Thai text correctly when the file is double-clicked
        encoding = str(parameters.get("encoding") or "utf-8-sig")
        append = _flag(parameters.get("append"), False)

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

        existing = append and target_path.is_file() and target_path.stat().st_size > 0
        if existing:
            # New rows follow the file's own header, so appended columns always line up
            with open(target_path, encoding="utf-8-sig", newline="") as handle:
                header = next(csv.reader(handle), [])
            unknown = [str(c) for c in df.columns if c not in header]
            if unknown:
                raise ValueError(f"csv.write cannot append columns that {target_path.name} does not have: "
                                 f"{', '.join(unknown)}. Its columns are: {', '.join(header)}.")
            for col in header:
                if col not in df.columns:
                    df[col] = ""
            df = df[header]
            # The byte order mark belongs only at the start of a file
            if encoding.lower().replace("_", "-") == "utf-8-sig":
                encoding = "utf-8"

        try:
            df.to_csv(target_path, index=False, encoding=encoding, mode="a" if existing else "w", header=not existing)
        except LookupError as exc:
            raise ValueError(f"Unknown encoding '{encoding}' for csv.write.") from exc
        return {"rows_written": len(df), "file_path": str(target_path), "mode": "append" if existing else "write"}


@register_action("csv.read")
class CsvReadAction(BaseAction):
    accepted_parameters = ('file_path', 'delimiter', 'encoding', 'clean_headers', 'as_text')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        file_path = parameters.get("file_path")
        delimiter = parameters.get("delimiter", ",")
        # utf-8-sig also reads files saved by Excel with a byte order mark, which would otherwise stick to the first header
        encoding = str(parameters.get("encoding") or "utf-8-sig")
        clean_headers = _flag(parameters.get("clean_headers"), True)
        as_text = _flag(parameters.get("as_text"), False)

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

        # Every cell is read as text first, so pandas never turns blanks into NaN, "NA" into a missing value,
        # or "0812345678" into a number; each column then gets one type
        try:
            df = pd.read_csv(target_path, sep=delimiter, encoding=encoding, dtype=str, keep_default_na=False)
        except UnicodeDecodeError as exc:
            raise _decode_error(target_path, encoding) from exc
        except LookupError as exc:
            raise ValueError(f"Unknown encoding '{encoding}' for csv.read.") from exc

        if clean_headers:
            df.columns = [str(c).strip() for c in df.columns]
        records = df.to_dict(orient="records")
        if as_text:
            return records
        typed = {column: _typed_column([r[column] for r in records]) for column in df.columns}
        return [{column: typed[column][i] for column in df.columns} for i in range(len(records))]

