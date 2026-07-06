"""
Oracle Notification Filter

ORACLE-023.4

Purpose:
- Decide whether an Oracle event should generate
  a notification.
- Prevent notification spam.
"""


class OracleNotificationFilter:

    def __init__(
        self,
        min_grade="B+",
        min_edge=2.0,
        min_confidence=60.0,
    ):
        self.min_grade = min_grade
        self.min_edge = min_edge
        self.min_confidence = min_confidence

        self.grade_order = {
            "C": 0,
            "C+": 1,
            "B-": 2,
            "B": 3,
            "B+": 4,
            "A-": 5,
            "A": 6,
            "A+": 7,
        }

    def should_notify(self, signal):

        if not isinstance(signal, dict):
            return False

        action = signal.get("action", "PASS")

        if action == "PASS":
            return False

        grade = signal.get("grade", "C")
        edge = float(signal.get("edge", 0))
        confidence = float(signal.get("confidence_score", 0))

        if self.grade_order.get(
            grade,
            0,
        ) < self.grade_order.get(
            self.min_grade,
            4,
        ):
            return False

        if edge < self.min_edge:
            return False

        if confidence < self.min_confidence:
            return False

        return True

    def filter(self, signals):

        if not signals:
            return []

        return [
            signal
            for signal in signals
            if self.should_notify(signal)
        ]


oracle_notification_filter = OracleNotificationFilter()