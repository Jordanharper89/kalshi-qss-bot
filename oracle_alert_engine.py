"""
Oracle Alert Engine

ORACLE-023.7

Purpose:
- Process Oracle signal changes.
- Generate notifications.
- Queue approved alerts.
"""

from oracle_notification_manager import (
    OracleNotificationManager,
)


class OracleAlertEngine:

    def __init__(
        self,
        notification_manager: OracleNotificationManager,
    ):
        self.notification_manager = notification_manager

    def process_change_events(
        self,
        change_events,
    ):

        if not change_events:
            return {
                "events": 0,
                "alerts": 0,
            }

        alerts = 0

        for event in change_events:

            signal = self._event_to_signal(event)

            if self.notification_manager.process_signal(signal):
                alerts += 1

        return {
            "events": len(change_events),
            "alerts": alerts,
        }

    def _event_to_signal(
        self,
        event,
    ):

        return {
            "ticker": event.get("ticker"),
            "title": event.get("title"),
            "action": event.get("new_action"),
            "grade": event.get("new_grade"),
            "confidence_score": event.get("new_confidence"),
            "edge": event.get("new_edge"),
            "oracle_fair_value": event.get("new_fair_value"),
            "yes_price": event.get("yes_price"),
            "no_price": event.get("no_price"),
        }


oracle_alert_engine = None


def initialize_alert_engine(
    notification_manager,
):

    global oracle_alert_engine

    oracle_alert_engine = OracleAlertEngine(
        notification_manager
    )

    return oracle_alert_engine