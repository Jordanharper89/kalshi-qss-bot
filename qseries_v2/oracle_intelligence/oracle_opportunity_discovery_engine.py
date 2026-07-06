"""
OI-057 Oracle Opportunity Discovery Engine

Purpose:
- Scan live market snapshots.
- Score and rank markets that deserve deeper Oracle analysis.
- Feed high-priority candidates into synthesis / consensus / report layers.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import math


class OracleOpportunityDiscoveryEngine:
    module_name = "oi_057_oracle_opportunity_discovery_engine"

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "purpose": "rank_live_market_opportunities",
        }

    def discover(
        self,
        markets: List[Dict[str, Any]],
        limit: int = 25,
        min_score: float = 0.0,
    ) -> Dict[str, Any]:
        scored = []

        for market in markets or []:
            item = self.score_market(market)
            if item["opportunity_score"] >= min_score:
                scored.append(item)

        scored.sort(
            key=lambda x: (
                x["opportunity_score"],
                x["priority_weight"],
                x["market"].get("volume", 0) or 0,
            ),
            reverse=True,
        )

        for idx, item in enumerate(scored, start=1):
            item["rank"] = idx

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "markets_scanned": len(markets or []),
            "opportunities_found": len(scored),
            "top_opportunities": scored[:limit],
        }

    def score_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        components = {
            "volume_acceleration": self._volume_acceleration_score(market),
            "liquidity_quality": self._liquidity_score(market),
            "spread_quality": self._spread_score(market),
            "momentum": self._momentum_score(market),
            "volatility": self._volatility_score(market),
            "expiration_proximity": self._expiration_score(market),
            "price_zone": self._price_zone_score(market),
            "information_density": self._information_density_score(market),
            "historical_context": self._historical_context_score(market),
            "cross_market_signal": self._cross_market_score(market),
        }

        weights = {
            "volume_acceleration": 0.16,
            "liquidity_quality": 0.13,
            "spread_quality": 0.12,
            "momentum": 0.13,
            "volatility": 0.10,
            "expiration_proximity": 0.10,
            "price_zone": 0.08,
            "information_density": 0.08,
            "historical_context": 0.06,
            "cross_market_signal": 0.04,
        }

        raw = sum(components[k] * weights[k] for k in components)
        opportunity_score = round(max(0.0, min(100.0, raw)), 2)

        reasons = self._reason_codes(components, market)
        priority = self._priority(opportunity_score)
        depth = self._analysis_depth(opportunity_score, reasons)

        return {
            "status": "ok",
            "read_only": True,
            "ticker": market.get("ticker") or market.get("market_ticker") or market.get("id"),
            "opportunity_score": opportunity_score,
            "priority": priority,
            "priority_weight": self._priority_weight(priority),
            "suggested_analysis_depth": depth,
            "reason_codes": reasons,
            "components": {k: round(v, 2) for k, v in components.items()},
            "research_status": "queued_for_analysis" if opportunity_score >= 70 else "watch_only",
            "market": market,
        }

    def _volume_acceleration_score(self, m: Dict[str, Any]) -> float:
        volume = self._num(m.get("volume"))
        prev_volume = self._num(m.get("previous_volume") or m.get("volume_5m_ago"))
        volume_delta_pct = self._num(m.get("volume_delta_pct"))

        if volume_delta_pct is not None:
            return self._scale(volume_delta_pct, 0, 200)

        if volume is not None and prev_volume not in {None, 0}:
            return self._scale(((volume - prev_volume) / max(prev_volume, 1)) * 100, 0, 200)

        if volume is not None:
            return self._scale(volume, 0, 50000)

        return 35.0

    def _liquidity_score(self, m: Dict[str, Any]) -> float:
        liquidity = self._num(m.get("liquidity") or m.get("open_interest"))

        if liquidity is None:
            return 40.0

        return self._scale(liquidity, 500, 50000)

    def _spread_score(self, m: Dict[str, Any]) -> float:
        spread = self._num(m.get("spread"))

        if spread is None:
            yes_bid = self._num(m.get("yes_bid"))
            yes_ask = self._num(m.get("yes_ask"))
            if yes_bid is not None and yes_ask is not None:
                spread = abs(yes_ask - yes_bid)

        if spread is None:
            return 40.0

        if spread <= 1:
            return 100.0
        if spread <= 2:
            return 90.0
        if spread <= 5:
            return 70.0
        if spread <= 10:
            return 45.0
        return 20.0

    def _momentum_score(self, m: Dict[str, Any]) -> float:
        momentum = self._num(m.get("momentum"))
        price_delta = self._num(m.get("price_delta_pct") or m.get("change_pct"))

        value = momentum if momentum is not None else price_delta

        if value is None:
            return 40.0

        return min(100.0, abs(value) * 10.0)

    def _volatility_score(self, m: Dict[str, Any]) -> float:
        volatility = self._num(m.get("volatility"))

        if volatility is None:
            return 45.0

        if volatility < 2:
            return 35.0
        if volatility <= 8:
            return 85.0
        if volatility <= 15:
            return 70.0
        return 45.0

    def _expiration_score(self, m: Dict[str, Any]) -> float:
        minutes = self._num(m.get("time_to_expiration_minutes") or m.get("minutes_to_expiration"))

        if minutes is None:
            return 45.0

        if minutes <= 5:
            return 50.0
        if minutes <= 60:
            return 95.0
        if minutes <= 240:
            return 80.0
        if minutes <= 1440:
            return 55.0
        return 30.0

    def _price_zone_score(self, m: Dict[str, Any]) -> float:
        price = self._num(
            m.get("price")
            or m.get("yes_price")
            or m.get("implied_probability")
        )

        if price is None:
            return 45.0

        if 40 <= price <= 60:
            return 95.0
        if 25 <= price < 40 or 60 < price <= 75:
            return 75.0
        if 15 <= price < 25 or 75 < price <= 85:
            return 55.0
        return 35.0

    def _information_density_score(self, m: Dict[str, Any]) -> float:
        keys = [
            "category",
            "regime",
            "pattern_name",
            "strategy",
            "momentum",
            "volatility",
            "volume",
            "liquidity",
            "spread",
            "time_to_expiration_minutes",
            "correlation_signal",
            "historical_similarity_count",
        ]
        present = sum(1 for k in keys if m.get(k) is not None)
        return self._scale(present, 0, len(keys))

    def _historical_context_score(self, m: Dict[str, Any]) -> float:
        count = self._num(m.get("historical_similarity_count") or m.get("analog_count"))

        if count is None:
            return 35.0

        return self._scale(count, 0, 50)

    def _cross_market_score(self, m: Dict[str, Any]) -> float:
        value = self._num(m.get("cross_market_divergence") or m.get("correlation_signal"))

        if value is None:
            return 35.0

        return min(100.0, abs(value) * 100 if abs(value) <= 1 else abs(value))

    def _reason_codes(self, components: Dict[str, float], market: Dict[str, Any]) -> List[str]:
        reasons = []

        if components["volume_acceleration"] >= 75:
            reasons.append("rapid_volume_acceleration")

        if components["spread_quality"] >= 80:
            reasons.append("tradable_tight_spread")

        if components["momentum"] >= 70:
            reasons.append("strong_price_momentum")

        if components["expiration_proximity"] >= 80:
            reasons.append("near_term_resolution_window")

        if components["historical_context"] >= 70:
            reasons.append("historical_analog_support")

        if components["cross_market_signal"] >= 70:
            reasons.append("cross_market_divergence_detected")

        if components["price_zone"] >= 85:
            reasons.append("high_information_price_zone")

        if not reasons:
            reasons.append("low_signal_watch_only")

        return reasons

    def _priority(self, score: float) -> str:
        if score >= 90:
            return "critical"
        if score >= 80:
            return "high"
        if score >= 70:
            return "medium"
        if score >= 55:
            return "watch"
        return "low"

    def _priority_weight(self, priority: str) -> int:
        return {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "watch": 2,
            "low": 1,
        }.get(priority, 0)

    def _analysis_depth(self, score: float, reasons: List[str]) -> str:
        if score >= 85 or "cross_market_divergence_detected" in reasons:
            return "full_oracle_consensus"
        if score >= 70:
            return "standard_oracle_research"
        if score >= 55:
            return "light_watch_report"
        return "no_deep_analysis"

    def _scale(self, value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.0

        return max(0.0, min(100.0, ((float(value) - low) / (high - low)) * 100.0))

    def _num(self, value: Any) -> Optional[float]:
        try:
            v = float(value)
            if math.isfinite(v):
                return v
            return None
        except Exception:
            return None


oracle_opportunity_discovery_engine = OracleOpportunityDiscoveryEngine()
