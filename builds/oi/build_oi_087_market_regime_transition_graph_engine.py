import os
from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "market_regime_transition_graph_engine.py"
TEST = ROOT / "test_oi_087_market_regime_transition_graph_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r"""
\"\"\"
OI-087 Market Regime Transition Graph Engine

Read-only Oracle Intelligence module.

Purpose:
- Analyze regime-state transitions using the OI-086 influence graph.
- Convert influence nodes and edges into market regime labels:
  accumulation, expansion, distribution, contraction, stress, contagion, stabilization.
- Detect transition pressure between regimes.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
\"\"\"

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
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
class RegimeNode:
    market: str
    regime: str
    transition_pressure: float
    instability_score: float
    influence_role: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RegimeTransitionEdge:
    source: str
    target: str
    source_regime: str
    target_regime: str
    transition_score: float
    transition_type: str
    confidence: float
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRegimeTransitionGraphEngine:
    module = "oi_087_market_regime_transition_graph_engine"

    def __init__(self) -> None:
        self.last_transition_graph: Dict[str, Any] = {}

    def build_transition_graph(
        self,
        influence_graph: Optional[Dict[str, Any]] = None,
        market_state_snapshot: Optional[Dict[str, Any]] = None,
        min_transition_score: float = 12.0,
    ) -> Dict[str, Any]:
        influence_graph = influence_graph or {}
        market_state_snapshot = market_state_snapshot or {}

        raw_nodes = influence_graph.get("nodes", [])
        raw_edges = influence_graph.get("edges", [])

        regime_nodes = self._classify_nodes(raw_nodes, market_state_snapshot)
        regime_lookup = {n.market: n for n in regime_nodes}
        transition_edges = self._build_transition_edges(raw_edges, regime_lookup, min_transition_score)
        regime_counts = self._regime_counts(regime_nodes)
        transition_summary = self._transition_summary(transition_edges)

        graph = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_module": "oi_086_market_influence_graph_engine",
            "node_count": len(regime_nodes),
            "transition_edge_count": len(transition_edges),
            "regime_counts": regime_counts,
            "nodes": [n.to_dict() for n in regime_nodes],
            "transition_edges": [e.to_dict() for e in transition_edges],
            "transition_summary": transition_summary,
            "highest_pressure_markets": sorted([n.to_dict() for n in regime_nodes], key=lambda x: x["transition_pressure"], reverse=True)[:10],
            "highest_instability_markets": sorted([n.to_dict() for n in regime_nodes], key=lambda x: x["instability_score"], reverse=True)[:10],
            "dominant_transitions": sorted([e.to_dict() for e in transition_edges], key=lambda x: x["transition_score"], reverse=True)[:10],
        }

        self.last_transition_graph = graph
        return graph

    def _classify_nodes(self, nodes: List[Dict[str, Any]], state: Dict[str, Any]) -> List[RegimeNode]:
        out: List[RegimeNode] = []
        explicit_state = state.get("markets", {}) if isinstance(state.get("markets"), dict) else {}

        for node in nodes:
            if not isinstance(node, dict):
                continue

            market = _safe_str(node.get("market")).strip()
            if not market:
                continue

            outgoing = _safe_float(node.get("outgoing_influence"))
            incoming = _safe_float(node.get("incoming_influence"))
            net = _safe_float(node.get("net_influence"))
            bridge = _safe_float(node.get("bridge_score"))
            role = _safe_str(node.get("role"), "balanced")

            market_state = explicit_state.get(market, {}) if isinstance(explicit_state.get(market, {}), dict) else {}
            momentum = _safe_float(market_state.get("momentum"), 0.0)
            volatility = _safe_float(market_state.get("volatility"), 0.0)
            liquidity_stress = _safe_float(market_state.get("liquidity_stress"), 0.0)
            reversal_pressure = _safe_float(market_state.get("reversal_pressure"), 0.0)

            regime, reason = self._regime_label(outgoing, incoming, net, bridge, role, momentum, volatility, liquidity_stress, reversal_pressure)

            transition_pressure = _clamp(abs(net) * 0.38 + bridge * 0.22 + volatility * 0.16 + liquidity_stress * 0.16 + reversal_pressure * 0.08)
            instability = _clamp(min(outgoing, incoming) * 0.24 + bridge * 0.30 + volatility * 0.22 + liquidity_stress * 0.24)

            out.append(
                RegimeNode(
                    market=market,
                    regime=regime,
                    transition_pressure=round(transition_pressure, 4),
                    instability_score=round(instability, 4),
                    influence_role=role,
                    reason=reason,
                )
            )

        out.sort(key=lambda n: (n.transition_pressure, n.instability_score), reverse=True)
        return out

    def _regime_label(
        self,
        outgoing: float,
        incoming: float,
        net: float,
        bridge: float,
        role: str,
        momentum: float,
        volatility: float,
        liquidity_stress: float,
        reversal_pressure: float,
    ) -> Tuple[str, str]:
        if liquidity_stress >= 70 or volatility >= 80:
            return "stress", "Liquidity stress or volatility is elevated."
        if role in ("dominant_source", "source") and momentum >= 20:
            return "expansion", "Source market influence is rising with positive momentum."
        if role in ("dominant_source", "source"):
            return "accumulation", "Source market is building influence before broader confirmation."
        if role in ("dominant_sink", "sink") and liquidity_stress >= 40:
            return "contraction", "Sink market is absorbing pressure with liquidity stress."
        if role in ("dominant_sink", "sink"):
            return "distribution", "Market is receiving influence and may be reacting late."
        if bridge >= 55 and volatility >= 40:
            return "contagion", "Bridge market is carrying influence through a volatile cluster."
        if reversal_pressure >= 60:
            return "stabilization", "Reversal pressure suggests regime cooling or mean reversion."
        if abs(net) <= 20 and bridge >= 35:
            return "stabilization", "Balanced influence with bridge behavior suggests stabilization."
        return "neutral", "No strong transition signature detected."

    def _build_transition_edges(self, raw_edges: List[Dict[str, Any]], regime_lookup: Dict[str, RegimeNode], min_transition_score: float) -> List[RegimeTransitionEdge]:
        out: List[RegimeTransitionEdge] = []

        for edge in raw_edges:
            if not isinstance(edge, dict):
                continue

            source = _safe_str(edge.get("source")).strip()
            target = _safe_str(edge.get("target")).strip()
            if source not in regime_lookup or target not in regime_lookup:
                continue

            src = regime_lookup[source]
            tgt = regime_lookup[target]
            influence = _safe_float(edge.get("influence_score"))
            confidence = _safe_float(edge.get("confidence"), 50.0)

            regime_gap = abs(src.transition_pressure - tgt.transition_pressure)
            instability_bonus = (src.instability_score + tgt.instability_score) / 2.0
            transition_score = _clamp(influence * 0.50 + confidence * 0.16 + regime_gap * 0.14 + instability_bonus * 0.20)

            if transition_score < min_transition_score:
                continue

            transition_type = self._transition_type(src.regime, tgt.regime)
            out.append(
                RegimeTransitionEdge(
                    source=source,
                    target=target,
                    source_regime=src.regime,
                    target_regime=tgt.regime,
                    transition_score=round(transition_score, 4),
                    transition_type=transition_type,
                    confidence=round(confidence, 4),
                    reason=f"{source} influence may transmit {src.regime} behavior into {target} {tgt.regime} state.",
                )
            )

        out.sort(key=lambda e: (e.transition_score, e.confidence), reverse=True)
        return out

    def _transition_type(self, source_regime: str, target_regime: str) -> str:
        pair = (source_regime, target_regime)
        if pair in {("stress", "contraction"), ("stress", "contagion"), ("contagion", "stress")}:
            return "risk_spread"
        if pair in {("accumulation", "expansion"), ("expansion", "accumulation")}:
            return "growth_rotation"
        if pair in {("distribution", "contraction"), ("expansion", "distribution")}:
            return "cycle_rollover"
        if pair in {("contraction", "stabilization"), ("stress", "stabilization")}:
            return "cooling_transition"
        if source_regime == target_regime:
            return "same_regime_transmission"
        return "mixed_regime_transition"

    def _regime_counts(self, nodes: List[RegimeNode]) -> Dict[str, int]:
        counts = defaultdict(int)
        for node in nodes:
            counts[node.regime] += 1
        return dict(sorted(counts.items(), key=lambda kv: kv[0]))

    def _transition_summary(self, edges: List[RegimeTransitionEdge]) -> Dict[str, Any]:
        counts = defaultdict(int)
        score_sum = defaultdict(float)
        for edge in edges:
            counts[edge.transition_type] += 1
            score_sum[edge.transition_type] += edge.transition_score

        summary = {}
        for key in sorted(counts.keys()):
            summary[key] = {"count": counts[key], "avg_score": round(score_sum[key] / max(1, counts[key]), 4)}
        return summary

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_transition_graph": bool(self.last_transition_graph),
            "node_count": self.last_transition_graph.get("node_count", 0),
            "transition_edge_count": self.last_transition_graph.get("transition_edge_count", 0),
            "read_only": True,
        }


market_regime_transition_graph_engine = MarketRegimeTransitionGraphEngine()
""", encoding="utf-8")

TEST.write_text(r"""
from qseries_v2.oracle_intelligence.market_regime_transition_graph_engine import market_regime_transition_graph_engine


def test_oi_087_market_regime_transition_graph_engine():
    influence_graph = {
        "nodes": [
            {"market": "FED-RATE", "outgoing_influence": 90, "incoming_influence": 5, "net_influence": 85, "bridge_score": 12, "role": "dominant_source"},
            {"market": "NASDAQ", "outgoing_influence": 62, "incoming_influence": 86, "net_influence": -24, "bridge_score": 70, "role": "bridge"},
            {"market": "AI-SECTOR", "outgoing_influence": 35, "incoming_influence": 75, "net_influence": -40, "bridge_score": 54, "role": "sink"},
            {"market": "OIL", "outgoing_influence": 58, "incoming_influence": 10, "net_influence": 48, "bridge_score": 22, "role": "source"},
            {"market": "AIRLINES", "outgoing_influence": 2, "incoming_influence": 55, "net_influence": -53, "bridge_score": 11, "role": "sink"},
        ],
        "edges": [
            {"source": "FED-RATE", "target": "NASDAQ", "influence_score": 83, "confidence": 75},
            {"source": "NASDAQ", "target": "AI-SECTOR", "influence_score": 59, "confidence": 67},
            {"source": "OIL", "target": "AIRLINES", "influence_score": 52, "confidence": 70},
        ],
    }

    state = {
        "markets": {
            "FED-RATE": {"momentum": 25, "volatility": 35, "liquidity_stress": 10},
            "NASDAQ": {"momentum": -12, "volatility": 65, "liquidity_stress": 45},
            "AI-SECTOR": {"momentum": -20, "volatility": 48, "liquidity_stress": 42},
            "OIL": {"momentum": 12, "volatility": 38, "liquidity_stress": 20},
            "AIRLINES": {"momentum": -15, "volatility": 44, "liquidity_stress": 50},
        }
    }

    graph = market_regime_transition_graph_engine.build_transition_graph(influence_graph, state)

    assert graph["status"] == "ok"
    assert graph["read_only"] is True
    assert graph["node_count"] == 5
    assert graph["transition_edge_count"] >= 3
    assert graph["regime_counts"]
    assert graph["dominant_transitions"]
    assert any(n["market"] == "FED-RATE" for n in graph["nodes"])

    diag = market_regime_transition_graph_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-087 Market Regime Transition Graph Engine")
    print({
        "nodes": graph["node_count"],
        "transition_edges": graph["transition_edge_count"],
        "regimes": graph["regime_counts"],
        "top_transition": graph["dominant_transitions"][0],
    })


if __name__ == "__main__":
    test_oi_087_market_regime_transition_graph_engine()
""", encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .market_regime_transition_graph_engine import market_regime_transition_graph_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-087 INSTALLER")
print(" Market Regime Transition Graph Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-087 installed")
print()
print("Run:")
print("python test_oi_087_market_regime_transition_graph_engine.py")
