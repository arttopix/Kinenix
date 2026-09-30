import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from ..runner import WorkerRunner

logger = logging.getLogger("kinenix_worker.trigger.scheduler")


class CronSchedulerTrigger:
    """
    Time-based scheduler trigger that dispatches flow execution at regular intervals
    or scheduled time windows.
    """

    def __init__(
        self,
        flow_path: str,
        interval_seconds: float = 60.0,
        use_sandbox: bool = False,
        extra_vars: Optional[Dict[str, Any]] = None,
        runner: Optional[WorkerRunner] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.flow_path = flow_path
        self.interval_seconds = max(0.1, float(interval_seconds))
        self.use_sandbox = use_sandbox
        self.extra_vars = extra_vars or {}
        self.runner = runner or WorkerRunner()
        self.callback = callback

        self.last_run_time: Optional[datetime] = None

    def should_run(self, now: Optional[datetime] = None) -> bool:
        current = now or datetime.now()
        if self.last_run_time is None:
            return True
        elapsed = (current - self.last_run_time).total_seconds()
        return elapsed >= self.interval_seconds

    def trigger_now(self) -> Dict[str, Any]:
        """
        Executes the flow immediately and updates last_run_time.
        """
        now = datetime.now()
        self.last_run_time = now

        injected_vars = dict(self.extra_vars)
        injected_vars["trigger_type"] = "schedule"
        injected_vars["trigger_timestamp"] = now.isoformat()

        logger.info(f"Scheduler triggering flow: {self.flow_path} at {now.isoformat()}")

        try:
            res = self.runner.execute_flow(
                flow_path_or_alias=self.flow_path,
                extra_vars=injected_vars,
                use_sandbox=self.use_sandbox
            )
            if self.callback:
                self.callback(res)
            return res
        except Exception as e:
            logger.error(f"Scheduler execution failed for '{self.flow_path}': {e}")
            return {"status": "failed", "error": str(e)}

    def check_and_run(self, now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Checks if interval has elapsed, and runs if due.
        """
        if self.should_run(now):
            return self.trigger_now()
        return None

    def run_loop(self, stop_event: Optional[Any] = None) -> None:
        """
        Runs the scheduler loop continuously.
        """
        logger.info(f"Starting scheduler on flow '{self.flow_path}' every {self.interval_seconds}s")
        while True:
            if stop_event and getattr(stop_event, "is_set", lambda: False)():
                logger.info("Scheduler received stop event. Terminating loop.")
                break
            try:
                self.check_and_run()
                time.sleep(min(1.0, self.interval_seconds))
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected error in scheduler loop: {e}")
                time.sleep(1.0)
