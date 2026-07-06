"""
Oracle Application

ORACLE-022.1

Purpose:
- Single entry point for Oracle.
- Provides one interface for the Telegram bot.
- Wraps Bootstrap, Session Manager, Scheduler,
  Opportunity Feed, Health Monitor, and Metrics.
"""

from oracle_bootstrap import OracleBootstrap


class OracleApp:

    def __init__(
        self,
        market_data_service,
        watchlist_service,
        research_service,
        notification_service=None,
    ):

        self.bootstrap = OracleBootstrap(
            market_data_service=market_data_service,
            watchlist_service=watchlist_service,
            research_service=research_service,
            notification_service=notification_service,
        )

        self.bootstrap.start()

    def run(self):
        return self.bootstrap.session().run_once()

    def opportunity_feed(self):
        return self.bootstrap.session().build_opportunity_feed()

    def status(self):
        return self.bootstrap.status()

    def metrics(self):
        return self.bootstrap.metrics_snapshot()

    def stop(self):
        self.bootstrap.stop()