"""Terminal output for the kinenix-worker CLI, rendered with rich.

rich drops colors and styling automatically when output is redirected to a file or pipe.
"""
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .orchestrator_client import OrchestratorClient


def _yes_no(value: bool) -> Text:
    return Text("yes", style="green") if value else Text("no", style="bold red")


def _key_value_grid() -> Table:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", no_wrap=True)
    grid.add_column(overflow="fold")
    return grid


def print_ping(console: Console, client: OrchestratorClient, result: Dict[str, Any]) -> None:
    grid = _key_value_grid()
    grid.add_row("Orchestrator", client.url or Text("(not set)", style="yellow"))
    grid.add_row("Worker ID", client.worker_id)
    grid.add_row("Reachable", _yes_no(result["reachable"]))
    grid.add_row("Authorized", _yes_no(result["authorized"]))
    grid.add_row("Detail", result["detail"])

    ok = result["authorized"]
    console.print(Panel(
        grid,
        title="[bold]kinenix-worker ping[/]",
        subtitle="[green]connected[/]" if ok else "[red]not connected[/]",
        border_style="green" if ok else "red",
        expand=False,
    ))


def print_info(console: Console, info: Dict[str, Any], client: OrchestratorClient) -> None:
    system = _key_value_grid()
    for key, value in info.items():
        system.add_row(key, str(value))

    orchestrator = _key_value_grid()
    orchestrator.add_row("worker_id", client.worker_id)
    orchestrator.add_row("orchestrator_url", client.url or Text("(not set)", style="yellow"))
    orchestrator.add_row(
        "orchestrator_api_key",
        Text("(set)", style="green") if client.api_key else Text("(not set)", style="yellow"),
    )

    console.print(Panel(system, title="[bold]System[/]", border_style="cyan", expand=False))
    console.print(Panel(orchestrator, title="[bold]Orchestrator[/]", border_style="cyan", expand=False))


def print_run_result(console: Console, res: Dict[str, Any]) -> None:
    failed = res["has_error"]
    status = Text(res["status"].upper(), style="bold red" if failed else "bold green")

    grid = _key_value_grid()
    grid.add_row("Status", status)
    grid.add_row("Flow", res["flow_name"])
    grid.add_row("Steps", f"{res['steps_executed']}/{res['steps_total']}")
    grid.add_row("Duration", f"{res['duration_seconds']}s")
    grid.add_row("Job ID", res["job_id"])
    if failed:
        grid.add_row("Error", Text(str(res["error"]), style="red"))

    console.print(Panel(
        grid,
        title="[bold]Execution Result[/]",
        border_style="red" if failed else "green",
        expand=False,
    ))
