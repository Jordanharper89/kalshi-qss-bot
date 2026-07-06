"""
OI-089 Cascade Severity Ranking Engine

Read-only Oracle Intelligence module.

Purpose:
- Rank systemic cascade paths and markets from OI-088.
- Convert raw contagion output into severity tiers, watch priorities, and explanation cards.
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
class CascadeSeverityItem:
    rank: int
    item_type: str
    label: str
    severity_score: float
    severity_tier: str
    urgency: str
    explanation: str
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CascadeSeverityRankingEngine:
    module = "oi_089_cascade_severity_ranking_engine"

    def __init__(self) -> None:
        self.last_ranking: Dict[str, Any] = {}

    def rank_cascades(
        self,
        contagion_report: Optional[Dict[str, Any]] = None,
        max_items: int = 25,
    ) -> Dict[str, Any]:
        contagion_report = contagion_report or {}

        candidates: List[CascadeSeverityItem] = []
        candidates.extend(self._rank_paths(contagion_report.get("cascade_paths", [])))
        candidates.extend(self._rank_markets(contagion_report.get("market_scores", [])))
        candidates.extend(self._rank_clusters(contagion_report.get("risk_clusters", [])))

        candidates.sort(key=lambda x: x.severity_score, reverse=True)
        final = []
        for idx, item in enumerate(candidates[:max_items], start=1):
            item.rank = idx
            final.append(item)

        ranking = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_module": "oi_088_systemic_risk_contagion_engine",
            "item_count": len(final),
            "highest_severity": final[0].to_dict() if final else None,
            "severity_counts": self._severity_counts(final),
            "rankings": [x.to_dict() for x in final],
            "critical_items": [x.to_dict() for x in final if x.severity_tier == "critical"],
            "high_items": [x.to_dict() for x in final if x.severity_tier == "high"],
        }

        self.last_ranking = ranking
        return ranking

    def _rank_paths(self, paths: List[Dict[str, Any]]) -> List[CascadeSeverityItem]:
        out: List[CascadeSeverityItem] = []
        for path in paths:
            if not isinstance(path, dict):
                continue

            markets = path.get("path", [])
            if not isinstance(markets, list):
                markets = []

            cascade_score = _safe_float(path.get("cascade_score"))
            path_length = _safe_float(path.get("path_length"), max(0, len(markets) - 1))
            risk_type = _safe_str(path.get("risk_type"), "influence_cascade")

            risk_bonus = {
                "stress_contagion_chain": 18,
                "contraction_chain": 14,
                "rollover_chain": 12,
                "late_cycle_rotation": 8,
                "influence_cascade": 5,
            }.get(risk_type, 4)

            severity = _clamp(cascade_score * 0.72 + min(path_length, 5) * 3.0 + risk_bonus)
            label = " -> ".join(_safe_str(x) for x in markets) or "unknown_path"

            out.append(
                CascadeSeverityItem(
                    rank=0,
                    item_type="cascade_path",
                    label=label,
                    severity_score=round(severity, 4),
                    severity_tier=self._tier(severity),
                    urgency=self._urgency(severity),
                    explanation=f"Cascade path rated {self._tier(severity)} due to {risk_type} pattern and path score {round(cascade_score, 2)}.",
                    evidence=dict(path),
                )
            )
        return out

    def _rank_markets(self, markets: List[Dict[str, Any]]) -> List[CascadeSeverityItem]:
        out: List[CascadeSeverityItem] = []
        for market in markets:
            if not isinstance(market, dict):
                continue

            name = _safe_str(market.get("market"), "unknown_market")
            source = _safe_float(market.get("contagion_source_score"))
            vulnerability = _safe_float(market.get("vulnerability_score"))
            systemic = _safe_float(market.get("systemic_importance_score"))
            role = _safe_str(market.get("risk_role"), "risk_watch")

            role_bonus = {
                "systemic_contagion_hub": 18,
                "contagion_source": 13,
                "vulnerable_sink": 11,
                "systemic_bridge": 10,
                "risk_watch": 5,
                "low_contagion_risk": 0,
            }.get(role, 3)

            severity = _clamp(systemic * 0.45 + source * 0.25 + vulnerability * 0.25 + role_bonus)

            out.append(
                CascadeSeverityItem(
                    rank=0,
                    item_type="market",
                    label=name,
                    severity_score=round(severity, 4),
                    severity_tier=self._tier(severity),
                    urgency=self._urgency(severity),
                    explanation=f"{name} rated {self._tier(severity)} as {role} with systemic score {round(systemic, 2)}.",
                    evidence=dict(market),
                )
            )
        return out

    def _rank_clusters(self, clusters: List[Dict[str, Any]]) -> List[CascadeSeverityItem]:
        out: List[CascadeSeverityItem] = []
        for cluster in clusters:
            if not isinstance(cluster, dict):
                continue

            risk_type = _safe_str(cluster.get("risk_type"), "risk_cluster")
            avg_score = _safe_float(cluster.get("avg_cascade_score"))
            path_count = _safe_float(cluster.get("path_count"))
            market_count = _safe_float(cluster.get("market_count"))
            markets = cluster.get("markets", [])
            if not isinstance(markets, list):
                markets = []

            severity = _clamp(avg_score * 0.70 + min(path_count, 10) * 2.0 + min(market_count, 10) * 1.5)
            label = f"{risk_type}: " + ", ".join(_safe_str(x) for x in markets[:5])

            out.append(
                CascadeSeverityItem(
                    rank=0,
                    item_type="risk_cluster",
                    label=label,
                    severity_score=round(severity, 4),
                    severity_tier=self._tier(severity),
                    urgency=self._urgency(severity),
                    explanation=f"Risk cluster rated {self._tier(severity)} with {int(path_count)} cascade paths across {int(market_count)} markets.",
                    evidence=dict(cluster),
                )
            )
        return out

    def _tier(self, score: float) -> str:
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "elevated"
        if score >= 30:
            return "watch"
        return "low"

    def _urgency(self, score: float) -> str:
        if score >= 85:
            return "immediate_review"
        if score >= 70:
            return "priority_watch"
        if score >= 50:
            return "active_monitoring"
        if score >= 30:
            return "background_watch"
        return "normal"

    def _severity_counts(self, items: List[CascadeSeverityItem]) -> Dict[str, int]:
        counts = {"critical": 0, "high": 0, "elevated": 0, "watch": 0, "low": 0}
        for item in items:
            counts[item.severity_tier] = counts.get(item.severity_tier, 0) + 1
        return counts

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_ranking": bool(self.last_ranking),
            "item_count": self.last_ranking.get("item_count", 0),
            "read_only": True,
        }


cascade_severity_ranking_engine = CascadeSeverityRankingEngine()
