import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import __version__
from .models.flow import FlowDefinition
from .engine.interpreter import FlowInterpreter
from .engine.logger import ExecutionLogger
from .engine.markdown import (
    load_flow,
    compile_markdown_to_json,
    export_json_to_markdown,
)


def _get_project_root() -> Optional[Path]:
    curr = Path.cwd().resolve()
    for p in [curr] + list(curr.parents):
        if (p / ".git").exists() or (p / "bat-core").is_dir():
            return p
    return None


def _get_search_directories() -> List[Path]:
    dirs = [
        Path.cwd(),
        Path.cwd() / "flows",
        Path.cwd() / "examples",
        Path(__file__).parent.parent / "examples",
        Path.home() / ".batautomate" / "flows",
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
    parser = argparse.ArgumentParser(prog="batautomate", description="batautomate - Enterprise RPA CLI Runner")
    parser.add_argument("-v", "--version", action="version", version=f"batautomate {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run an RPA Flow by name or path (e.g. 'batautomate run rpachallenge')")
    run_parser.add_argument("flow_file", help="Flow name or path to flow.json / flow.md file")
    run_parser.add_argument("--vars", help="Optional JSON string of variables to override", default=None)
    run_parser.add_argument("--log-dir", help="Directory to save execution JSON logs (default: auto-detected project root 'logs/')", default=None)
    run_parser.add_argument("--orchestrator", help="Optional Central Orchestrator URL to transmit telemetry (e.g. http://localhost:8080)", default=None)
    run_parser.add_argument("--worker-id", help="Identifier for this worker node (default: local-worker)", default=None)

    # Command: compile
    compile_parser = subparsers.add_parser("compile", help="Compile a flow.md specification file into flow.json")
    compile_parser.add_argument("markdown_file", help="Path to flow.md file or project directory containing flow.md")
    compile_parser.add_argument("-o", "--output", help="Optional output flow.json path", default=None)

    # Command: export-md
    export_parser = subparsers.add_parser("export-md", help="Export a flow.json file into human-readable flow.md")
    export_parser.add_argument("json_file", help="Path to flow.json file or project directory containing flow.json")
    export_parser.add_argument("-o", "--output", help="Optional output flow.md path", default=None)

    # Command: list
    subparsers.add_parser("list", help="List all discovered RPA Flows available to run")

    # Command: orchestrator
    orch_parser = subparsers.add_parser("orchestrator", help="Start the Central Orchestrator & AI Dashboard web service")
    orch_parser.add_argument("--port", type=int, default=None, help="Port to bind the orchestrator server (default: $ORCHESTRATOR_PORT or 8080)")
    orch_parser.add_argument("--host", default=None, help="Host to bind the orchestrator server (default: $ORCHESTRATOR_HOST or 127.0.0.1; use 0.0.0.0 to accept remote connections)")

    # Command: version
    subparsers.add_parser("version", help="Show batautomate version and environment details")

    # Command: install-browsers
    subparsers.add_parser("install-browsers", help="Download and install Playwright Chromium browser")

    args = parser.parse_args()

    if args.command == "version":
        print(f"batautomate:   v{__version__}")
        print(f"Python:       {platform.python_version()} ({platform.python_implementation()})")
        print(f"Platform:     {platform.system()} {platform.release()} ({platform.machine()})")
        sys.exit(0)

    elif args.command == "install-browsers":
        import subprocess
        print("Installing Playwright Chromium browser for batautomate...")
        res = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        if res.returncode == 0:
            print("Chromium browser successfully installed.")
        else:
            print("Installation failed. On Linux/Raspberry Pi, you may also need: sudo playwright install-deps chromium", file=sys.stderr)
        sys.exit(res.returncode)

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
            sys.exit(0)
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
            print("No flows found in current directory, 'flows/', 'examples/', or ~/.batautomate/flows/.")
            print("Tip: You can specify full file path with: batautomate run <path_to_flow.json>")
            sys.exit(0)

        # Deduplicate by resolved file path so the same flow isn't printed multiple times for different aliases
        unique_flows: Dict[Path, Tuple[str, str, List[str]]] = {}
        for alias, (path, name) in flows.items():
            resolved = path.resolve()
            if resolved not in unique_flows:
                unique_flows[resolved] = (alias, name, [alias])
            else:
                unique_flows[resolved][2].append(alias)

        print("\nAvailable Flows in batautomate:")
        print("-" * 80)
        for path, (primary_alias, name, all_aliases) in sorted(
            unique_flows.items(), key=lambda item: min(item[1][2], key=len)
        ):
            clean_alias = min(all_aliases, key=len)
            print(f"  {clean_alias:<18} | {name:<35} | {path}")
        print("-" * 80)
        print("To run a flow: batautomate run <flow_name>\n")
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
            print("\nTip: You can also specify full file path: batautomate run <path_to_flow.json>", file=sys.stderr)
            sys.exit(1)

        try:
            if resolved_path.suffix.lower() == ".md":
                # Auto-compile to flow.json alongside flow.md
                json_target = resolved_path.parent / "flow.json"
                compile_markdown_to_json(resolved_path, json_target)
            flow_def = load_flow(resolved_path)
        except Exception as e:
            print(f"Error loading flow at '{resolved_path}': {str(e)}", file=sys.stderr)
            sys.exit(1)

        extra_vars = {}
        if args.vars:
            try:
                extra_vars = json.loads(args.vars)
            except Exception as e:
                print(f"Error parsing --vars JSON: {str(e)}", file=sys.stderr)
                sys.exit(1)

        extra_vars["__flow_dir__"] = str(resolved_path.parent)
        if args.orchestrator:
            extra_vars["orchestrator_url"] = args.orchestrator
        if args.worker_id:
            extra_vars["worker_id"] = args.worker_id

        logger = ExecutionLogger(log_dir=args.log_dir, flow_path=resolved_path)
        interpreter = FlowInterpreter(logger=logger)
        context = interpreter.run_flow(flow_def, initial_vars=extra_vars)

        if context.has_error:
            sys.exit(1)
        sys.exit(0)

    elif args.command == "orchestrator":
        import uvicorn
        from importlib import import_module
        root = _get_project_root()
        if root and str(root) not in sys.path:
            sys.path.insert(0, str(root))
        orch_app = import_module("bat-orchestrator.app")
        orch_config = import_module("bat-orchestrator.config")
        host = args.host or orch_config.HOST
        port = args.port or orch_config.PORT
        host_display = "localhost" if host == "0.0.0.0" else host
        network_note = "all interfaces, remote access enabled" if host == "0.0.0.0" else "this address only"
        print(f"\n=======================================================")
        print(f"  [BatAutomate] Central Orchestrator & AI Dashboard")
        print(f"=======================================================")
        print(f"  Web Dashboard:  http://{host_display}:{port}")
        print(f"  Listening on:   {host} ({network_note})")
        print(f"  Central LLM:    {orch_config.CENTRAL_LLM_URL}")
        print(f"=======================================================\n")
        uvicorn.run(orch_app.app, host=host, port=port)
        sys.exit(0)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
