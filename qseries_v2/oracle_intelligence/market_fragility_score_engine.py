"""
OI-091 Market Fragility Score Engine

Read-only Oracle Intelligence module.

Purpose:
- Score market fragility using influence, regime transition, contagion, and cascade severity outputs.
- Fragility means how likely a market is to move sharply when new information or a shock arrives.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from collections import defaultdict
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
class MarketFragilityScore:
    market: str
    fragility_score: float
    fragility_tier: str
    primary_driver: str
    components: Dict[str, float]
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketFragilityScoreEngine:
    module = "oi_091_market_fragility_score_engine"

    def __init__(self) -> None:
        self.last_scores: Dict[str, Any] = {}

    def score_fragility(
        self,
        influence_graph: Optional[Dict[str, Any]] = None,
        transition_graph: Optional[Dict[str, Any]] = None,
        contagion_report: Optional[Dict[str, Any]] = None,
        severity_ranking: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        influence_graph = influence_graph or {}
        transition_graph = transition_graph or {}
        contagion_report = contagion_report or {}
        severity_ranking = severity_ranking or {}

        influence_nodes = self._index(influence_graph.get("nodes", []), "market")
        transition_nodes = self._index(transition_graph.get("nodes", []), "market")
        contagion_markets = self._index(contagion_report.get("market_scores", []), "market")
        severity_by_market = self._severity_by_market(severity_ranking.get("rankings", []))

        markets = set(influence_nodes.keys()) | set(transition_nodes.keys()) | set(contagion_markets.keys()) | set(severity_by_market.keys())

        scores: List[MarketFragilityScore] = []
        for market in markets:
            inode = influence_nodes.get(market, {})
            tnode = transition_nodes.get(market, {})
            cnode = contagion_markets.get(market, {})
            severity = severity_by_market.get(market, 0.0)

            influence_component = _clamp(
                abs(_safe_float(inode.get("net_influence"))) * 0.45
                + _safe_float(inode.get("bridge_score")) * 0.35
                + (_safe_float(inode.get("incoming_influence")) + _safe_float(inode.get("outgoing_influence"))) * 0.10
            )
            regime_component = _clamp(
                _safe_float(tnode.get("transition_pressure")) * 0.52
                + _safe_float(tnode.get("instability_score")) * 0.48
            )
            contagion_component = _clamp(
                _safe_float(cnode.get("vulnerability_score")) * 0.36
                + _safe_float(cnode.get("contagion_source_score")) * 0.28
                + _safe_float(cnode.get("systemic_importance_score")) * 0.36
            )
            severity_component = _clamp(severity)

            final_score = _clamp(
                influence_component * 0.24
                + regime_component * 0.26
                + contagion_component * 0.30
                + severity_component * 0.20
            )

            components = {
                "influence_component": round(influence_component, 4),
                "regime_component": round(regime_component, 4),
                "contagion_component": round(contagion_component, 4),
                "severity_component": round(severity_component, 4),
            }

            primary_driver = max(components.items(), key=lambda kv: kv[1])[0]
            reasons = self._reasons(inode, tnode, cnode, components, primary_driver)

            scores.append(
                MarketFragilityScore(
                    market=market,
                    fragility_score=round(final_score, 4),
                    fragility_tier=self._tier(final_score),
                    primary_driver=primary_driver,
                    components=components,
                    reasons=reasons,
                )
            )

        scores.sort(key=lambda x: x.fragility_score, reverse=True)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_modules": [
                "oi_086_market_influence_graph_engine",
                "oi_087_market_regime_transition_graph_engine",
                "oi_088_systemic_risk_contagion_engine",
                "oi_089_cascade_severity_ranking_engine",
            ],
            "market_count": len(scores),
            "scores": [x.to_dict() for x in scores],
            "top_fragile_markets": [x.to_dict() for x in scores[:10]],
            "fragility_counts": self._counts(scores),
            "highest_fragility": scores[0].to_dict() if scores else None,
        }

        self.last_scores = report
        return report

    def _index(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = _safe_str(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _severity_by_market(self, rankings: List[Dict[str, Any]]) -> Dict[str, float]:
        out = defaultdict(float)
        for row in rankings:
            if not isinstance(row, dict):
                continue
            if row.get("item_type") != "market":
                continue
            market = _safe_str(row.get("label")).strip()
            if market:
                out[market] = max(out[market], _safe_float(row.get("severity_score")))
        return dict(out)

    def _tier(self, score: float) -> str:
        if score >= 80:
            return "extreme"
        if score >= 65:
            return "high"
        if score >= 45:
            return "elevated"
        if score >= 25:
            return "moderate"
        return "low"

    def _counts(self, scores: List[MarketFragilityScore]) -> Dict[str, int]:
        counts = {"extreme": 0, "high": 0, "elevated": 0, "moderate": 0, "low": 0}
        for score in scores:
            counts[score.fragility_tier] = counts.get(score.fragility_tier, 0) + 1
        return counts

    def _reasons(
        self,
        inode: Dict[str, Any],
        tnode: Dict[str, Any],
        cnode: Dict[str, Any],
        components: Dict[str, float],
        primary_driver: str,
    ) -> List[str]:
        reasons = [f"Primary fragility driver is {primary_driver}."]

        role = _safe_str(inode.get("role"))
        regime = _safe_str(tnode.get("regime"))
        risk_role = _safe_str(cnode.get("risk_role"))

        if role:
            reasons.append(f"Influence role: {role}.")
        if regime:
            reasons.append(f"Regime state: {regime}.")
        if risk_role:
            reasons.append(f"Contagion role: {risk_role}.")
        if components.get("regime_component", 0) >= 65:
            reasons.append("Regime transition pressure is elevated.")
        if components.get("contagion_component", 0) >= 65:
            reasons.append("Contagion vulnerability is elevated.")
        if components.get("influence_component", 0) >= 65:
            reasons.append("Influence imbalance or bridge pressure is elevated.")

        return reasons[:8]

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_scores": bool(self.last_scores),
            "market_count": self.last_scores.get("market_count", 0),
            "read_only": True,
        }


market_fragility_score_engine = MarketFragilityScoreEngine()
