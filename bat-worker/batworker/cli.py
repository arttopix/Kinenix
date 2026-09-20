import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .runner import WorkerRunner


def main():
    parser = argparse.ArgumentParser(
        prog="batworker",
        description="BAT Worker: Unattended Robot Daemon and Edge Execution Engine"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"batworker {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: info
    subparsers.add_parser("info", help="Display worker machine hardware, architecture, and runtime stats")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute a flow or project bundle on this worker")
    run_parser.add_argument("flow_path", help="Path to flow.json or project bundle directory")
    run_parser.add_argument("--sandbox", action="store_true", help="Execute inside an isolated temporary sandbox workspace")
    run_parser.add_argument("--vars", type=str, help="JSON string of variables to inject (e.g. '{\"env\":\"prod\"}')")
    run_parser.add_argument("--log-dir", type=str, help="Custom directory path to store execution logs")

    # Command: watch
    watch_parser = subparsers.add_parser("watch", help="Watch a directory and automatically trigger a flow when new files appear")
    watch_parser.add_argument("directory", help="Directory path to watch")
    watch_parser.add_argument("--flow", required=True, help="Path to flow.json or bundle to execute")
    watch_parser.add_argument("--pattern", default="*.*", help="File matching pattern (e.g. '*.xlsx', '*.csv')")
    watch_parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    watch_parser.add_argument("--sandbox", action="store_true", help="Execute in isolated sandbox workspace")
    watch_parser.add_argument("--vars", type=str, help="JSON string of variables to inject")

    # Command: schedule
    sched_parser = subparsers.add_parser("schedule", help="Execute a flow on a scheduled time interval")
    sched_parser.add_argument("--flow", required=True, help="Path to flow.json or bundle to execute")
    sched_parser.add_argument("--interval", type=float, default=60.0, help="Interval in seconds between runs")
    sched_parser.add_argument("--sandbox", action="store_true", help="Execute in isolated sandbox workspace")
    sched_parser.add_argument("--vars", type=str, help="JSON string of variables to inject")

    # Command: daemon
    daemon_parser = subparsers.add_parser("daemon", help="Run multi-trigger daemon using a configuration file")
    daemon_parser.add_argument("--config", default="triggers.json", help="Path to triggers.json configuration file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    runner = WorkerRunner()

    if args.command == "info":
        info = runner.get_system_info()
        print("BAT Worker System Information:")
        print("-------------------------------")
        for k, v in info.items():
            print(f"  {k}: {v}")
        sys.exit(0)

    if args.command == "run":
        extra_vars = {}
        if args.vars:
            try:
                extra_vars = json.loads(args.vars)
            except Exception as e:
                print(f"Error parsing --vars JSON: {e}", file=sys.stderr)
                sys.exit(1)

        try:
            res = runner.execute_flow(
                flow_path_or_alias=args.flow_path,
                extra_vars=extra_vars,
                use_sandbox=args.sandbox,
                log_dir=args.log_dir
            )

            print("Execution Result:")
            print(f"  Job ID: {res['job_id']}")
            print(f"  Flow Name: {res['flow_name']}")
            print(f"  Status: {res['status'].upper()}")
            print(f"  Duration: {res['duration_seconds']}s")
            print(f"  Steps Executed: {res['steps_executed']}/{res['steps_total']}")
            if res["has_error"]:
                print(f"  Error Details: {res['error']}")
                sys.exit(1)
            else:
                sys.exit(0)

        except Exception as e:
            print(f"Worker execution failed with error: {e}", file=sys.stderr)
            sys.exit(1)

    if args.command == "watch":
        from .triggers.watcher import FileWatcherTrigger

        extra_vars = {}
        if args.vars:
            try:
                extra_vars = json.loads(args.vars)
            except Exception as e:
                print(f"Error parsing --vars JSON: {e}", file=sys.stderr)
                sys.exit(1)

        watcher = FileWatcherTrigger(
            watch_dir=args.directory,
            flow_path=args.flow,
            pattern=args.pattern,
            poll_interval=args.interval,
            use_sandbox=args.sandbox,
            extra_vars=extra_vars,
            runner=runner
        )
        print(f"Watching directory '{args.directory}' for pattern '{args.pattern}'...")
        print(f"Target flow: {args.flow}")
        print("Press Ctrl+C to stop.")
        watcher.run_loop()
        sys.exit(0)

    if args.command == "schedule":
        from .triggers.scheduler import CronSchedulerTrigger

        extra_vars = {}
        if args.vars:
            try:
                extra_vars = json.loads(args.vars)
            except Exception as e:
                print(f"Error parsing --vars JSON: {e}", file=sys.stderr)
                sys.exit(1)

        scheduler = CronSchedulerTrigger(
            flow_path=args.flow,
            interval_seconds=args.interval,
            use_sandbox=args.sandbox,
            extra_vars=extra_vars,
            runner=runner
        )
        print(f"Scheduled flow '{args.flow}' to run every {args.interval}s...")
        print("Press Ctrl+C to stop.")
        scheduler.run_loop()
        sys.exit(0)

    if args.command == "daemon":
        from .triggers.manager import TriggerManager

        manager = TriggerManager(runner=runner)
        try:
            manager.load_from_config(args.config)
            print(f"Loaded triggers from '{args.config}'. Running daemon...")
            print("Press Ctrl+C to stop.")
            manager.start_all(blocking=True)
            sys.exit(0)
        except Exception as e:
            print(f"Failed to start trigger daemon: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

