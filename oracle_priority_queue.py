"""
Oracle Priority Queue Scheduler

KQ-018.2

Purpose:
- Score watched Oracle markets by importance.
- Sort markets so Oracle refreshes the best opportunities first.
- Does NOT execute trades.
- Does NOT send notifications.
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


ACTION_SCORE = {
    "PASS": 0,
    "BUY YES": 18,
    "BUY NO": 18,
}


@dataclass
class OracleQueueJob:
    ticker: str
    priority_score: float
    action: str
    grade: str
    edge: float
    confidence_score: float
    reason: str
    raw_market: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OraclePriorityQueue:
    """
    Turns watched markets into sorted refresh jobs.

    Higher score = scanned first.
    """

    def __init__(
        self,
        stale_boost_minutes: int = 15,
        max_stale_boost: float = 20.0,
    ):
        self.stale_boost_minutes = stale_boost_minutes
        self.max_stale_boost = max_stale_boost

    def build_queue(self, watched_markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        jobs: List[OracleQueueJob] = []

        for market in watched_markets:
            job = self._build_job(market)
            if job:
                jobs.append(job)

        jobs.sort(key=lambda job: job.priority_score, reverse=True)

        return [job.to_dict() for job in jobs]

    def _build_job(self, market: Dict[str, Any]) -> Optional[OracleQueueJob]:
        ticker = self._get_ticker(market)

        if not ticker:
            return None

        action = self._safe_action(market)
        grade = self._safe_grade(market.get("grade"))
        edge = self._safe_float(market.get("edge"), default=0.0)
        confidence = self._safe_float(market.get("confidence_score"), default=0.0)

        priority_score = self._score_market(
            market=market,
            action=action,
            grade=grade,
            edge=edge,
            confidence=confidence,
        )

        reason = self._build_reason(
            market=market,
            action=action,
            grade=grade,
            edge=edge,
            confidence=confidence,
            priority_score=priority_score,
        )

        return OracleQueueJob(
            ticker=ticker,
            priority_score=round(priority_score, 2),
            action=action,
            grade=grade,
            edge=edge,
            confidence_score=confidence,
            reason=reason,
            raw_market=market,
        )

    def _score_market(
        self,
        market: Dict[str, Any],
        action: str,
        grade: str,
        edge: float,
        confidence: float,
    ) -> float:
        score = 0.0

        score += self._score_edge(edge)
        score += self._score_confidence(confidence)
        score += self._score_grade(grade)
        score += self._score_action(action)
        score += self._score_volume(market)
        score += self._score_liquidity(market)
        score += self._score_expiration(market)
        score += self._score_recent_signal_change(market)
        score += self._score_staleness(market)

        return max(0.0, min(100.0, score))

    def _score_edge(self, edge: float) -> float:
        if edge <= 0:
            return 0.0

        return min(edge * 4.0, 28.0)

    def _score_confidence(self, confidence: float) -> float:
        if confidence <= 0:
            return 0.0

        return min(confidence / 100.0 * 22.0, 22.0)

    def _score_grade(self, grade: str) -> float:
        rank = GRADE_RANK.get(grade, 0)
        return min(rank * 2.5, 22.5)

    def _score_action(self, action: str) -> float:
        return ACTION_SCORE.get(action, 0)

    def _score_volume(self, market: Dict[str, Any]) -> float:
        volume = self._safe_float(
            market.get("volume")
            or market.get("volume_24h")
            or market.get("daily_volume"),
            default=0.0,
        )

        if volume <= 0:
            return 0.0

        if volume >= 100000:
            return 8.0
        if volume >= 50000:
            return 6.0
        if volume >= 10000:
            return 4.0
        if volume >= 1000:
            return 2.0

        return 1.0

    def _score_liquidity(self, market: Dict[str, Any]) -> float:
        liquidity = self._safe_float(
            market.get("liquidity")
            or market.get("open_interest")
            or market.get("dollar_liquidity"),
            default=0.0,
        )

        if liquidity <= 0:
            return 0.0

        if liquidity >= 100000:
            return 8.0
        if liquidity >= 50000:
            return 6.0
        if liquidity >= 10000:
            return 4.0
        if liquidity >= 1000:
            return 2.0

        return 1.0

    def _score_expiration(self, market: Dict[str, Any]) -> float:
        expiration = (
            market.get("expiration_time")
            or market.get("close_time")
            or market.get("end_time")
        )

        expiration_dt = self._parse_datetime(expiration)

        if not expiration_dt:
            return 0.0

        now = datetime.now(timezone.utc)
        minutes_left = (expiration_dt - now).total_seconds() / 60

        if minutes_left <= 0:
            return 0.0

        if minutes_left <= 30:
            return 10.0
        if minutes_left <= 120:
            return 8.0
        if minutes_left <= 360:
            return 5.0
        if minutes_left <= 1440:
            return 3.0

        return 1.0

    def _score_recent_signal_change(self, market: Dict[str, Any]) -> float:
        change_severity = str(
            market.get("last_change_severity")
            or market.get("signal_change_severity")
            or ""
        ).upper().strip()

        if change_severity == "CRITICAL":
            return 12.0
        if change_severity == "HIGH":
            return 9.0
        if change_severity == "MEDIUM":
            return 5.0
        if change_severity == "LOW":
            return 2.0

        return 0.0

    def _score_staleness(self, market: Dict[str, Any]) -> float:
        last_checked = (
            market.get("last_checked_at")
            or market.get("last_researched_at")
            or market.get("updated_at")
        )

        last_checked_dt = self._parse_datetime(last_checked)

        if not last_checked_dt:
            return self.max_stale_boost

        now = datetime.now(timezone.utc)
        minutes_old = max(0.0, (now - last_checked_dt).total_seconds() / 60)

        if minutes_old <= self.stale_boost_minutes:
            return 0.0

        boost = minutes_old / self.stale_boost_minutes
        return min(boost, self.max_stale_boost)

    def _build_reason(
        self,
        market: Dict[str, Any],
        action: str,
        grade: str,
        edge: float,
        confidence: float,
        priority_score: float,
    ) -> str:
        reasons = []

        if action in ("BUY YES", "BUY NO"):
            reasons.append(f"active action: {action}")

        if edge >= 5:
            reasons.append(f"strong edge: {edge:.2f}c")
        elif edge > 0:
            reasons.append(f"positive edge: {edge:.2f}c")

        if confidence >= 80:
            reasons.append(f"high confidence: {confidence:.0f}")

        if grade in ("A-", "A", "A+"):
            reasons.append(f"strong grade: {grade}")

        severity = str(
            market.get("last_change_severity")
            or market.get("signal_change_severity")
            or ""
        ).upper().strip()

        if severity:
            reasons.append(f"recent signal change: {severity}")

        if not reasons:
            reasons.append("stale or low-priority market")

        return f"Priority {priority_score:.2f}: " + "; ".join(reasons)

    def _get_ticker(self, market: Dict[str, Any]) -> str:
        return str(
            market.get("ticker")
            or market.get("market_ticker")
            or market.get("symbol")
            or ""
        ).strip()

    def _safe_action(self, market: Dict[str, Any]) -> str:
        raw = str(
            market.get("action")
            or market.get("decision")
            or market.get("trade_decision")
            or "PASS"
        ).upper().strip()

        raw = raw.replace("_", " ")

        if raw in ("BUY YES", "YES", "LONG YES"):
            return "BUY YES"

        if raw in ("BUY NO", "NO", "LONG NO"):
            return "BUY NO"

        return "PASS"

    def _safe_grade(self, value: Any) -> str:
        if value is None:
            return "F"

        grade = str(value).upper().strip()
        return grade if grade in GRADE_RANK else "F"

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default

            if isinstance(value, str):
                value = value.replace("%", "").replace("c", "").replace("¢", "").strip()

            return float(value)

        except (TypeError, ValueError):
            return default

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if not value:
            return None

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        if not isinstance(value, str):
            return None

        cleaned = value.strip()

        try:
            if cleaned.endswith("Z"):
                cleaned = cleaned.replace("Z", "+00:00")

            parsed = datetime.fromisoformat(cleaned)

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)

            return parsed

        except ValueError:
            return None


def build_oracle_priority_queue(
    watched_markets: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    queue = OraclePriorityQueue()
    return queue.build_queue(watched_markets)


if __name__ == "__main__":
    sample_markets = [
        {
            "ticker": "KXBTC",
            "action": "BUY YES",
            "grade": "A+",
            "edge": 6.8,
            "confidence_score": 88,
            "volume": 120000,
            "liquidity": 55000,
            "last_change_severity": "HIGH",
            "last_checked_at": "2026-06-27T04:00:00+00:00",
        },
        {
            "ticker": "KXETH",
            "action": "PASS",
            "grade": "B",
            "edge": 1.4,
            "confidence_score": 61,
            "volume": 8500,
            "liquidity": 9000,
            "last_checked_at": "2026-06-27T01:00:00+00:00",
        },
        {
            "ticker": "KXFED",
            "action": "BUY NO",
            "grade": "A-",
            "edge": 4.9,
            "confidence_score": 79,
            "volume": 25000,
            "liquidity": 30000,
            "last_change_severity": "MEDIUM",
            "last_checked_at": "2026-06-27T03:30:00+00:00",
        },
    ]

    queue = build_oracle_priority_queue(sample_markets)

    for job in queue:
        print(job["ticker"], job["priority_score"], job["reason"])