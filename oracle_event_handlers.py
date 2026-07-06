"""
Oracle Event Handlers

ORACLE-022.4

Purpose:
- Register default Oracle event handlers.
- Connect Oracle services through the Event Bus.
"""

from oracle_event_bus import oracle_event_bus, OracleEvents
from oracle_logger import oracle_logger


class OracleEventHandlers:

    def __init__(
        self,
        notification_service=None,
        metrics=None,
    ):
        self.notification_service = notification_service
        self.metrics = metrics

    def register(self):

        oracle_event_bus.subscribe(
            OracleEvents.RESEARCH_STARTED,
            self.on_research_started,
        )

        oracle_event_bus.subscribe(
            OracleEvents.RESEARCH_COMPLETED,
            self.on_research_completed,
        )

        oracle_event_bus.subscribe(
            OracleEvents.DISCOVERY_COMPLETED,
            self.on_discovery_completed,
        )

        oracle_event_bus.subscribe(
            OracleEvents.SIGNAL_CHANGED,
            self.on_signal_changed,
        )

        oracle_event_bus.subscribe(
            OracleEvents.OPPORTUNITY_FOUND,
            self.on_opportunity_found,
        )

        oracle_event_bus.subscribe(
            OracleEvents.ERROR,
            self.on_error,
        )

    def on_research_started(self, payload):
        oracle_logger.info("Research cycle started.")

    def on_research_completed(self, payload):
        oracle_logger.info("Research cycle completed.")

        if self.metrics and isinstance(payload, dict):
            self.metrics.update(payload)

    def on_discovery_completed(self, payload):
        oracle_logger.info("Discovery cycle completed.")

    def on_signal_changed(self, payload):
        oracle_logger.info(f"Signal changed: {payload}")

        if (
            self.notification_service
            and hasattr(
                self.notification_service,
                "handle_signal_changes",
            )
        ):
            self.notification_service.handle_signal_changes(payload)

    def on_opportunity_found(self, payload):
        oracle_logger.info(f"Opportunity found: {payload}")

    def on_error(self, payload):
        oracle_logger.error(payload)