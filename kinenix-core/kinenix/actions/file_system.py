import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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


def _flag(value: Any, default: bool) -> bool:
    """Reads a boolean parameter; the text "false" from a config file means False."""
    if value is None or value == "":
        return default
    if isinstance(value, str):
        return value.strip().lower() not in ("false", "no", "0", "off")
    return bool(value)


@register_action("file.exists")
class FileExistsAction(BaseAction):
    accepted_parameters = ('path',)

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        path_str = parameters.get("path")
        if not path_str:
            raise ValueError("Parameter 'path' is required for action 'file.exists'.")

        target = _resolve_file_path(path_str, context)
        exists = target.exists()
        return exists


@register_action("file.copy")
class FileCopyAction(BaseAction):
    accepted_parameters = ('source', 'destination', 'overwrite')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        src_str = parameters.get("source")
        dst_str = parameters.get("destination")
        overwrite = _flag(parameters.get("overwrite"), True)

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
    accepted_parameters = ('source', 'destination', 'overwrite')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        src_str = parameters.get("source")
        dst_str = parameters.get("destination")
        overwrite = _flag(parameters.get("overwrite"), True)

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
    accepted_parameters = ('path', 'missing_ok')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        path_str = parameters.get("path")
        missing_ok = _flag(parameters.get("missing_ok"), True)

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


@register_action("file.zip")
class FileZipAction(BaseAction):
    """Packs files and folders into one zip file, for example to attach a run's output to an email."""
    accepted_parameters = ('source', 'destination', 'overwrite')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        sources = parameters.get("source")
        dst_str = parameters.get("destination")
        if not sources or not dst_str:
            raise ValueError("Parameters 'source' and 'destination' are required for action 'file.zip'.")
        if not isinstance(sources, list):
            sources = [sources]

        dst = _resolve_file_path(str(dst_str), context)
        if dst.exists() and not _flag(parameters.get("overwrite"), True):
            raise FileExistsError(f"Zip file already exists and overwrite is false: {dst}")

        entries: List[tuple] = []
        for source in sources:
            src = _resolve_file_path(str(source), context)
            if not src.exists():
                raise FileNotFoundError(f"Source path not found for zip: {src}")
            if src.is_dir():
                # The folder name is kept as the top level inside the zip, so several folders do not mix
                for item in sorted(src.rglob("*")):
                    if item.is_file() and item.resolve() != dst:
                        entries.append((item, Path(src.name) / item.relative_to(src)))
            elif src != dst:
                entries.append((src, Path(src.name)))

        names = [arcname.as_posix() for _, arcname in entries]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"file.zip would store more than one file as {', '.join(duplicates)}; "
                             f"zip their folders instead, or rename them.")

        dst.parent.mkdir(parents=True, exist_ok=True)
        # Written next to the target first, so a failed run never leaves a half-written zip behind
        partial = dst.with_name(dst.name + ".partial")
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, arcname in entries:
                archive.write(path, arcname.as_posix())
        partial.replace(dst)

        return {
            "zip_path": str(dst),
            "files_added": len(entries),
            "size_bytes": dst.stat().st_size,
            "status": "zipped",
        }


@register_action("file.unzip")
class FileUnzipAction(BaseAction):
    """Extracts a zip file into a folder."""
    accepted_parameters = ('source', 'destination', 'overwrite')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        src_str = parameters.get("source")
        if not src_str:
            raise ValueError("Parameter 'source' is required for action 'file.unzip'.")

        src = _resolve_file_path(str(src_str), context)
        if not src.is_file():
            raise FileNotFoundError(f"Zip file not found for unzip: {src}")
        dst_str = parameters.get("destination")
        dst = _resolve_file_path(str(dst_str), context) if dst_str else src.with_suffix("")
        overwrite = _flag(parameters.get("overwrite"), True)

        if not zipfile.is_zipfile(src):
            raise ValueError(f"Not a zip file: {src}")

        with zipfile.ZipFile(src) as archive:
            members = [m for m in archive.infolist() if not m.is_dir()]
            for member in members:
                target = (dst / member.filename).resolve()
                # A zip entry such as "../../etc/passwd" must not write outside the destination folder
                if target != dst and dst not in target.parents:
                    raise ValueError(f"Zip entry '{member.filename}' points outside the destination folder; "
                                     f"the file was not extracted.")
                if target.exists() and not overwrite:
                    raise FileExistsError(f"File already exists and overwrite is false: {target}")
            dst.mkdir(parents=True, exist_ok=True)
            archive.extractall(dst)

        return {
            "destination": str(dst),
            "files": [m.filename for m in members],
            "files_extracted": len(members),
            "status": "unzipped",
        }


@register_action("file.create_folder")
class FileCreateFolderAction(BaseAction):
    accepted_parameters = ('path',)

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        path_str = parameters.get("path")
        if not path_str:
            raise ValueError("Parameter 'path' is required for action 'file.create_folder'.")
        target = _resolve_file_path(str(path_str), context)
        if target.exists() and not target.is_dir():
            raise FileExistsError(f"A file with this name already exists, so the folder cannot be created: {target}")
        created = not target.exists()
        target.mkdir(parents=True, exist_ok=True)
        return {"path": str(target), "created": created, "status": "created" if created else "exists"}


LIST_TYPES = ("files", "folders", "all")
LIST_SORTS = ("name", "modified", "size")


@register_action("file.list")
class FileListAction(BaseAction):
    """
    Lists the files or folders in a folder, so a flow can loop over them (for example every CSV in an inbox)
    or pick the newest one. Each item carries its name, path, size, and modification time.
    """
    accepted_parameters = ('path', 'pattern', 'recursive', 'type', 'sort_by', 'descending', 'limit')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        path_str = parameters.get("path")
        if not path_str:
            raise ValueError("Parameter 'path' is required for action 'file.list'.")
        folder = _resolve_file_path(str(path_str), context)
        if not folder.is_dir():
            raise FileNotFoundError(f"Folder not found for file.list: {folder}")

        pattern = str(parameters.get("pattern") or "*")
        kind = str(parameters.get("type") or "files").strip().lower()
        sort_by = str(parameters.get("sort_by") or "name").strip().lower()
        if kind not in LIST_TYPES:
            raise ValueError(f"file.list type must be one of {', '.join(LIST_TYPES)}; got '{kind}'.")
        if sort_by not in LIST_SORTS:
            raise ValueError(f"file.list sort_by must be one of {', '.join(LIST_SORTS)}; got '{sort_by}'.")

        found = folder.rglob(pattern) if _flag(parameters.get("recursive"), False) else folder.glob(pattern)
        items = []
        for item in found:
            is_dir = item.is_dir()
            if (kind == "files" and is_dir) or (kind == "folders" and not is_dir):
                continue
            stat = item.stat()
            items.append({
                "name": item.name,
                "stem": item.stem,
                "extension": "" if is_dir else item.suffix.lower(),
                "path": str(item),
                "relative_path": item.relative_to(folder).as_posix(),
                "is_folder": is_dir,
                "size": 0 if is_dir else stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0).isoformat(),
                "_mtime": stat.st_mtime,
            })

        keys = {"name": lambda i: i["relative_path"].lower(), "modified": lambda i: i["_mtime"], "size": lambda i: i["size"]}
        items.sort(key=keys[sort_by], reverse=_flag(parameters.get("descending"), False))
        for item in items:
            del item["_mtime"]

        limit = parameters.get("limit")
        if limit not in (None, ""):
            try:
                items = items[:max(int(limit), 0)]
            except (TypeError, ValueError) as exc:
                raise ValueError(f"file.list limit must be a whole number; got '{limit}'.") from exc
        return items


TEXT_FORMATS = ("text", "lines", "json")


@register_action("file.read_text")
class FileReadTextAction(BaseAction):
    """Reads a text file as one string, as a list of lines, or as parsed JSON."""
    accepted_parameters = ('path', 'encoding', 'format')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        path_str = parameters.get("path")
        if not path_str:
            raise ValueError("Parameter 'path' is required for action 'file.read_text'.")
        source = _resolve_file_path(str(path_str), context)
        if not source.is_file():
            raise FileNotFoundError(f"File not found for file.read_text: {source}")

        fmt = str(parameters.get("format") or "text").strip().lower()
        if fmt not in TEXT_FORMATS:
            raise ValueError(f"file.read_text format must be one of {', '.join(TEXT_FORMATS)}; got '{fmt}'.")
        # utf-8-sig also reads files saved by Excel or Notepad with a byte order mark
        encoding = str(parameters.get("encoding") or "utf-8-sig")
        try:
            text = source.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            raise ValueError(f"Could not read {source} as {encoding}. Thai files from older systems are often "
                             f"'cp874' or 'tis-620'; set the encoding parameter.") from exc
        except LookupError as exc:
            raise ValueError(f"Unknown encoding '{encoding}' for file.read_text.") from exc

        if fmt == "lines":
            return text.splitlines()
        if fmt == "json":
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source} is not valid JSON: {exc}") from exc
        return text


@register_action("file.write_text")
class FileWriteTextAction(BaseAction):
    """
    Writes text to a file, replacing it or adding to its end. A list or object is written as formatted JSON.
    With append, the text is added as a line: a line break follows it if it does not end with one.
    """
    accepted_parameters = ('path', 'content', 'append', 'encoding')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        path_str = parameters.get("path")
        if not path_str:
            raise ValueError("Parameter 'path' is required for action 'file.write_text'.")
        if "content" not in parameters:
            raise ValueError("Parameter 'content' is required for action 'file.write_text'.")
        target = _resolve_file_path(str(path_str), context)

        content = parameters.get("content")
        if isinstance(content, (dict, list)):
            text = json.dumps(content, ensure_ascii=False, indent=2) + "\n"
        else:
            text = "" if content is None else str(content)

        append = _flag(parameters.get("append"), False)
        if append and not text.endswith("\n"):
            text += "\n"
        encoding = str(parameters.get("encoding") or "utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(target, "a" if append else "w", encoding=encoding, newline="") as handle:
                handle.write(text)
        except LookupError as exc:
            raise ValueError(f"Unknown encoding '{encoding}' for file.write_text.") from exc

        return {"path": str(target), "characters_written": len(text), "mode": "append" if append else "write",
                "status": "written"}
