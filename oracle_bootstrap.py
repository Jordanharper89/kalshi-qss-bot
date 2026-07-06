"""
Oracle Bootstrap

ORACLE-022.0

Purpose:
- Build and initialize the complete Oracle system.
- Creates all Oracle services.
- Starts scheduler if enabled.
- Returns a ready-to-use Oracle instance.
"""

from oracle_config import oracle_config
from oracle_session_manager import OracleSessionManager
from oracle_scheduler import OracleScheduler
from oracle_health_monitor import OracleHealthMonitor
from oracle_metrics import OracleMetrics
from oracle_state_store import OracleStateStore
from oracle_logger import oracle_logger


class OracleBootstrap:

    def __init__(
        self,
        market_data_service,
        watchlist_service,
        research_service,
        notification_service=None,
    ):

        self.market_data_service = market_data_service
        self.watchlist_service = watchlist_service
        self.research_service = research_service
        self.notification_service = notification_service

        self.metrics = OracleMetrics()
        self.state_store = OracleStateStore()

        self.session_manager = OracleSessionManager(
            market_data_service=self.market_data_service,
            watchlist_service=self.watchlist_service,
            research_service=self.research_service,
            notification_service=self.notification_service,
            preferred_categories=oracle_config.preferred_categories,
        )

        self.scheduler = OracleScheduler(
            oracle_session_manager=self.session_manager,
            interval_seconds=oracle_config.discovery_interval_seconds,
        )

        self.health_monitor = OracleHealthMonitor(
            session_manager=self.session_manager,
            scheduler=self.scheduler,
        )

    def start(self):

        oracle_logger.info("Oracle Bootstrap Starting")

        if oracle_config.scheduler_enabled:
            self.scheduler.start()
            oracle_logger.info("Oracle Scheduler Started")

    def stop(self):

        self.scheduler.stop()

        oracle_logger.info("Oracle Scheduler Stopped")

    def status(self):

        return self.health_monitor.report()

    def session(self):

        return self.session_manager

    def metrics_snapshot(self):

        return self.metrics.snapshot()