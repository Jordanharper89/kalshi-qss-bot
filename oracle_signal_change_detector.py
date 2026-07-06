"""
Oracle Signal Change Detector

KQ-018.1

Purpose:
- Compare previous Oracle signal state vs latest Oracle research result.
- Detect meaningful signal changes.
- Return structured change events only.
- Does NOT send alerts.
- Does NOT execute trades.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


GRADE_RANK = {
    "F": 0,
    "D": 1,
    "C": 2,
    "C+": 3,
    "B-": 4,
    "B": 5,
    "B+": 6,
    "A-": 7,
    "A": 8,
    "A+": 9,
}


ACTION_RANK = {
    "PASS": 0,
    "BUY YES": 1,
    "BUY NO": 1,
}


@dataclass
class SignalChangeEvent:
    ticker: str
    change_type: str
    field: str
    previous_value: Any
    latest_value: Any
    severity: str
    message: str
    detected_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleSignalChangeDetector:
    """
    Compares old Oracle signal state against new Oracle signal state.

    This class is intentionally stateless.
    It receives two dictionaries:
    - previous_signal
    - latest_signal

    It returns a list of structured change events.
    """

    def __init__(
        self,
        confidence_threshold: float = 5.0,
        edge_threshold: float = 1.0,
        fair_value_threshold: float = 2.0,
    ):
        self.confidence_threshold = confidence_threshold
        self.edge_threshold = edge_threshold
        self.fair_value_threshold = fair_value_threshold

    def detect_changes(
        self,
        previous_signal: Optional[Dict[str, Any]],
        latest_signal: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Main public method.

        Returns:
            List[Dict[str, Any]]
        """

        if not latest_signal:
            return []

        ticker = self._get_ticker(latest_signal)
        detected_at = self._utc_now()

        if not previous_signal:
            return [
                SignalChangeEvent(
                    ticker=ticker,
                    change_type="NEW_SIGNAL",
                    field="signal",
                    previous_value=None,
                    latest_value=self._safe_action(latest_signal),
                    severity="INFO",
                    message=f"New Oracle signal created for {ticker}.",
                    detected_at=detected_at,
                ).to_dict()
            ]

        events: List[SignalChangeEvent] = []

        events.extend(
            self._detect_action_change(
                ticker=ticker,
                previous_signal=previous_signal,
                latest_signal=latest_signal,
                detected_at=detected_at,
            )
        )

        events.extend(
            self._detect_confidence_change(
                ticker=ticker,
                previous_signal=previous_signal,
                latest_signal=latest_signal,
                detected_at=detected_at,
            )
        )

        events.extend(
            self._detect_edge_change(
                ticker=ticker,
                previous_signal=previous_signal,
                latest_signal=latest_signal,
                detected_at=detected_at,
            )
        )

        events.extend(
            self._detect_fair_value_change(
                ticker=ticker,
                previous_signal=previous_signal,
                latest_signal=latest_signal,
                detected_at=detected_at,
            )
        )

        events.extend(
            self._detect_grade_change(
                ticker=ticker,
                previous_signal=previous_signal,
                latest_signal=latest_signal,
                detected_at=detected_at,
            )
        )

        events.extend(
            self._detect_reason_change(
                ticker=ticker,
                previous_signal=previous_signal,
                latest_signal=latest_signal,
                detected_at=detected_at,
            )
        )

        events.extend(
            self._detect_expected_hold_change(
                ticker=ticker,
                previous_signal=previous_signal,
                latest_signal=latest_signal,
                detected_at=detected_at,
            )
        )

        return [event.to_dict() for event in events]

    def _detect_action_change(
        self,
        ticker: str,
        previous_signal: Dict[str, Any],
        latest_signal: Dict[str, Any],
        detected_at: str,
    ) -> List[SignalChangeEvent]:
        previous_action = self._safe_action(previous_signal)
        latest_action = self._safe_action(latest_signal)

        if previous_action == latest_action:
            return []

        severity = "INFO"
        change_type = "ACTION_CHANGED"

        if previous_action == "PASS" and latest_action in ("BUY YES", "BUY NO"):
            severity = "HIGH"
            change_type = "ACTION_UPGRADED_TO_BUY"

        elif previous_action in ("BUY YES", "BUY NO") and latest_action == "PASS":
            severity = "HIGH"
            change_type = "ACTION_DOWNGRADED_TO_PASS"

        elif previous_action in ("BUY YES", "BUY NO") and latest_action in ("BUY YES", "BUY NO"):
            severity = "CRITICAL"
            change_type = "ACTION_FLIPPED"

        return [
            SignalChangeEvent(
                ticker=ticker,
                change_type=change_type,
                field="action",
                previous_value=previous_action,
                latest_value=latest_action,
                severity=severity,
                message=f"Oracle action changed: {previous_action} → {latest_action}",
                detected_at=detected_at,
            )
        ]

    def _detect_confidence_change(
        self,
        ticker: str,
        previous_signal: Dict[str, Any],
        latest_signal: Dict[str, Any],
        detected_at: str,
    ) -> List[SignalChangeEvent]:
        previous_value = self._safe_float(previous_signal.get("confidence_score"))
        latest_value = self._safe_float(latest_signal.get("confidence_score"))

        if previous_value is None or latest_value is None:
            return []

        diff = latest_value - previous_value

        if abs(diff) < self.confidence_threshold:
            return []

        change_type = "CONFIDENCE_INCREASED" if diff > 0 else "CONFIDENCE_DECREASED"
        severity = "MEDIUM"

        if abs(diff) >= 15:
            severity = "HIGH"

        return [
            SignalChangeEvent(
                ticker=ticker,
                change_type=change_type,
                field="confidence_score",
                previous_value=previous_value,
                latest_value=latest_value,
                severity=severity,
                message=f"Confidence changed: {previous_value:.1f} → {latest_value:.1f}",
                detected_at=detected_at,
            )
        ]

    def _detect_edge_change(
        self,
        ticker: str,
        previous_signal: Dict[str, Any],
        latest_signal: Dict[str, Any],
        detected_at: str,
    ) -> List[SignalChangeEvent]:
        previous_value = self._safe_float(previous_signal.get("edge"))
        latest_value = self._safe_float(latest_signal.get("edge"))

        if previous_value is None or latest_value is None:
            return []

        diff = latest_value - previous_value

        if abs(diff) < self.edge_threshold:
            return []

        change_type = "EDGE_IMPROVED" if diff > 0 else "EDGE_WEAKENED"
        severity = "MEDIUM"

        if abs(diff) >= 4:
            severity = "HIGH"

        return [
            SignalChangeEvent(
                ticker=ticker,
                change_type=change_type,
                field="edge",
                previous_value=previous_value,
                latest_value=latest_value,
                severity=severity,
                message=f"Edge changed: {previous_value:.2f}c → {latest_value:.2f}c",
                detected_at=detected_at,
            )
        ]

    def _detect_fair_value_change(
        self,
        ticker: str,
        previous_signal: Dict[str, Any],
        latest_signal: Dict[str, Any],
        detected_at: str,
    ) -> List[SignalChangeEvent]:
        previous_value = self._safe_float(previous_signal.get("oracle_fair_value"))
        latest_value = self._safe_float(latest_signal.get("oracle_fair_value"))

        if previous_value is None or latest_value is None:
            return []

        diff = latest_value - previous_value

        if abs(diff) < self.fair_value_threshold:
            return []

        change_type = "FAIR_VALUE_INCREASED" if diff > 0 else "FAIR_VALUE_DECREASED"
        severity = "MEDIUM"

        if abs(diff) >= 6:
            severity = "HIGH"

        return [
            SignalChangeEvent(
                ticker=ticker,
                change_type=change_type,
                field="oracle_fair_value",
                previous_value=previous_value,
                latest_value=latest_value,
                severity=severity,
                message=f"Fair value changed: {previous_value:.2f} → {latest_value:.2f}",
                detected_at=detected_at,
            )
        ]

    def _detect_grade_change(
        self,
        ticker: str,
        previous_signal: Dict[str, Any],
        latest_signal: Dict[str, Any],
        detected_at: str,
    ) -> List[SignalChangeEvent]:
        previous_grade = self._safe_grade(previous_signal.get("grade"))
        latest_grade = self._safe_grade(latest_signal.get("grade"))

        if not previous_grade or not latest_grade:
            return []

        if previous_grade == latest_grade:
            return []

        previous_rank = GRADE_RANK.get(previous_grade)
        latest_rank = GRADE_RANK.get(latest_grade)

        if previous_rank is None or latest_rank is None:
            return []

        diff = latest_rank - previous_rank

        change_type = "GRADE_UPGRADED" if diff > 0 else "GRADE_DOWNGRADED"
        severity = "MEDIUM"

        if abs(diff) >= 2:
            severity = "HIGH"

        return [
            SignalChangeEvent(
                ticker=ticker,
                change_type=change_type,
                field="grade",
                previous_value=previous_grade,
                latest_value=latest_grade,
                severity=severity,
                message=f"Grade changed: {previous_grade} → {latest_grade}",
                detected_at=detected_at,
            )
        ]

    def _detect_reason_change(
        self,
        ticker: str,
        previous_signal: Dict[str, Any],
        latest_signal: Dict[str, Any],
        detected_at: str,
    ) -> List[SignalChangeEvent]:
        previous_reason = self._normalize_reason(previous_signal.get("reason"))
        latest_reason = self._normalize_reason(latest_signal.get("reason"))

        if previous_reason == latest_reason:
            return []

        return [
            SignalChangeEvent(
                ticker=ticker,
                change_type="REASON_CHANGED",
                field="reason",
                previous_value=previous_reason,
                latest_value=latest_reason,
                severity="LOW",
                message="Oracle reasoning changed.",
                detected_at=detected_at,
            )
        ]

    def _detect_expected_hold_change(
        self,
        ticker: str,
        previous_signal: Dict[str, Any],
        latest_signal: Dict[str, Any],
        detected_at: str,
    ) -> List[SignalChangeEvent]:
        previous_hold = self._normalize_text(previous_signal.get("expected_hold"))
        latest_hold = self._normalize_text(latest_signal.get("expected_hold"))

        if previous_hold == latest_hold:
            return []

        return [
            SignalChangeEvent(
                ticker=ticker,
                change_type="EXPECTED_HOLD_CHANGED",
                field="expected_hold",
                previous_value=previous_hold,
                latest_value=latest_hold,
                severity="LOW",
                message=f"Expected hold changed: {previous_hold} → {latest_hold}",
                detected_at=detected_at,
            )
        ]

    def _get_ticker(self, signal: Dict[str, Any]) -> str:
        return str(
            signal.get("ticker")
            or signal.get("market_ticker")
            or signal.get("symbol")
            or "UNKNOWN"
        ).strip()

    def _safe_action(self, signal: Dict[str, Any]) -> str:
        raw_action = str(
            signal.get("action")
            or signal.get("decision")
            or signal.get("trade_decision")
            or "PASS"
        ).upper().strip()

        raw_action = raw_action.replace("_", " ")

        if raw_action in ("BUY YES", "YES", "LONG YES"):
            return "BUY YES"

        if raw_action in ("BUY NO", "NO", "LONG NO"):
            return "BUY NO"

        return "PASS"

    def _safe_grade(self, value: Any) -> Optional[str]:
        if value is None:
            return None

        grade = str(value).upper().strip()

        return grade if grade in GRADE_RANK else None

    def _safe_float(self, value: Any) -> Optional[float]:
        try:
            if value is None:
                return None

            if isinstance(value, str):
                value = value.replace("%", "").replace("c", "").replace("¢", "").strip()

            return float(value)

        except (TypeError, ValueError):
            return None

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    def _normalize_reason(self, value: Any) -> Any:
        if value is None:
            return ""

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        return str(value).strip()

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def detect_oracle_signal_changes(
    previous_signal: Optional[Dict[str, Any]],
    latest_signal: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Convenience function for simple imports.

    Example:
        changes = detect_oracle_signal_changes(previous, latest)
    """

    detector = OracleSignalChangeDetector()
    return detector.detect_changes(previous_signal, latest_signal)


if __name__ == "__main__":
    previous = {
        "ticker": "KXBTC",
        "action": "PASS",
        "confidence_score": 71,
        "edge": 2.4,
        "oracle_fair_value": 54.2,
        "grade": "B+",
        "reason": ["Weak edge", "Waiting for confirmation"],
        "expected_hold": "15-45 min",
    }

    latest = {
        "ticker": "KXBTC",
        "action": "BUY YES",
        "confidence_score": 88,
        "edge": 6.8,
        "oracle_fair_value": 61.5,
        "grade": "A+",
        "reason": ["Momentum confirmed", "Edge expanded", "Volume improving"],
        "expected_hold": "30-90 min",
    }

    detector = OracleSignalChangeDetector()
    changes = detector.detect_changes(previous, latest)

    for change in changes:
        print(change)