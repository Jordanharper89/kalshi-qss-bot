"""
Oracle Runtime

ORACLE-022.6

Purpose:
- Single runtime object for Oracle.
- Coordinates lifecycle, scheduler, metrics, state, and session.
"""

from oracle_lifecycle import oracle_lifecycle
from oracle_logger import oracle_logger


class OracleRuntime:

    def __init__(
        self,
        app,
        scheduler,
        metrics,
        state_store,
        health_monitor,
    ):
        self.app = app
        self.scheduler = scheduler
        self.metrics = metrics
        self.state_store = state_store
        self.health_monitor = health_monitor

    def start(self):

        oracle_lifecycle.start()

        if not self.scheduler.is_running():
            self.scheduler.start()

        oracle_logger.info("Oracle Runtime Started")

    def stop(self):

        if self.scheduler.is_running():
            self.scheduler.stop()

        self.state_store.save(
            {
                "metrics": self.metrics.snapshot(),
                "health": self.health_monitor.report(),
            }
        )

        oracle_lifecycle.stop()

        oracle_logger.info("Oracle Runtime Stopped")

    def run_cycle(self):

        result = self.app.run()

        if isinstance(result, dict):
            self.metrics.update(result)

        return result

    def opportunity_feed(self):
        return self.app.opportunity_feed()

    def status(self):
        return self.health_monitor.report()

    def metrics_snapshot(self):
        return self.metrics.snapshot()

    def save_state(self):

        self.state_store.save(
            {
                "metrics": self.metrics.snapshot(),
                "health": self.health_monitor.report(),
            }
        )

    def load_state(self):
        return self.state_store.load()