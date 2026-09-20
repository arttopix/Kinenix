import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .watcher import FileWatcherTrigger
from .scheduler import CronSchedulerTrigger
from ..runner import WorkerRunner

logger = logging.getLogger("batworker.trigger.manager")


class TriggerManager:
    """
    Manages multiple concurrent triggers (file watchers, schedulers).
    Can be configured programmatically or loaded from a triggers configuration file.
    """

    def __init__(self, runner: Optional[WorkerRunner] = None):
        self.runner = runner or WorkerRunner()
        self.triggers: List[Any] = []
        self._stop_event = threading.Event()
        self._threads: List[threading.Thread] = []

    def add_trigger(self, trigger: Any) -> None:
        self.triggers.append(trigger)

    def load_from_config(self, config_path: str) -> None:
        p = Path(config_path).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Triggers configuration file not found: {p}")

        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            trigger_list = data.get("triggers", [])
        elif isinstance(data, list):
            trigger_list = data
        else:
            raise ValueError("Triggers configuration must be a list or a dict with a 'triggers' array.")

        for item in trigger_list:
            t_type = item.get("type", "").lower()
            flow = item.get("flow") or item.get("flow_path")
            if not flow:
                logger.warning(f"Skipping trigger without flow: {item}")
                continue

            if t_type in ("file_watcher", "watcher", "file"):
                watch_dir = item.get("watch_dir") or item.get("directory", ".")
                pattern = item.get("pattern", "*.*")
                interval = float(item.get("interval", 2.0))
                self.add_trigger(
                    FileWatcherTrigger(
                        watch_dir=watch_dir,
                        flow_path=flow,
                        pattern=pattern,
                        poll_interval=interval,
                        runner=self.runner,
                        extra_vars=item.get("vars", {})
                    )
                )
            elif t_type in ("scheduler", "cron", "interval"):
                sec = float(item.get("interval_seconds") or item.get("interval", 60.0))
                self.add_trigger(
                    CronSchedulerTrigger(
                        flow_path=flow,
                        interval_seconds=sec,
                        runner=self.runner,
                        extra_vars=item.get("vars", {})
                    )
                )
            else:
                logger.warning(f"Unknown trigger type '{t_type}', skipping.")

    def start_all(self, blocking: bool = True) -> None:
        self._stop_event.clear()
        self._threads = []

        for trigger in self.triggers:
            t = threading.Thread(target=trigger.run_loop, args=(self._stop_event,), daemon=True)
            t.start()
            self._threads.append(t)

        logger.info(f"Started {len(self._threads)} triggers in background daemon.")

        if blocking:
            try:
                while not self._stop_event.is_set():
                    time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("Trigger manager received shutdown signal.")
                self.stop()

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=2.0)
        logger.info("All triggers stopped.")
