"""`kinenix hub query`: read-only questions to the Hub database from the terminal (docs/hub.md, Querying).

Without --url it reads hub.db on this machine (the Hub does not need to run); with --url it asks a Hub
over HTTP with the dashboard credentials. Both use query.py, so they give the same answers.
"""
import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from . import query as hub_query
from .console import ask_secret

CELL_WIDTH = 60
# Below this width per column, rows are printed as blocks of column: value lines instead of a table
MIN_COLUMN_WIDTH = 12
FORMATS = ("table", "json", "csv", "md")


class _Local:
    """Answers from hub.db on this machine."""

    def __init__(self, path: Path, views_dir: Optional[Path]):
        self.conn = hub_query.connect(path)
        self.views_dir = views_dir

    def catalog(self) -> List[Dict[str, Any]]:
        return hub_query.catalog(self.conn, self.views_dir)

    def describe(self, name: str) -> Dict[str, Any]:
        return hub_query.describe(self.conn, name, self.views_dir)

    def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        source = request.pop("source")
        return hub_query.run(self.conn, source, **request).to_dict()


class _Remote:
    """Answers from a Hub over HTTP; HTTP errors are raised as requests.HTTPError."""

    def __init__(self, url: str, auth: Optional[Tuple[str, str]]):
        self.url = url.rstrip("/")
        self.auth = auth

    def _check(self, res: requests.Response) -> Any:
        if res.status_code == 400:
            raise hub_query.QueryError(res.json().get("detail", res.text))
        if res.status_code == 404:
            raise hub_query.QueryError(f"{self.url} does not answer queries; it may run an older Kinenix Hub.")
        res.raise_for_status()
        return res.json()

    def catalog(self) -> List[Dict[str, Any]]:
        return self._check(requests.get(f"{self.url}/api/v1/query/catalog", auth=self.auth, timeout=15))["objects"]

    def describe(self, name: str) -> Dict[str, Any]:
        return self._check(requests.get(f"{self.url}/api/v1/query/describe/{name}", auth=self.auth, timeout=15))

    def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return self._check(requests.post(f"{self.url}/api/v1/query", json=request, auth=self.auth, timeout=30))


def parse_filters(pairs: Optional[List[str]]) -> Dict[str, str]:
    filters = {}
    for pair in pairs or []:
        column, sep, value = pair.partition("=")
        if not sep or not column.strip():
            raise hub_query.QueryError(f"--filter needs column=value, not '{pair}'.")
        filters[column.strip()] = value
    return filters


def _expanded(value: Any, column: str) -> Any:
    """A `details` column as a JSON object instead of text."""
    if column == "details" and isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def _records(result: Dict[str, Any], expand: bool) -> List[Dict[str, Any]]:
    columns = result["columns"]
    return [{c: (_expanded(v, c) if expand else v) for c, v in zip(columns, row)} for row in result["rows"]]


def _short(value: Any, expand: bool) -> str:
    if value is None:
        return ""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    if expand:
        return text
    text = " ".join(text.split())
    return text if len(text) <= CELL_WIDTH else text[:CELL_WIDTH - 3] + "..."


def format_result(result: Dict[str, Any], fmt: str, expand: bool = False) -> str:
    """The rows as json, csv, or md text."""
    if fmt == "json":
        return json.dumps(_records(result, expand), ensure_ascii=False, indent=2, default=str) + "\n"
    if fmt == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(result["columns"])
        for row in result["rows"]:
            writer.writerow(["" if v is None else v for v in row])
        return buffer.getvalue()
    if fmt == "md":
        def cell(value: Any) -> str:
            return _short(value, expand).replace("|", "\\|").replace("\n", " ")
        lines = ["| " + " | ".join(result["columns"]) + " |", "|" + " --- |" * len(result["columns"])]
        lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in result["rows"]]
        return "\n".join(lines) + "\n"
    raise hub_query.QueryError(f"--format must be one of {', '.join(FORMATS)}.")


def print_table(console: Console, result: Dict[str, Any], expand: bool = False) -> None:
    """A table when the columns fit the terminal; otherwise one block of column: value lines per row."""
    if not result["rows"]:
        console.print("[dim]No rows.[/]")
        return
    if len(result["columns"]) * MIN_COLUMN_WIDTH > console.width:
        width = max(len(c) for c in result["columns"])
        for number, row in enumerate(result["rows"], start=1):
            grid = Table.grid(padding=(0, 2))
            grid.add_column(style="bold cyan", no_wrap=True, min_width=width)
            grid.add_column(overflow="fold")
            for column, value in zip(result["columns"], row):
                grid.add_row(column, Text(_short(value, expand)))
            console.print(f"[bold]Row {number}[/]")
            console.print(grid)
        return
    table = Table(show_lines=expand)
    for column in result["columns"]:
        table.add_column(column, overflow="fold")
    for row in result["rows"]:
        table.add_row(*[Text(_short(v, expand)) for v in row])
    console.print(table)


def print_catalog(console: Console, objects: List[Dict[str, Any]]) -> None:
    table = Table(title="Tables and views", title_justify="left", title_style="bold")
    for column in ("Name", "Type", "Rows", "Answers"):
        table.add_column(column, overflow="fold", no_wrap=column in ("Name", "Type", "Rows"))
    for item in objects:
        rows = "-" if item["rows"] is None else str(item["rows"])
        table.add_row(Text(item["name"], style="bold" if item["type"] == "view" else ""), item["type"], rows,
                      Text(item.get("about") or ""))
    console.print(table)
    console.print("[dim]Columns and their meaning: kinenix hub query --describe NAME[/]")


def print_describe(console: Console, data: Dict[str, Any]) -> None:
    console.print(f"[bold]{escape(data['name'])}[/] ({data['type']})")
    if data.get("about"):
        console.print(Text(data["about"]))
    if data.get("doc"):
        console.print(Text(data["doc"]))
    table = Table(title="Columns", title_justify="left", title_style="bold")
    for column in ("Column", "Meaning", "Example"):
        table.add_column(column, overflow="fold", no_wrap=column == "Column")
    for column in data["columns"]:
        table.add_row(column["name"], Text(column["meaning"]), Text(column["example"], style="dim"))
    console.print(table)
    if data.get("details_keys"):
        keys = Table(title="Keys of the details column (JSON)", title_justify="left", title_style="bold")
        for column in ("Key", "Meaning", "Example"):
            keys.add_column(column, overflow="fold", no_wrap=column == "Key")
        for key in data["details_keys"]:
            keys.add_row(key["name"], Text(key["meaning"]), Text(key["example"], style="dim"))
        console.print(keys)


def _output_format(fmt: str, output: Optional[str]) -> str:
    """--output with the default table format picks the format from the file extension (csv otherwise)."""
    if output and fmt == "table":
        suffix = Path(output).suffix.lower().lstrip(".")
        return suffix if suffix in ("json", "md") else "csv"
    return fmt


def run_command(console: Console, args: Any, source: Any, error_console: Optional[Console] = None) -> None:
    """Runs one `kinenix hub query` invocation against a _Local or _Remote source. Raises QueryError."""
    error_console = error_console or console
    if args.list:
        print_catalog(console, source.catalog())
        return
    if args.describe:
        print_describe(console, source.describe(args.describe))
        return
    if not args.target:
        raise hub_query.QueryError("Name a view or table (kinenix hub query v_failures), give one SQL SELECT in quotes, "
                                   "or use --list to see what can be queried.")
    fmt = _output_format(args.format, args.output)
    request = {"source": args.target, "since": args.since, "flow": args.flow, "worker": args.worker,
               "status": args.status, "filters": parse_filters(args.filter), "limit": args.limit}
    result = source.run(request)
    more = f"Showing the first {len(result['rows'])} rows; more exist (use --limit)." if result["truncated"] else ""

    if args.output:
        Path(args.output).write_text(format_result(result, fmt, args.expand), encoding="utf-8")
        console.print(f"Wrote {len(result['rows'])} rows to {args.output} ({fmt}).")
        if more:
            console.print(f"[yellow]{more}[/]")
        return
    if fmt == "table":
        print_table(console, result, args.expand)
        console.print(f"[dim]{len(result['rows'])} rows[/]" + (f" [yellow]{more}[/]" if more else ""))
        return
    # json, csv, md go to standard output alone, so they can be piped; notes go to standard error
    console.file.write(format_result(result, fmt, args.expand))
    if more:
        error_console.print(f"[yellow]{more}[/]")


def open_source(args: Any, hub_config: Any, auth: Optional[Tuple[str, str]]) -> Any:
    if args.url:
        return _Remote(args.url, auth)
    return _Local(hub_query.database_path(hub_config.DATABASE_URL), hub_config.VIEWS_DIR)


def main(console: Console, error_console: Console, args: Any, hub_config: Any, interactive: bool) -> int:
    """Exit code of `kinenix hub query`."""
    auth = (hub_config.DASHBOARD_USER, hub_config.DASHBOARD_PASSWORD) if hub_config.DASHBOARD_PASSWORD else None
    while True:
        try:
            run_command(console, args, open_source(args, hub_config, auth), error_console)
            return 0
        except hub_query.QueryError as e:
            error_console.print(f"[bold red]Error:[/] {escape(str(e))}")
            return 1
        except requests.HTTPError as e:
            code = e.response.status_code
            if code == 401 and auth is None and interactive:
                password = ask_secret(error_console, f"Dashboard password for '{hub_config.DASHBOARD_USER}'")
                if password:
                    auth = (hub_config.DASHBOARD_USER, password)
                    continue
            hint = " Check KINENIX_HUB_DASHBOARD_USER and KINENIX_HUB_DASHBOARD_PASSWORD against the server's values." if code in (401, 403) else ""
            error_console.print(f"[bold red]Error:[/] {args.url} returned HTTP {code}.{hint}")
            return 1
        except requests.RequestException as e:
            error_console.print(f"[bold red]Error:[/] cannot reach {args.url}. Is the Hub running? ({e.__class__.__name__})")
            return 1
