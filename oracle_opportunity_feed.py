"""
Oracle Opportunity Feed

KQ-018.5

Purpose:
- Build a ranked Top Opportunities feed from Oracle watchlist/research state.
- Surface strongest live edges.
- Does NOT execute trades.
- Does NOT send Telegram alerts directly.
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


@dataclass
class OracleOpportunity:
    rank: int
    ticker: str
    title: str
    action: str
    grade: str
    confidence_score: float
    edge: float
    oracle_fair_value: float
    yes_price: float
    no_price: float
    opportunity_score: float
    reason: str
    updated_at: str
    raw: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleOpportunityFeed:
    def __init__(
        self,
        min_grade: str = "B+",
        min_edge: float = 2.0,
        min_confidence: float = 60.0,
        max_items: int = 10,
    ):
        self.min_grade = min_grade.upper().strip()
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        self.max_items = max_items

    def build_feed(self, watched_markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        opportunities: List[OracleOpportunity] = []

        for market in watched_markets:
            signal = self._extract_signal(market)

            if not signal:
                continue

            opportunity = self._build_opportunity(market, signal)

            if not opportunity:
                continue

            if not self._passes_filters(opportunity):
                continue

            opportunities.append(opportunity)

        opportunities.sort(key=lambda item: item.opportunity_score, reverse=True)

        ranked = []
        for index, opportunity in enumerate(opportunities[: self.max_items], start=1):
            opportunity.rank = index
            ranked.append(opportunity.to_dict())

        return ranked

    def _build_opportunity(
        self,
        market: Dict[str, Any],
        signal: Dict[str, Any],
    ) -> Optional[OracleOpportunity]:
        ticker = self._get_ticker(market, signal)

        if not ticker:
            return None

        action = self._safe_action(signal)
        grade = self._safe_grade(signal.get("grade"))
        confidence = self._safe_float(signal.get("confidence_score"))
        edge = self._safe_float(signal.get("edge"))
        fair_value = self._safe_float(
            signal.get("oracle_fair_value")
            or signal.get("fair_value")
        )

        yes_price = self._safe_float(
            signal.get("yes_price")
            or market.get("yes_price")
            or market.get("last_price")
        )

        no_price = self._safe_float(
            signal.get("no_price")
            or market.get("no_price")
        )

        score = self._score_opportunity(
            action=action,
            grade=grade,
            confidence=confidence,
            edge=edge,
        )

        return OracleOpportunity(
            rank=0,
            ticker=ticker,
            title=self._get_title(market, signal),
            action=action,
            grade=grade,
            confidence_score=confidence,
            edge=edge,
            oracle_fair_value=fair_value,
            yes_price=yes_price,
            no_price=no_price,
            opportunity_score=round(score, 2),
            reason=self._build_reason(action, grade, confidence, edge),
            updated_at=self._get_updated_at(market, signal),
            raw={
                "market": market,
                "signal": signal,
            },
        )

    def _passes_filters(self, opportunity: OracleOpportunity) -> bool:
        if opportunity.action == "PASS":
            return False

        if opportunity.edge < self.min_edge:
            return False

        if opportunity.confidence_score < self.min_confidence:
            return False

        min_rank = GRADE_RANK.get(self.min_grade, 0)
        grade_rank = GRADE_RANK.get(opportunity.grade, 0)

        if grade_rank < min_rank:
            return False

        return True

    def _score_opportunity(
        self,
        action: str,
        grade: str,
        confidence: float,
        edge: float,
    ) -> float:
        score = 0.0

        if action in ("BUY YES", "BUY NO"):
            score += 25.0

        score += min(edge * 5.0, 35.0)
        score += min(confidence / 100.0 * 25.0, 25.0)
        score += min(GRADE_RANK.get(grade, 0) * 2.0, 18.0)

        return max(0.0, min(100.0, score))

    def _build_reason(
        self,
        action: str,
        grade: str,
        confidence: float,
        edge: float,
    ) -> str:
        return (
            f"{action} | Grade {grade} | "
            f"Confidence {confidence:.0f} | Edge {edge:.2f}c"
        )

    def _extract_signal(self, market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        signal = (
            market.get("latest_signal")
            or market.get("signal")
            or market.get("research")
            or market
        )

        return signal if isinstance(signal, dict) else None

    def _get_ticker(
        self,
        market: Dict[str, Any],
        signal: Dict[str, Any],
    ) -> str:
        return str(
            signal.get("ticker")
            or market.get("ticker")
            or market.get("market_ticker")
            or signal.get("market_ticker")
            or ""
        ).strip()

    def _get_title(
        self,
        market: Dict[str, Any],
        signal: Dict[str, Any],
    ) -> str:
        return str(
            signal.get("title")
            or market.get("title")
            or market.get("name")
            or ""
        ).strip()

    def _safe_action(self, signal: Dict[str, Any]) -> str:
        raw = str(
            signal.get("action")
            or signal.get("decision")
            or signal.get("trade_decision")
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

    def _safe_float(self, value: Any) -> float:
        try:
            if value is None:
                return 0.0

            if isinstance(value, str):
                value = (
                    value.replace("%", "")
                    .replace("c", "")
                    .replace("¢", "")
                    .replace(",", "")
                    .strip()
                )

            return float(value)

        except (TypeError, ValueError):
            return 0.0

    def _get_updated_at(
        self,
        market: Dict[str, Any],
        signal: Dict[str, Any],
    ) -> str:
        return str(
            signal.get("last_checked_at")
            or market.get("last_checked_at")
            or signal.get("updated_at")
            or market.get("updated_at")
            or self._utc_now()
        )

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def build_oracle_opportunity_feed(
    watched_markets: List[Dict[str, Any]],
    min_grade: str = "B+",
    min_edge: float = 2.0,
    min_confidence: float = 60.0,
    max_items: int = 10,
) -> List[Dict[str, Any]]:
    feed = OracleOpportunityFeed(
        min_grade=min_grade,
        min_edge=min_edge,
        min_confidence=min_confidence,
        max_items=max_items,
    )

    return feed.build_feed(watched_markets)