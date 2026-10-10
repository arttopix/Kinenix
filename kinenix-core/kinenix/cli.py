import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import __version__
from .models.flow import FlowDefinition
from .engine.interpreter import FlowInterpreter
from .engine.logger import ExecutionLogger
from .engine.markdown import (
    FlowSync,
    load_flow,
    compile_markdown_to_json,
    export_json_to_markdown,
    markdown_issues,
    sync_flow_json,
)
from .engine.validation import validate_flow
from .scaffold import (
    DEFAULT_EXAMPLE,
    EXAMPLES_DIR,
    NEW_PROJECT_TEMPLATE,
    available_examples,
    create_new_project,
    create_project,
    project_folder_name,
)
from .workspace import (
    configured_flows_dir,
    ensure_flows_dir,
    flows_dir,
    prepare_flows_dir,
    save_flows_dir,
    settings_file as workspace_settings_file,
)


def report_validation(flow: FlowDefinition, md_path: Optional[Path] = None) -> List[str]:
    """Print validation problems as warnings and return them; with md_path, also lines flow.md ignores."""
    issues = []
    if md_path is not None and md_path.suffix.lower() == ".md" and md_path.is_file():
        issues.extend(markdown_issues(md_path.read_text(encoding="utf-8-sig")))
    issues.extend(validate_flow(flow))
    for issue in issues:
        print(f"Warning: {issue}", file=sys.stderr)
    return issues


def report_flow_sync(status: str, md_path: Path) -> None:
    """Tell the user when flow.json was rebuilt from flow.md, or when the two disagree."""
    bundle = md_path.parent
    if status == FlowSync.CREATED:
        print(f"Compiled {md_path.name} -> flow.json (flow.json did not exist).")
    elif status == FlowSync.COMPILED:
        print(f"Compiled {md_path.name} -> flow.json (flow.md has changes).")
    elif status == FlowSync.JSON_NEWER:
        print(
            f"Warning: {bundle / 'flow.json'} differs from flow.md and was edited after it (for example in Studio).\n"
            f"         Running flow.json as it is. flow.md is the source of truth, so either keep the edit with\n"
            f"           kinenix export-md {bundle}\n"
            f"         or discard it with\n"
            f"           kinenix compile {bundle}",
            file=sys.stderr,
        )


def _get_project_root() -> Optional[Path]:
    curr = Path.cwd().resolve()
    for p in [curr] + list(curr.parents):
        if (p / ".git").exists() or (p / "kinenix-core").is_dir():
            return p
    return None


def _get_search_directories() -> List[Path]:
    dirs = [
        Path.cwd(),
        flows_dir(),  # the user's flows folder (KINENIX_FLOWS_DIR, saved setting, or ~/kinenix-flows)
        Path.cwd() / "flows",
        Path.cwd() / "examples",
        Path(__file__).parent.parent / "examples",
        Path.home() / ".kinenix" / "flows",
    ]
    root = _get_project_root()
    if root:
        dirs.insert(1, root / "flows")
        dirs.append(root / "examples")

    unique_dirs = []
    seen = set()
    for d in dirs:
        if d.exists() and d.resolve() not in seen:
            seen.add(d.resolve())
            unique_dirs.append(d.resolve())
    return unique_dirs


def discover_flows() -> Dict[str, Tuple[Path, str]]:
    """
    Discovers available flow JSON and Markdown files across search directories.
    Returns dict mapping flow alias/name to (file_path, description).
    """
    discovered: Dict[str, Tuple[Path, str]] = {}

    for search_dir in _get_search_directories():
        # 1. Discover Self-Contained Project Bundles (directories with flow.json or flow.md)
        flow_candidates = list(search_dir.glob("**/flow.json")) + list(search_dir.glob("**/flow.md"))
        for flow_file in flow_candidates:
            parts = flow_file.parts
            if any(p.startswith(".") or p in ["__pycache__", "subflows", "node_modules", ".venv", "venv"] for p in parts):
                continue
            # The templates for `kinenix init` are not runnable projects; running one would write into the package
            if EXAMPLES_DIR in flow_file.resolve().parents or NEW_PROJECT_TEMPLATE in flow_file.resolve().parents:
                continue
            alias = flow_file.parent.name
            if alias in discovered and flow_file.suffix == ".md":
                # Prefer existing flow.json if already registered
                continue
            try:
                flow_def = load_flow(flow_file)
                name = flow_def.name or alias
                discovered[alias] = (flow_file, name)

                try:
                    rel = flow_file.parent.relative_to(search_dir)
                    rel_str = str(rel).replace("\\", "/")
                    if rel_str and rel_str != alias and rel_str not in discovered:
                        discovered[rel_str] = (flow_file, name)
                except ValueError:
                    pass
            except Exception:
                continue

        # 2. Discover flat flow files (*.json and *.md)
        for candidate_file in list(search_dir.glob("*.json")) + list(search_dir.glob("*.md")):
            if candidate_file.name in ["flow.json", "flow.md", "package.json", "tsconfig.json"]:
                continue
            if candidate_file.name.endswith("_flow.json") or candidate_file.name.endswith("_flow.md") or candidate_file.parent.name in ["examples", "flows"]:
                try:
                    flow_def = load_flow(candidate_file)
                    name = flow_def.name or candidate_file.stem
                    alias = candidate_file.stem
                    if alias.endswith("_flow"):
                        alias = alias[:-5]
                    if alias not in discovered:
                        discovered[alias] = (candidate_file, name)
                except Exception:
                    continue
    return discovered


def resolve_flow_path(flow_input: str) -> Optional[Path]:
    """
    Smart Flow Resolver: resolves a flow name, alias, project directory, or path into an absolute file path.
    Supports both flow.json and flow.md.
    """
    direct_path = Path(flow_input)
    # 1. Exact file path
    if direct_path.is_file():
        return direct_path.resolve()

    # 2. Directory with flow.json or flow.md
    if direct_path.is_dir():
        if (direct_path / "flow.json").is_file():
            return (direct_path / "flow.json").resolve()
        if (direct_path / "flow.md").is_file():
            return (direct_path / "flow.md").resolve()

    # 3. Direct path with extension
    for ext in [".json", ".md"]:
        p = Path(f"{flow_input}{ext}")
        if p.is_file():
            return p.resolve()

    # 4. Search discovered flows
    flows = discover_flows()
    if flow_input in flows:
        return flows[flow_input][0].resolve()

    if f"{flow_input}_flow" in flows:
        return flows[f"{flow_input}_flow"][0].resolve()

    # 5. Search directories for project bundles or files
    for search_dir in _get_search_directories():
        candidates = [
            search_dir / flow_input / "flow.json",
            search_dir / flow_input / "flow.md",
            search_dir / flow_input,
            search_dir / f"{flow_input}.json",
            search_dir / f"{flow_input}.md",
            search_dir / f"{flow_input}_flow.json",
            search_dir / f"{flow_input}_flow.md",
        ]
        for c in candidates:
            if c.is_file():
                return c.resolve()
            if c.is_dir():
                if (c / "flow.json").is_file():
                    return (c / "flow.json").resolve()
                if (c / "flow.md").is_file():
                    return (c / "flow.md").resolve()

        for matched in list(search_dir.glob(f"**/{flow_input}/flow.json")) + list(search_dir.glob(f"**/{flow_input}/flow.md")):
            if matched.is_file():
                return matched.resolve()

    return None


def main():
    parser = argparse.ArgumentParser(prog="kinenix", description="kinenix - Enterprise RPA CLI Runner")
    parser.add_argument("-v", "--version", action="version", version=f"kinenix {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run an RPA Flow by name or path (e.g. 'kinenix run rpachallenge')")
    run_parser.add_argument("flow_file", help="Flow name or path to flow.json / flow.md file")
    run_parser.add_argument("--vars", help="Optional JSON string of variables to override", default=None)
    run_parser.add_argument("--log-dir", help="Directory to save execution JSON logs (default: auto-detected project root 'logs/')", default=None)
    run_parser.add_argument("--hub", "--orchestrator", dest="hub", help="Optional Hub URL to transmit telemetry (e.g. http://localhost:8080); --orchestrator is the name from before the rename to Hub", default=None)
    run_parser.add_argument("--worker-id", help="Identifier for this worker node (default: local-worker)", default=None)

    # Command: init
    init_parser = subparsers.add_parser(
        "init", help="Create a project for a new task (kinenix init \"Get stock data\"), or copy an example (--example)")
    init_parser.add_argument("name", nargs="?", default=None,
                             help="Task name, e.g. \"Get stock data\"; the folder becomes get_stock_data")
    init_parser.add_argument("--dir", default=None, help="Folder to create instead of the one derived from the name")
    init_parser.add_argument("--example", "-e", default=None,
                             help="Copy a complete example instead of starting a new task; see --list")
    init_parser.add_argument("--list", action="store_true", help="List the available examples")

    # Command: flows-dir
    flows_dir_parser = subparsers.add_parser("flows-dir", help="Show or set the folder where your flows are kept")
    flows_dir_parser.add_argument("path", nargs="?", default=None, help="New flows folder to remember")

    # Command: actions
    actions_parser = subparsers.add_parser("actions", help="List every action and the parameters it accepts")
    actions_parser.add_argument("filter", nargs="?", default=None, help="Only actions starting with this, e.g. web or csv.write")

    # Command: compile
    compile_parser = subparsers.add_parser("compile", help="Compile a flow.md specification file into flow.json")
    compile_parser.add_argument("markdown_file", help="Path to flow.md file or project directory containing flow.md")
    compile_parser.add_argument("-o", "--output", help="Optional output flow.json path", default=None)
    compile_parser.add_argument("--strict", action="store_true", help="Exit with code 1 when validation finds problems (for CI)")

    # Command: validate
    validate_parser = subparsers.add_parser("validate", help="Check a flow for unknown actions and parameters that would be ignored")
    validate_parser.add_argument("flow_file", help="Flow name, bundle directory, flow.md, or flow.json")

    # Command: export-md
    export_parser = subparsers.add_parser("export-md", help="Export a flow.json file into human-readable flow.md")
    export_parser.add_argument("json_file", help="Path to flow.json file or project directory containing flow.json")
    export_parser.add_argument("-o", "--output", help="Optional output flow.md path", default=None)

    # Command: list
    subparsers.add_parser("list", help="List all discovered RPA Flows available to run")

    # Command: hub
    # "orchestrator" is the name from before the rename to Hub and still works as an alias
    hub_parser = subparsers.add_parser("hub", aliases=["orchestrator"], help="Start the Kinenix Hub, set it up, or show its workers and executions")
    hub_parser.add_argument("action", nargs="?", choices=["start", "status", "logs", "setup", "show-key"], default="start",
                             help="'start' runs the server (default; asks setup questions on first run); "
                                  "'status' shows workers and recent executions of a running server; "
                                  "'logs [ID]' shows the steps of one execution (latest when ID is omitted); "
                                  "'setup' changes the saved settings; 'show-key' prints the worker API key")
    hub_parser.add_argument("execution_id", nargs="?", default=None,
                             help="For 'logs': execution ID or its first characters, as shown by 'status'")
    hub_parser.add_argument("--url", default=None, help="Hub URL for 'status' and 'logs' (default: http://127.0.0.1:<port>)")
    hub_parser.add_argument("--limit", type=int, default=10, help="Number of recent executions shown by 'status' (default: 10)")
    hub_parser.add_argument("--no-prompt", action="store_true", help="Never ask questions (for services and scripts); use the environment and saved settings only")
    hub_parser.add_argument("--port", type=int, default=None, help="Port to bind the hub server (default: $KINENIX_HUB_PORT or 8080)")
    hub_parser.add_argument("--host", default=None, help="Host to bind the hub server (default: $KINENIX_HUB_HOST or 127.0.0.1; use 0.0.0.0 to accept remote connections)")

    # Command: version
    subparsers.add_parser("version", help="Show kinenix version and environment details")

    # Command: install-browsers
    subparsers.add_parser("install-browsers", help="Download and install Playwright Chromium browser")

    args = parser.parse_args()

    if args.command == "version":
        print(f"Kinenix:      v{__version__}")
        print(f"Python:       {platform.python_version()} ({platform.python_implementation()})")
        print(f"Platform:     {platform.system()} {platform.release()} ({platform.machine()})")
        sys.exit(0)

    elif args.command == "install-browsers":
        import subprocess
        print("Installing Playwright Chromium browser for kinenix...")
        res = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        if res.returncode == 0:
            print("Chromium browser successfully installed.")
        else:
            print("Installation failed. On Linux/Raspberry Pi, you may also need: sudo playwright install-deps chromium", file=sys.stderr)
        sys.exit(res.returncode)

    elif args.command == "init":
        examples = available_examples()
        if args.list:
            print("Examples (kinenix init <folder> --example <name>):\n")
            for name, description, needs_browser in examples:
                note = "  [needs a browser and internet]" if needs_browser else ""
                print(f"  {name:<14}{description}{note}")
            print('\nFor a new task of your own: kinenix init "Task name"')
            sys.exit(0)

        if not args.example and not args.name:
            print('Error: give the task a name, for example: kinenix init "Get stock data"', file=sys.stderr)
            print(f"       or copy a complete example: kinenix init --example {DEFAULT_EXAMPLE}  (see --list)",
                  file=sys.stderr)
            sys.exit(1)

        # Projects go into the flows folder (asked the first time), unless --dir names a folder
        base = None if args.dir else ensure_flows_dir(interactive=sys.stdin.isatty())
        try:
            if args.example:
                # With an example, the positional argument is the folder name, used as typed (my-bot stays my-bot)
                target = Path(args.dir) if args.dir else base / (args.name or args.example)
                created = create_project(target, args.example)
            else:
                target = Path(args.dir) if args.dir else base / project_folder_name(args.name)
                created = create_new_project(args.name, target)
        except (ValueError, FileExistsError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        # Inside the flows folder a flow runs by its folder name from anywhere; elsewhere use its path
        run_name = created.name if base and created.parent == base.resolve() else str(created)
        print(f"Created {created}" + (f" from the '{args.example}' example." if args.example
                                      else f" for '{args.name.strip()}'.") + "\n")
        print("Next steps:")
        if args.example:
            if next((nb for name, _, nb in examples if name == args.example), False):
                print("  kinenix install-browsers        # once per machine; this example drives a web browser")
            print(f"  kinenix run {run_name}")
            print(f"  Edit flow.md (the flow) and config/config.json (its values) in {created}; see its README.md")
        else:
            print(f"  1. Describe the task in {created / 'requirements.md'}")
            print(f"  2. Open {created} in your AI assistant and ask it to build the flow from requirements.md")
            print("     (it follows AGENTS.md; or write flow.md yourself)")
            print(f"  3. kinenix validate {run_name}")
            print(f"  4. kinenix run {run_name}")
        sys.exit(0)

    elif args.command == "flows-dir":
        if args.path:
            path = prepare_flows_dir(Path(args.path), use_git=False)
            save_flows_dir(path)
            print(f"Flows folder set to {path} (saved in {workspace_settings_file()}).")
            if os.environ.get("KINENIX_FLOWS_DIR"):
                print("Note: KINENIX_FLOWS_DIR is set in the environment and takes precedence over this setting.")
            sys.exit(0)
        chosen = configured_flows_dir()
        source = ("KINENIX_FLOWS_DIR" if os.environ.get("KINENIX_FLOWS_DIR")
                  else f"saved in {workspace_settings_file()}" if chosen else "default; not chosen yet")
        print(f"{flows_dir()}  ({source})")
        sys.exit(0)

    elif args.command == "actions":
        from .actions.registry import ActionRegistry
        from . import actions as _all_actions  # noqa: F401  (registers every action)

        names = sorted(n for n in ActionRegistry.list_actions() if not args.filter or n.startswith(args.filter))
        if not names:
            print(f"No action starts with '{args.filter}'.", file=sys.stderr)
            sys.exit(1)
        width = max(len(n) for n in names) + 2
        print("Actions and the parameters they accept (details: docs/actions_reference.md)\n")
        for name in names:
            params = ActionRegistry.get(name).accepted_parameters
            listed = ", ".join(params) if params else "(none)"
            print(f"  {name:<{width}}{listed}")
        print("\nEvery step also accepts: description, output_var, condition, on_error, max_retries, retry_interval, fallback_step_id")
        sys.exit(0)

    elif args.command == "validate":
        resolved_path = resolve_flow_path(args.flow_file)
        if not resolved_path:
            print(f"Error: Could not find flow '{args.flow_file}'.", file=sys.stderr)
            sys.exit(1)
        # Check the source: flow.md when the bundle has one, otherwise the given file
        source = resolved_path.parent / "flow.md" if (resolved_path.parent / "flow.md").is_file() else resolved_path
        try:
            flow_def = load_flow(source)
        except Exception as e:
            print(f"Error loading flow at '{source}': {e}", file=sys.stderr)
            sys.exit(1)
        issues = report_validation(flow_def, md_path=source)
        if issues:
            print(f"{len(issues)} problem(s) in {source}", file=sys.stderr)
            sys.exit(1)
        print(f"OK: {source} ({flow_def.name})")
        sys.exit(0)

    elif args.command == "compile":
        src = Path(args.markdown_file).resolve()
        if src.is_dir() and (src / "flow.md").is_file():
            src = src / "flow.md"
        if not src.is_file():
            print(f"Error: Markdown flow file not found at: {src}", file=sys.stderr)
            sys.exit(1)
        out = Path(args.output).resolve() if args.output else None
        try:
            target = compile_markdown_to_json(src, output_json_path=out)
            print(f"Successfully compiled: {src}")
            print(f"Output saved to:       {target}")
            issues = report_validation(load_flow(target), md_path=src)
            sys.exit(1 if issues and args.strict else 0)
        except Exception as e:
            print(f"Compilation error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "export-md":
        src = Path(args.json_file).resolve()
        if src.is_dir() and (src / "flow.json").is_file():
            src = src / "flow.json"
        if not src.is_file():
            print(f"Error: JSON flow file not found at: {src}", file=sys.stderr)
            sys.exit(1)
        out = Path(args.output).resolve() if args.output else None
        try:
            target = export_json_to_markdown(src, output_md_path=out)
            print(f"Successfully exported: {src}")
            print(f"Output saved to:       {target}")
            sys.exit(0)
        except Exception as e:
            print(f"Export error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        flows = discover_flows()
        if not flows:
            print("No flows found in current directory, 'flows/', 'examples/', or ~/.kinenix/flows/.")
            print("Tip: You can specify full file path with: kinenix run <path_to_flow.json>")
            sys.exit(0)

        # Deduplicate by resolved file path so the same flow isn't printed multiple times for different aliases
        unique_flows: Dict[Path, Tuple[str, str, List[str]]] = {}
        for alias, (path, name) in flows.items():
            resolved = path.resolve()
            if resolved not in unique_flows:
                unique_flows[resolved] = (alias, name, [alias])
            else:
                unique_flows[resolved][2].append(alias)

        print("\nAvailable Flows in kinenix:")
        print("-" * 80)
        for path, (primary_alias, name, all_aliases) in sorted(
            unique_flows.items(), key=lambda item: min(item[1][2], key=len)
        ):
            clean_alias = min(all_aliases, key=len)
            print(f"  {clean_alias:<18} | {name:<35} | {path}")
        print("-" * 80)
        print("To run a flow: kinenix run <flow_name>\n")
        sys.exit(0)

    elif args.command == "run":
        resolved_path = resolve_flow_path(args.flow_file)
        if not resolved_path:
            print(f"Error: Could not find flow '{args.flow_file}'.", file=sys.stderr)
            flows = discover_flows()
            if flows:
                print("\nAvailable flows you can run:", file=sys.stderr)
                for alias, (_, name) in sorted(flows.items()):
                    print(f"  - {alias:<16} ({name})", file=sys.stderr)
            print("\nTip: You can also specify full file path: kinenix run <path_to_flow.json>", file=sys.stderr)
            sys.exit(1)

        try:
            # A bundle's flow.md is the source; flow.json is its build output and is what runs
            if resolved_path.name in ("flow.md", "flow.json") and (resolved_path.parent / "flow.md").is_file():
                md_source = resolved_path.parent / "flow.md"
                report_flow_sync(sync_flow_json(md_source), md_source)
                resolved_path = md_source.parent / "flow.json"
            flow_def = load_flow(resolved_path)
        except Exception as e:
            print(f"Error loading flow at '{resolved_path}': {str(e)}", file=sys.stderr)
            sys.exit(1)
        report_validation(flow_def, md_path=resolved_path.parent / "flow.md")

        extra_vars = {}
        if args.vars:
            try:
                extra_vars = json.loads(args.vars)
            except Exception as e:
                print(f"Error parsing --vars JSON: {str(e)}", file=sys.stderr)
                sys.exit(1)

        extra_vars["__flow_dir__"] = str(resolved_path.parent)
        if args.hub:
            extra_vars["hub_url"] = args.hub
        if args.worker_id:
            extra_vars["worker_id"] = args.worker_id

        logger = ExecutionLogger(log_dir=args.log_dir, flow_path=resolved_path)
        interpreter = FlowInterpreter(logger=logger)
        context = interpreter.run_flow(flow_def, initial_vars=extra_vars)

        if context.has_error:
            sys.exit(1)
        sys.exit(0)

    elif args.command in ("hub", "orchestrator"):
        if args.command == "orchestrator":
            print("Note: 'kinenix orchestrator' is now 'kinenix hub'; the old name will be removed in a later release.", file=sys.stderr)
        try:
            from rich.console import Console
            from kinenix_hub import config as hub_config
            from kinenix_hub import console as hub_console
        except ImportError as e:
            print(f"Error: the Hub is not installed ({e}).")
            print("Install it with: pip install -e kinenix-hub")
            sys.exit(1)
        import importlib
        console = Console()
        interactive = hub_console.can_prompt() and not args.no_prompt

        # First start: ask the setup questions once and save them to the settings file
        first_run = args.action == "start" and not hub_config.settings_exist() and interactive
        if args.action == "setup" or first_run:
            if not hub_console.can_prompt():
                console.print("[bold red]Error:[/] setup needs an interactive terminal.")
                sys.exit(1)
            try:
                hub_console.run_setup(console, hub_config.SETTINGS_FILE)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Setup cancelled. Nothing was saved.[/]")
                sys.exit(1)
            importlib.reload(hub_config)
            if args.action == "setup":
                console.print("Start the Hub with: [bold]kinenix hub[/]")
                sys.exit(0)

        if args.action == "show-key":
            if not hub_config.API_KEY:
                console.print("No worker API key is set. Create one with: [bold]kinenix hub setup[/]")
                sys.exit(1)
            console.print(hub_config.API_KEY, soft_wrap=True)
            sys.exit(0)

        port = args.port or hub_config.PORT

        if args.action in ("status", "logs"):
            import requests
            url = args.url or f"http://127.0.0.1:{port}"
            # Same credentials the server reads; unset password works only against a localhost server
            auth = (hub_config.DASHBOARD_USER, hub_config.DASHBOARD_PASSWORD) if hub_config.DASHBOARD_PASSWORD else None
            while True:
                try:
                    with console.status(f"Reading {url}..."):
                        if args.action == "status":
                            data = hub_console.fetch_status(url, auth, args.limit)
                        else:
                            data = hub_console.fetch_execution_log(url, auth, args.execution_id)
                    break
                except LookupError as e:
                    console.print(f"[bold red]Error:[/] {e}")
                    sys.exit(1)
                except requests.HTTPError as e:
                    code = e.response.status_code
                    # Ask once for the password when the server requires one and none was given
                    if code == 401 and auth is None and interactive:
                        password = hub_console.ask_secret(console, f"Dashboard password for '{hub_config.DASHBOARD_USER}'")
                        if password:
                            auth = (hub_config.DASHBOARD_USER, password)
                            continue
                    hint = " Check KINENIX_HUB_DASHBOARD_USER and KINENIX_HUB_DASHBOARD_PASSWORD against the server's values." if code in (401, 403) else ""
                    console.print(f"[bold red]Error:[/] {url} returned HTTP {code}.{hint}")
                    sys.exit(1)
                except requests.RequestException as e:
                    console.print(f"[bold red]Error:[/] cannot reach {url}. Is the Hub running? ({e.__class__.__name__})")
                    sys.exit(1)
            if args.action == "status":
                hub_console.print_status(console, url, data)
            else:
                hub_console.print_execution_log(console, data)
            sys.exit(0)

        import uvicorn
        from kinenix_hub import app as hub_app
        host = args.host or hub_config.HOST
        hub_console.print_banner(
            console, host, port, hub_config.CENTRAL_LLM_URL,
            api_key_set=bool(hub_config.API_KEY),
            dashboard_password_set=hub_config.dashboard_password_required(),
        )
        hub_console.hide_uvicorn_bind_url()
        uvicorn.run(hub_app.app, host=host, port=port)
        sys.exit(0)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
