"""
Oracle Notification Manager

ORACLE-023.6

Purpose:
- Complete notification pipeline.
- Filter -> Format -> Queue.
- Single entry point for Oracle alerts.
"""

from oracle_notification_filter import (
    OracleNotificationFilter,
)

from oracle_notification_formatter import (
    OracleNotificationFormatter,
)


class OracleNotificationManager:

    def __init__(
        self,
        dispatcher,
        min_grade="B+",
        min_edge=2.0,
        min_confidence=60.0,
    ):

        self.dispatcher = dispatcher

        self.filter = OracleNotificationFilter(
            min_grade=min_grade,
            min_edge=min_edge,
            min_confidence=min_confidence,
        )

    def process_signal(self, signal):

        if not self.filter.should_notify(signal):
            return False

        message = OracleNotificationFormatter.format(
            signal
        )

        notification_id = (
            signal.get("ticker", "UNKNOWN")
            + "_"
            + signal.get("action", "PASS")
        )

        self.dispatcher.queue_notification(
            notification_id,
            message,
        )

        return True

    def process_signals(self, signals):

        accepted = 0

        for signal in signals:

            if self.process_signal(signal):
                accepted += 1

        return {
            "processed": len(signals),
            "queued": accepted,
        }


oracle_notification_manager = None


def initialize_notification_manager(
    dispatcher,
    min_grade="B+",
    min_edge=2.0,
    min_confidence=60.0,
):

    global oracle_notification_manager

    oracle_notification_manager = (
        OracleNotificationManager(
            dispatcher,
            min_grade=min_grade,
            min_edge=min_edge,
            min_confidence=min_confidence,
        )
    )

    return oracle_notification_manager