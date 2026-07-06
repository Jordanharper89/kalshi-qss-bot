"""
Oracle Dashboard Engine

ORACLE-024.0

Purpose:
- Build one clean Oracle dashboard snapshot.
- Combines status, metrics, alerts, feed, scheduler, and health.
- No Telegram sending.
- No trade execution.
"""


class OracleDashboardEngine:

    def __init__(
        self,
        oracle_engine=None,
        scheduler=None,
        health_monitor=None,
        metrics=None,
        alert_history=None,
        alert_statistics=None,
    ):
        self.oracle_engine = oracle_engine
        self.scheduler = scheduler
        self.health_monitor = health_monitor
        self.metrics = metrics
        self.alert_history = alert_history
        self.alert_statistics = alert_statistics

    def snapshot(self):

        return {
            "status": self._safe_status(),
            "health": self._safe_health(),
            "scheduler": self._safe_scheduler(),
            "metrics": self._safe_metrics(),
            "opportunity_feed": self._safe_feed(),
            "recent_alerts": self._safe_alerts(),
            "alert_statistics": self._safe_alert_statistics(),
        }

    def _safe_status(self):
        try:
            if self.oracle_engine:
                return self.oracle_engine.status()
        except Exception as error:
            return {"error": str(error)}

        return {}

    def _safe_health(self):
        try:
            if self.health_monitor:
                return self.health_monitor.report()
        except Exception as error:
            return {"error": str(error)}

        return {}

    def _safe_scheduler(self):
        try:
            if self.scheduler:
                return self.scheduler.status()
        except Exception as error:
            return {"error": str(error)}

        return {}

    def _safe_metrics(self):
        try:
            if self.metrics:
                return self.metrics.snapshot()
        except Exception as error:
            return {"error": str(error)}

        return {}

    def _safe_feed(self):
        try:
            if self.oracle_engine:
                result = self.oracle_engine.feed()

                if isinstance(result, dict):
                    return result.get("result", result)

                return result
        except Exception as error:
            return {"error": str(error)}

        return []

    def _safe_alerts(self):
        try:
            if self.alert_history:
                return self.alert_history.latest(limit=10)
        except Exception as error:
            return [{"error": str(error)}]

        return []

    def _safe_alert_statistics(self):
        try:
            if self.alert_statistics:
                return self.alert_statistics.snapshot()
        except Exception as error:
            return {"error": str(error)}

        return {}


oracle_dashboard_engine = None


def initialize_dashboard_engine(
    oracle_engine=None,
    scheduler=None,
    health_monitor=None,
    metrics=None,
    alert_history=None,
    alert_statistics=None,
):
    global oracle_dashboard_engine

    oracle_dashboard_engine = OracleDashboardEngine(
        oracle_engine=oracle_engine,
        scheduler=scheduler,
        health_monitor=health_monitor,
        metrics=metrics,
        alert_history=alert_history,
        alert_statistics=alert_statistics,
    )

    return oracle_dashboard_engine