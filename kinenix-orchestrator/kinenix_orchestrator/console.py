"""Terminal output for `kinenix orchestrator`: the startup banner and the `status` command."""
import logging
import secrets
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .settings_file import hash_password, read_settings, write_settings

WORKER_STATUS_STYLES = {"online": "green", "busy": "yellow", "offline": "red"}
EXECUTION_STATUS_STYLES = {"success": "green", "failed": "red", "running": "yellow"}
STEP_STATUS_STYLES = {"success": "green", "failed": "red", "skipped": "dim"}


def lan_ip() -> Optional[str]:
    """IP address of the interface used for outbound traffic (no packets are sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 80))
            ip = s.getsockname()[0]
    except OSError:
        return None
    return None if ip.startswith("127.") else ip


def browser_urls(host: str, port: int) -> List[str]:
    """URLs a person can open for a given bind address; 0.0.0.0 itself is not a valid browser address."""
    if host in ("0.0.0.0", "::"):
        urls = [f"http://127.0.0.1:{port}"]
        ip = lan_ip()
        if ip:
            urls.append(f"http://{ip}:{port}")
        return urls
    return [f"http://{host}:{port}"]


class _HideBindUrl(logging.Filter):
    """Drops uvicorn's "Uvicorn running on http://0.0.0.0:..." line; the banner already shows URLs that open."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not str(record.msg).startswith("Uvicorn running on")


def hide_uvicorn_bind_url() -> None:
    logging.getLogger("uvicorn.error").addFilter(_HideBindUrl())


def print_banner(console: Console, host: str, port: int, llm_url: str, api_key_set: bool, dashboard_password_set: bool) -> None:
    remote = host in ("0.0.0.0", "::")
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", no_wrap=True)
    grid.add_column(overflow="fold")

    urls = browser_urls(host, port)
    grid.add_row("Dashboard", urls[0])
    if len(urls) > 1:
        grid.add_row("Worker URL", Text(urls[1], style="bold"))
    grid.add_row("Listening on", f"{host}:{port} " + ("(all interfaces)" if remote else "(this address only)"))
    grid.add_row("Worker API key", Text("set", style="green") if api_key_set else Text("not set: localhost workers only", style="yellow"))
    grid.add_row("Dashboard login", Text("set", style="green") if dashboard_password_set else Text("not set: localhost viewers only", style="yellow"))
    grid.add_row("Central LLM", llm_url)

    console.print(Panel(grid, title="[bold]Kinenix Orchestrator[/]", subtitle="[dim]Ctrl+C to stop[/]",
                        border_style="cyan", expand=False))


def can_prompt() -> bool:
    """Prompts are shown only in an interactive terminal, never when run as a service or from a script."""
    return sys.stdin is not None and sys.stdin.isatty()


def ask_secret(console: Console, label: str) -> str:
    return console.input(f"[bold cyan]{label}[/]: ", password=True).strip()


def ask_text(console: Console, label: str, default: str) -> str:
    return console.input(f"[bold cyan]{label}[/] [dim]\\[{default}][/]: ").strip() or default


def ask_yes_no(console: Console, label: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        answer = console.input(f"[bold cyan]{label}[/] [dim]\\[{hint}][/]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        console.print("[red]Please answer y or n.[/]")


def _ask_port(console: Console, default: str) -> str:
    while True:
        port = ask_text(console, "Port", default)
        if port.isdigit() and 0 < int(port) < 65536:
            return port
        console.print("[red]Enter a number between 1 and 65535.[/]")


def _ask_new_password(console: Console, label: str) -> str:
    """Hidden input asked twice; an empty answer means no change."""
    while True:
        password = ask_secret(console, label)
        if not password or ask_secret(console, "Repeat dashboard password") == password:
            return password
        console.print("[red]Passwords do not match. Try again.[/]")


def run_setup(console: Console, path: Path) -> Dict[str, str]:
    """Interactive first-run setup. Saves the answers to the settings file and returns them."""
    values = read_settings(path)
    console.print(Panel(
        "Answers are saved to " + str(path) + "\nso next time `kinenix orchestrator` starts without questions.\n"
        "[dim]Run `kinenix orchestrator setup` again to change them.[/]",
        title="[bold]Kinenix Orchestrator setup[/]", border_style="cyan", expand=False,
    ))

    remote = ask_yes_no(console, "Allow workers on other machines (e.g. a Raspberry Pi) to connect?",
                        default=values.get("ORCHESTRATOR_HOST", "0.0.0.0") != "127.0.0.1")
    values["ORCHESTRATOR_HOST"] = "0.0.0.0" if remote else "127.0.0.1"
    values["ORCHESTRATOR_PORT"] = _ask_port(console, values.get("ORCHESTRATOR_PORT", "8080"))

    new_key = None
    if remote:
        has_key = bool(values.get("ORCHESTRATOR_API_KEY"))
        typed = ask_secret(console, "Worker API key (Enter to keep the current key)" if has_key
                           else "Worker API key (Enter to generate a new one)")
        if typed:
            values["ORCHESTRATOR_API_KEY"] = typed
        elif not has_key:
            new_key = values["ORCHESTRATOR_API_KEY"] = secrets.token_urlsafe(32)

        user = values.get("ORCHESTRATOR_DASHBOARD_USER", "admin")
        has_password = bool(values.get("ORCHESTRATOR_DASHBOARD_PASSWORD_HASH"))
        password = _ask_new_password(
            console,
            f"Dashboard password for '{user}' " + ("(Enter to keep the current password)" if has_password
                                                   else "(Enter to allow localhost viewers only)"),
        )
        if password:
            values["ORCHESTRATOR_DASHBOARD_PASSWORD_HASH"] = hash_password(password)

    write_settings(path, values)
    console.print(f"[green]Saved[/] {path}")
    if new_key:
        console.print(Panel(
            f"{new_key}\n\n[dim]Set it on each worker as KINENIX_ORCHESTRATOR_API_KEY.\n"
            "Show it again with: kinenix orchestrator show-key[/]",
            title="[bold]New worker API key[/]", border_style="yellow", expand=False,
        ))
    return values


def fetch_status(base_url: str, auth: Optional[Tuple[str, str]], limit: int) -> Dict[str, Any]:
    """Read workers and recent executions. Raises requests.RequestException on network or HTTP errors."""
    base_url = base_url.rstrip("/")
    workers = requests.get(f"{base_url}/api/v1/workers", auth=auth, timeout=5)
    workers.raise_for_status()
    executions = requests.get(f"{base_url}/api/v1/executions", params={"limit": limit}, auth=auth, timeout=5)
    executions.raise_for_status()
    return {"workers": workers.json()["workers"], "executions": executions.json()["executions"]}


def _ago(iso_timestamp: Optional[str], now: Optional[datetime] = None) -> str:
    if not iso_timestamp:
        return "-"
    try:
        then = datetime.fromisoformat(iso_timestamp)
    except ValueError:
        return iso_timestamp
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    seconds = int(((now or datetime.now(timezone.utc)) - then).total_seconds())
    if seconds < 60:
        return f"{max(seconds, 0)}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _styled(value: str, styles: Dict[str, str]) -> Text:
    return Text(value or "-", style=styles.get(value, ""))


def print_status(console: Console, base_url: str, data: Dict[str, Any], now: Optional[datetime] = None) -> None:
    workers = Table(title=f"Workers ({len(data['workers'])})", title_justify="left", title_style="bold")
    for column in ("Worker", "IP", "Status", "Task", "CPU", "RAM", "Last seen"):
        workers.add_column(column, no_wrap=column in ("Status", "CPU", "Last seen"))
    for w in sorted(data["workers"], key=lambda w: w["id"]):
        cpu = w.get("cpu_percent")
        workers.add_row(
            w["id"],
            w.get("ip_address") or "-",
            _styled(w.get("status"), WORKER_STATUS_STYLES),
            w.get("current_task") or "-",
            f"{cpu:.0f}%" if cpu is not None else "-",
            w.get("ram_usage") or "-",
            _ago(w.get("last_heartbeat"), now),
        )

    executions = Table(title=f"Recent executions ({len(data['executions'])})", title_justify="left", title_style="bold")
    for column in ("ID", "When", "Flow", "Worker", "Status", "Duration", "Failure"):
        executions.add_column(column, no_wrap=column in ("ID", "When", "Status", "Duration"))
    for e in data["executions"]:
        failure = "-"
        if e.get("has_error"):
            failure = e.get("ai_summary") or e.get("error_message") or e.get("failed_step_name") or "failed"
        executions.add_row(
            Text(short_id(e.get("id")), style="dim"),
            _ago(e.get("created_at"), now),
            Text(e.get("flow_name") or "-"),
            Text(e.get("worker_id") or "-"),
            _styled(e.get("status"), EXECUTION_STATUS_STYLES),
            f"{e.get('duration_seconds') or 0:.1f}s",
            Text(failure, style="red" if e.get("has_error") else ""),
        )

    console.print(f"[bold]Kinenix Orchestrator[/] [dim]{base_url}[/]")
    console.print(workers if data["workers"] else "[dim]No workers have sent a heartbeat yet.[/]")
    console.print(executions if data["executions"] else "[dim]No executions recorded yet.[/]")
    if data["executions"]:
        console.print("[dim]Step details: kinenix orchestrator logs <ID>  (latest run when ID is omitted)[/]")


SHORT_ID_LENGTH = 8


def short_id(execution_id: Optional[str]) -> str:
    return (execution_id or "-")[:SHORT_ID_LENGTH]


def fetch_execution_log(base_url: str, auth: Optional[Tuple[str, str]], id_prefix: Optional[str]) -> Dict[str, Any]:
    """Find an execution by ID prefix (latest when None) among recent runs and return it with its steps.

    Raises LookupError when no or several executions match, and requests.RequestException on network or HTTP errors.
    """
    base_url = base_url.rstrip("/")
    res = requests.get(f"{base_url}/api/v1/executions", params={"limit": 200}, auth=auth, timeout=5)
    res.raise_for_status()
    executions = res.json()["executions"]
    if not executions:
        raise LookupError("No executions recorded yet.")

    if id_prefix:
        matches = [e for e in executions if e["id"].startswith(id_prefix)]
        if not matches:
            raise LookupError(f"No recent execution ID starts with '{id_prefix}'.")
        if len(matches) > 1:
            raise LookupError(f"'{id_prefix}' matches {len(matches)} executions; type more characters of the ID.")
        execution_id = matches[0]["id"]
    else:
        execution_id = executions[0]["id"]

    res = requests.get(f"{base_url}/api/v1/executions/{execution_id}/steps", auth=auth, timeout=5)
    res.raise_for_status()
    return res.json()


def print_execution_log(console: Console, data: Dict[str, Any], now: Optional[datetime] = None) -> None:
    e = data["execution"]
    failed = bool(e.get("has_error"))

    header = Table.grid(padding=(0, 2))
    header.add_column(style="bold cyan", no_wrap=True)
    header.add_column(overflow="fold")
    header.add_row("Flow", Text(e.get("flow_name") or "-"))
    header.add_row("Worker", Text(e.get("worker_id") or "-"))
    header.add_row("Status", _styled(e.get("status"), EXECUTION_STATUS_STYLES))
    header.add_row("Started", f"{e.get('start_time') or '-'} ({_ago(e.get('created_at'), now)})")
    header.add_row("Duration", f"{e.get('duration_seconds') or 0:.1f}s")
    header.add_row("ID", e.get("id") or "-")
    if failed:
        header.add_row("Failed step", Text(e.get("failed_step_name") or e.get("failed_step_id") or "-", style="red"))
        header.add_row("Error", Text(e.get("error_message") or "-", style="red"))
        if e.get("ai_summary"):
            header.add_row("AI summary", Text(e["ai_summary"]))
        if e.get("ai_suggestion"):
            header.add_row("Suggestion", Text(e["ai_suggestion"]))
    console.print(Panel(header, title="[bold]Execution[/]", border_style="red" if failed else "green", expand=False))

    steps = data.get("steps") or []
    if not steps:
        console.print("[dim]No step details were recorded for this execution.[/]")
        return

    table = Table(title=f"Steps ({len(steps)})", title_justify="left", title_style="bold")
    for column in ("#", "Step", "Action", "Status", "Duration", "Error"):
        table.add_column(column, no_wrap=column in ("#", "Status", "Duration"))
    for number, step in enumerate(steps, start=1):
        duration = step.get("duration_seconds")
        error = step.get("error_message") or "-"
        if step.get("error_type") and step.get("error_message"):
            error = f"{step['error_type']}: {step['error_message']}"
        table.add_row(
            str(number),
            Text(step.get("step_name") or step.get("step_id") or "-"),
            Text(step.get("action") or "-", style="dim"),
            _styled(step.get("status"), STEP_STATUS_STYLES),
            f"{duration:.1f}s" if isinstance(duration, (int, float)) else "-",
            Text(error, style="red" if step.get("error_message") else ""),
        )
    console.print(table)
