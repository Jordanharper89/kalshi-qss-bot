
"""
OI-094 Global Market Stability Engine

Read-only Oracle Intelligence module.

Purpose:
- Aggregate Oracle Intelligence risk and recovery outputs into a global market stability index.
- Combine fragility, resilience, contagion, cascade severity, regime transitions, and adaptive decay.
- Produce network-level stability, market-level stability, and risk posture summary.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import math
import time


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(value)))


@dataclass
class MarketStabilityScore:
    market: str
    stability_score: float
    stability_tier: str
    risk_pressure_score: float
    recovery_support_score: float
    persistence_penalty: float
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GlobalMarketStabilityEngine:
    module = "oi_094_global_market_stability_engine"

    def __init__(self) -> None:
        self.last_index: Dict[str, Any] = {}

    def build_stability_index(
        self,
        fragility_report: Optional[Dict[str, Any]] = None,
        resilience_report: Optional[Dict[str, Any]] = None,
        contagion_report: Optional[Dict[str, Any]] = None,
        severity_ranking: Optional[Dict[str, Any]] = None,
        decay_profiles: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        fragility_report = fragility_report or {}
        resilience_report = resilience_report or {}
        contagion_report = contagion_report or {}
        severity_ranking = severity_ranking or {}
        decay_profiles = decay_profiles or {}

        fragility = self._index(fragility_report.get("scores", []), "market")
        resilience = self._index(resilience_report.get("scores", []), "market")
        contagion = self._index(contagion_report.get("market_scores", []), "market")
        decay = self._index(decay_profiles.get("profiles", []), "market")
        severity = self._severity_by_market(severity_ranking.get("rankings", []))

        markets = set(fragility.keys()) | set(resilience.keys()) | set(contagion.keys()) | set(decay.keys()) | set(severity.keys())

        scores: List[MarketStabilityScore] = []
        for market in markets:
            f = fragility.get(market, {})
            r = resilience.get(market, {})
            c = contagion.get(market, {})
            d = decay.get(market, {})

            fragility_score = _safe_float(f.get("fragility_score"))
            resilience_score = _safe_float(r.get("resilience_score"))
            systemic = _safe_float(c.get("systemic_importance_score"))
            vulnerability = _safe_float(c.get("vulnerability_score"))
            source = _safe_float(c.get("contagion_source_score"))
            severity_score = _safe_float(severity.get(market))
            persistence = _safe_float(d.get("persistence_score"))
            decay_rate = _safe_float(d.get("decay_rate"), 0.45)

            risk_pressure = _clamp(
                fragility_score * 0.32
                + systemic * 0.22
                + vulnerability * 0.18
                + source * 0.10
                + severity_score * 0.18
            )
            recovery_support = _clamp(resilience_score)
            persistence_penalty = _clamp(persistence * 0.70 + max(0.0, 0.50 - decay_rate) * 60.0)
            stability = _clamp(100 - risk_pressure * 0.58 + recovery_support * 0.34 - persistence_penalty * 0.22)

            scores.append(
                MarketStabilityScore(
                    market=market,
                    stability_score=round(stability, 4),
                    stability_tier=self._tier(stability),
                    risk_pressure_score=round(risk_pressure, 4),
                    recovery_support_score=round(recovery_support, 4),
                    persistence_penalty=round(persistence_penalty, 4),
                    reasons=self._reasons(stability, risk_pressure, recovery_support, persistence_penalty),
                )
            )

        scores.sort(key=lambda x: x.stability_score, reverse=True)

        global_score = self._global_score(scores)
        index = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "market_count": len(scores),
            "global_stability_score": global_score,
            "global_stability_tier": self._tier(global_score),
            "risk_posture": self._posture(global_score),
            "scores": [s.to_dict() for s in scores],
            "most_stable_markets": [s.to_dict() for s in scores[:10]],
            "least_stable_markets": [s.to_dict() for s in sorted(scores, key=lambda x: x.stability_score)[:10]],
            "stability_tier_counts": self._counts(scores),
        }

        self.last_index = index
        return index

    def _index(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            if isinstance(row, dict):
                value = _safe_str(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _severity_by_market(self, rankings: List[Dict[str, Any]]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for row in rankings:
            if not isinstance(row, dict):
                continue
            if row.get("item_type") != "market":
                continue
            market = _safe_str(row.get("label")).strip()
            if market:
                out[market] = max(out.get(market, 0.0), _safe_float(row.get("severity_score")))
        return out

    def _global_score(self, scores: List[MarketStabilityScore]) -> float:
        if not scores:
            return 0.0
        avg = sum(s.stability_score for s in scores) / len(scores)
        weak_penalty = len([s for s in scores if s.stability_score < 45]) * 2.0
        systemic_floor = min(s.stability_score for s in scores)
        final = avg * 0.72 + systemic_floor * 0.18 - weak_penalty
        return round(_clamp(final), 4)

    def _tier(self, score: float) -> str:
        if score >= 80:
            return "stable"
        if score >= 65:
            return "constructive"
        if score >= 45:
            return "mixed"
        if score >= 25:
            return "unstable"
        return "critical"

    def _posture(self, score: float) -> str:
        if score >= 80:
            return "normal_risk"
        if score >= 65:
            return "selective_risk"
        if score >= 45:
            return "heightened_monitoring"
        if score >= 25:
            return "defensive_monitoring"
        return "systemic_alert"

    def _counts(self, scores: List[MarketStabilityScore]) -> Dict[str, int]:
        counts = {"stable": 0, "constructive": 0, "mixed": 0, "unstable": 0, "critical": 0}
        for score in scores:
            counts[score.stability_tier] = counts.get(score.stability_tier, 0) + 1
        return counts

    def _reasons(self, stability: float, risk: float, recovery: float, persistence: float) -> List[str]:
        reasons = [f"Stability score is {round(stability, 2)}."]
        if risk >= 65:
            reasons.append("Risk pressure is elevated.")
        if recovery >= 65:
            reasons.append("Recovery support is strong.")
        if persistence >= 65:
            reasons.append("Persistent influence pressure reduces stability.")
        if stability < 45:
            reasons.append("Market belongs on defensive monitoring.")
        elif stability >= 65:
            reasons.append("Market has constructive stability support.")
        return reasons[:8]

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_index": bool(self.last_index),
            "market_count": self.last_index.get("market_count", 0),
            "global_stability_score": self.last_index.get("global_stability_score", 0),
            "read_only": True,
        }


global_market_stability_engine = GlobalMarketStabilityEngine()
