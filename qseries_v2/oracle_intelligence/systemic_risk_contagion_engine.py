
"""
OI-088 Systemic Risk Contagion Engine

Read-only Oracle Intelligence module.

Purpose:
- Detect cascading influence and systemic contagion across connected markets.
- Consume OI-086 influence graph and OI-087 regime transition graph.
- Score contagion sources, vulnerable sinks, cascade paths, and systemic risk clusters.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque
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
class ContagionMarketScore:
    market: str
    contagion_source_score: float
    vulnerability_score: float
    systemic_importance_score: float
    risk_role: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CascadePath:
    path: List[str]
    cascade_score: float
    path_length: int
    risk_type: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SystemicRiskContagionEngine:
    module = "oi_088_systemic_risk_contagion_engine"

    HIGH_RISK_REGIMES = {"stress", "contagion", "contraction"}
    WATCH_REGIMES = {"distribution", "stabilization"}

    def __init__(self) -> None:
        self.last_report: Dict[str, Any] = {}

    def analyze_contagion(
        self,
        influence_graph: Optional[Dict[str, Any]] = None,
        transition_graph: Optional[Dict[str, Any]] = None,
        min_cascade_score: float = 20.0,
    ) -> Dict[str, Any]:
        influence_graph = influence_graph or {}
        transition_graph = transition_graph or {}

        influence_nodes = self._index_by_market(influence_graph.get("nodes", []))
        transition_nodes = self._index_by_market(transition_graph.get("nodes", []))
        influence_edges = [e for e in influence_graph.get("edges", []) if isinstance(e, dict)]
        transition_edges = [e for e in transition_graph.get("transition_edges", []) if isinstance(e, dict)]

        market_scores = self._score_markets(influence_nodes, transition_nodes, influence_edges, transition_edges)
        cascade_paths = self._find_cascade_paths(influence_edges, transition_edges, transition_nodes, min_cascade_score)
        clusters = self._risk_clusters(cascade_paths)
        headline = self._headline_risk(market_scores, cascade_paths)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_modules": {
                "influence_graph": "oi_086_market_influence_graph_engine",
                "regime_transition_graph": "oi_087_market_regime_transition_graph_engine",
            },
            "market_count": len(market_scores),
            "cascade_path_count": len(cascade_paths),
            "headline_risk": headline,
            "market_scores": [m.to_dict() for m in market_scores],
            "cascade_paths": [p.to_dict() for p in cascade_paths],
            "risk_clusters": clusters,
            "top_contagion_sources": sorted([m.to_dict() for m in market_scores], key=lambda x: x["contagion_source_score"], reverse=True)[:10],
            "top_vulnerable_markets": sorted([m.to_dict() for m in market_scores], key=lambda x: x["vulnerability_score"], reverse=True)[:10],
            "top_systemic_markets": sorted([m.to_dict() for m in market_scores], key=lambda x: x["systemic_importance_score"], reverse=True)[:10],
        }

        self.last_report = report
        return report

    def _index_by_market(self, rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            market = _safe_str(row.get("market")).strip()
            if market:
                out[market] = row
        return out

    def _score_markets(
        self,
        influence_nodes: Dict[str, Dict[str, Any]],
        transition_nodes: Dict[str, Dict[str, Any]],
        influence_edges: List[Dict[str, Any]],
        transition_edges: List[Dict[str, Any]],
    ) -> List[ContagionMarketScore]:
        markets = set(influence_nodes.keys()) | set(transition_nodes.keys())
        outgoing_edge_score = defaultdict(float)
        incoming_edge_score = defaultdict(float)
        outgoing_count = defaultdict(int)
        incoming_count = defaultdict(int)
        risk_transition_count = defaultdict(int)

        for edge in influence_edges:
            source = _safe_str(edge.get("source"))
            target = _safe_str(edge.get("target"))
            score = _safe_float(edge.get("influence_score"))
            if source:
                outgoing_edge_score[source] += score
                outgoing_count[source] += 1
            if target:
                incoming_edge_score[target] += score
                incoming_count[target] += 1

        for edge in transition_edges:
            source = _safe_str(edge.get("source"))
            target = _safe_str(edge.get("target"))
            transition_type = _safe_str(edge.get("transition_type"))
            score = _safe_float(edge.get("transition_score"))
            if transition_type in {"risk_spread", "cycle_rollover"}:
                risk_transition_count[source] += 1
                risk_transition_count[target] += 1
                outgoing_edge_score[source] += score * 0.40
                incoming_edge_score[target] += score * 0.40

        results: List[ContagionMarketScore] = []
        for market in markets:
            inode = influence_nodes.get(market, {})
            tnode = transition_nodes.get(market, {})
            regime = _safe_str(tnode.get("regime"), "neutral")
            role = _safe_str(inode.get("role"), _safe_str(tnode.get("influence_role"), "balanced"))

            outgoing = _safe_float(inode.get("outgoing_influence")) + outgoing_edge_score[market] * 0.35
            incoming = _safe_float(inode.get("incoming_influence")) + incoming_edge_score[market] * 0.35
            bridge = _safe_float(inode.get("bridge_score"))
            transition_pressure = _safe_float(tnode.get("transition_pressure"))
            instability = _safe_float(tnode.get("instability_score"))

            regime_risk = 0.0
            reasons = []
            if regime in self.HIGH_RISK_REGIMES:
                regime_risk = 35.0
                reasons.append(f"Market is in high-risk regime: {regime}.")
            elif regime in self.WATCH_REGIMES:
                regime_risk = 15.0
                reasons.append(f"Market is in watch regime: {regime}.")

            if role in ("dominant_source", "source"):
                reasons.append("Market has source influence behavior.")
            if role in ("bridge", "balanced") and bridge >= 45:
                reasons.append("Market acts as a bridge across influence clusters.")
            if incoming >= 60:
                reasons.append("Market has elevated incoming pressure.")
            if transition_pressure >= 60:
                reasons.append("Market has elevated transition pressure.")

            source_score = _clamp(outgoing * 0.38 + bridge * 0.20 + transition_pressure * 0.22 + regime_risk * 0.20 + risk_transition_count[market] * 5.0)
            vulnerability = _clamp(incoming * 0.34 + instability * 0.30 + transition_pressure * 0.18 + regime_risk * 0.18 + incoming_count[market] * 2.0)
            systemic = _clamp(source_score * 0.35 + vulnerability * 0.35 + bridge * 0.20 + (outgoing_count[market] + incoming_count[market]) * 2.5)

            results.append(
                ContagionMarketScore(
                    market=market,
                    contagion_source_score=round(source_score, 4),
                    vulnerability_score=round(vulnerability, 4),
                    systemic_importance_score=round(systemic, 4),
                    risk_role=self._risk_role(source_score, vulnerability, systemic),
                    reasons=reasons[:8] or ["No elevated contagion signature detected."],
                )
            )

        results.sort(key=lambda m: (m.systemic_importance_score, m.contagion_source_score, m.vulnerability_score), reverse=True)
        return results

    def _risk_role(self, source: float, vulnerability: float, systemic: float) -> str:
        if systemic >= 75 and source >= 60 and vulnerability >= 50:
            return "systemic_contagion_hub"
        if source >= 65:
            return "contagion_source"
        if vulnerability >= 65:
            return "vulnerable_sink"
        if systemic >= 55:
            return "systemic_bridge"
        if vulnerability >= 45 or source >= 45:
            return "risk_watch"
        return "low_contagion_risk"

    def _find_cascade_paths(
        self,
        influence_edges: List[Dict[str, Any]],
        transition_edges: List[Dict[str, Any]],
        transition_nodes: Dict[str, Dict[str, Any]],
        min_cascade_score: float,
    ) -> List[CascadePath]:
        adjacency = defaultdict(list)

        transition_lookup = {}
        for edge in transition_edges:
            key = (_safe_str(edge.get("source")), _safe_str(edge.get("target")))
            transition_lookup[key] = edge

        for edge in influence_edges:
            source = _safe_str(edge.get("source"))
            target = _safe_str(edge.get("target"))
            if not source or not target:
                continue
            adjacency[source].append(edge)

        paths: List[CascadePath] = []
        for start in adjacency.keys():
            q = deque([(start, [start], 0.0, 0)])
            while q:
                current, path, score, depth = q.popleft()
                if depth >= 4:
                    continue

                for edge in adjacency.get(current, []):
                    nxt = _safe_str(edge.get("target"))
                    if not nxt or nxt in path:
                        continue

                    influence_score = _safe_float(edge.get("influence_score"))
                    tedge = transition_lookup.get((current, nxt), {})
                    transition_score = _safe_float(tedge.get("transition_score"))
                    transition_type = _safe_str(tedge.get("transition_type"))
                    target_regime = _safe_str(transition_nodes.get(nxt, {}).get("regime"), "neutral")
                    regime_bonus = 18.0 if target_regime in self.HIGH_RISK_REGIMES else 7.0 if target_regime in self.WATCH_REGIMES else 0.0
                    risk_type_bonus = 12.0 if transition_type in {"risk_spread", "cycle_rollover"} else 0.0

                    new_score = score + influence_score * 0.58 + transition_score * 0.24 + regime_bonus + risk_type_bonus
                    new_path = path + [nxt]

                    normalized_score = _clamp(new_score / max(1, len(new_path) - 1))
                    if len(new_path) >= 3 and normalized_score >= min_cascade_score:
                        risk_type = self._cascade_type(new_path, transition_nodes)
                        paths.append(
                            CascadePath(
                                path=new_path,
                                cascade_score=round(normalized_score, 4),
                                path_length=len(new_path) - 1,
                                risk_type=risk_type,
                                reason=f"Influence path {' -> '.join(new_path)} shows multi-market cascade pressure.",
                            )
                        )

                    q.append((nxt, new_path, new_score, depth + 1))

        paths.sort(key=lambda p: (p.cascade_score, p.path_length), reverse=True)
        return paths[:20]

    def _cascade_type(self, path: List[str], transition_nodes: Dict[str, Dict[str, Any]]) -> str:
        regimes = [_safe_str(transition_nodes.get(m, {}).get("regime"), "neutral") for m in path]
        if "stress" in regimes and "contagion" in regimes:
            return "stress_contagion_chain"
        if regimes.count("contraction") >= 2:
            return "contraction_chain"
        if "distribution" in regimes and "contraction" in regimes:
            return "rollover_chain"
        if "expansion" in regimes and "distribution" in regimes:
            return "late_cycle_rotation"
        return "influence_cascade"

    def _risk_clusters(self, paths: List[CascadePath]) -> List[Dict[str, Any]]:
        cluster_map = defaultdict(lambda: {"paths": 0, "score_sum": 0.0, "markets": set()})

        for path in paths:
            key = path.risk_type
            cluster_map[key]["paths"] += 1
            cluster_map[key]["score_sum"] += path.cascade_score
            cluster_map[key]["markets"].update(path.path)

        clusters = []
        for risk_type, data in cluster_map.items():
            count = data["paths"]
            clusters.append(
                {
                    "risk_type": risk_type,
                    "path_count": count,
                    "avg_cascade_score": round(data["score_sum"] / max(1, count), 4),
                    "markets": sorted(data["markets"]),
                    "market_count": len(data["markets"]),
                }
            )

        clusters.sort(key=lambda c: (c["avg_cascade_score"], c["path_count"]), reverse=True)
        return clusters

    def _headline_risk(self, market_scores: List[ContagionMarketScore], paths: List[CascadePath]) -> Dict[str, Any]:
        if not market_scores:
            return {"level": "none", "score": 0.0, "reason": "No markets available for contagion analysis."}

        top_market = max(market_scores, key=lambda m: m.systemic_importance_score)
        top_path_score = paths[0].cascade_score if paths else 0.0
        headline_score = _clamp(top_market.systemic_importance_score * 0.65 + top_path_score * 0.35)

        if headline_score >= 75:
            level = "high"
        elif headline_score >= 55:
            level = "elevated"
        elif headline_score >= 35:
            level = "watch"
        else:
            level = "low"

        return {
            "level": level,
            "score": round(headline_score, 4),
            "top_market": top_market.market,
            "top_market_role": top_market.risk_role,
            "reason": f"Headline systemic risk is {level}; top systemic market is {top_market.market}.",
        }

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_report": bool(self.last_report),
            "market_count": self.last_report.get("market_count", 0),
            "cascade_path_count": self.last_report.get("cascade_path_count", 0),
            "read_only": True,
        }


systemic_risk_contagion_engine = SystemicRiskContagionEngine()
