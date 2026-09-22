
"""
OI-086 Market Influence Graph Engine

Read-only Oracle Intelligence module.

Purpose:
- Build a directed market influence graph from:
  1. Propagation outputs
  2. Causal inference outputs
  3. Cross-market information flow outputs
- Identify source markets, sink markets, bridge markets, clusters, and strongest influence paths.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
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
class InfluenceEdge:
    source: str
    target: str
    influence_score: float
    confidence: float
    edge_type: str
    evidence_count: int
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InfluenceNode:
    market: str
    outgoing_influence: float
    incoming_influence: float
    net_influence: float
    bridge_score: float
    total_degree: int
    role: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketInfluenceGraphEngine:
    module = "oi_086_market_influence_graph_engine"

    def __init__(self) -> None:
        self.last_graph: Dict[str, Any] = {}

    def build_graph(
        self,
        propagation_snapshot: Optional[Dict[str, Any]] = None,
        causal_snapshot: Optional[Dict[str, Any]] = None,
        flow_snapshot: Optional[Dict[str, Any]] = None,
        min_edge_score: float = 15.0,
    ) -> Dict[str, Any]:
        propagation_snapshot = propagation_snapshot or {}
        causal_snapshot = causal_snapshot or {}
        flow_snapshot = flow_snapshot or {}

        bucket: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._ingest_propagation(bucket, propagation_snapshot)
        self._ingest_causal(bucket, causal_snapshot)
        self._ingest_flow(bucket, flow_snapshot)

        edges = self._finalize_edges(bucket, min_edge_score)
        nodes = self._build_nodes(edges)
        clusters = self._build_clusters(edges)
        strongest_paths = self._strongest_paths(edges, max_paths=12)

        graph = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_modules": {
                "propagation": bool(propagation_snapshot),
                "causal_inference": bool(causal_snapshot),
                "cross_market_flow": bool(flow_snapshot),
            },
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
            "clusters": clusters,
            "strongest_paths": strongest_paths,
            "top_sources": [n.to_dict() for n in nodes if n.role in ("dominant_source", "source")][:10],
            "top_sinks": [n.to_dict() for n in nodes if n.role in ("dominant_sink", "sink")][:10],
            "top_bridges": sorted([n.to_dict() for n in nodes], key=lambda x: x["bridge_score"], reverse=True)[:10],
        }
        self.last_graph = graph
        return graph

    def _blank_edge(self) -> Dict[str, Any]:
        return {"score": 0.0, "confidence_sum": 0.0, "evidence_count": 0, "reasons": []}

    def _add_edge(
        self,
        bucket: Dict[Tuple[str, str], Dict[str, Any]],
        source: Any,
        target: Any,
        score: Any,
        confidence: Any,
        reason: str,
        weight: float = 1.0,
    ) -> None:
        source = _safe_str(source).strip()
        target = _safe_str(target).strip()
        if not source or not target or source == target:
            return

        score_f = _safe_float(score) * weight
        confidence_f = _safe_float(confidence, 50.0)
        if score_f <= 0:
            return

        item = bucket.setdefault((source, target), self._blank_edge())
        item["score"] = _clamp(item["score"] + score_f)
        item["confidence_sum"] += _clamp(confidence_f)
        item["evidence_count"] += 1
        if reason:
            item["reasons"].append(reason)

    def _ingest_propagation(self, bucket: Dict[Tuple[str, str], Dict[str, Any]], snap: Dict[str, Any]) -> None:
        rows: List[Dict[str, Any]] = []
        for key in ("propagation_edges", "edges", "links", "relationships", "signals"):
            val = snap.get(key)
            if isinstance(val, list):
                rows.extend([x for x in val if isinstance(x, dict)])

        for row in rows:
            source = row.get("source") or row.get("from") or row.get("leader") or row.get("origin_market")
            target = row.get("target") or row.get("to") or row.get("follower") or row.get("affected_market")
            score = row.get("propagation_score") or row.get("influence_score") or row.get("score") or row.get("strength")
            confidence = row.get("confidence", 50.0)
            self._add_edge(bucket, source, target, score, confidence, "Propagation evidence indicates source-to-target movement.", 0.95)

    def _ingest_causal(self, bucket: Dict[Tuple[str, str], Dict[str, Any]], snap: Dict[str, Any]) -> None:
        rows: List[Dict[str, Any]] = []
        for key in ("causal_edges", "causal_links", "relationships", "inferences", "causes"):
            val = snap.get(key)
            if isinstance(val, list):
                rows.extend([x for x in val if isinstance(x, dict)])

        for row in rows:
            source = row.get("cause") or row.get("source") or row.get("from") or row.get("driver_market")
            target = row.get("effect") or row.get("target") or row.get("to") or row.get("impacted_market")
            score = row.get("causal_score") or row.get("causality_score") or row.get("inference_score") or row.get("score")
            confidence = row.get("confidence", 55.0)
            self._add_edge(bucket, source, target, score, confidence, "Causal inference suggests directional influence.", 1.15)

    def _ingest_flow(self, bucket: Dict[Tuple[str, str], Dict[str, Any]], snap: Dict[str, Any]) -> None:
        rows: List[Dict[str, Any]] = []
        for key in ("flow_edges", "information_flows", "cross_market_flows", "edges", "flows"):
            val = snap.get(key)
            if isinstance(val, list):
                rows.extend([x for x in val if isinstance(x, dict)])

        for row in rows:
            source = row.get("source") or row.get("from") or row.get("origin") or row.get("leader_market")
            target = row.get("target") or row.get("to") or row.get("destination") or row.get("lagging_market")
            score = row.get("flow_score") or row.get("information_flow_score") or row.get("influence_score") or row.get("score")
            confidence = row.get("confidence", 50.0)
            self._add_edge(bucket, source, target, score, confidence, "Cross-market information flow supports this edge.", 1.0)

    def _finalize_edges(self, bucket: Dict[Tuple[str, str], Dict[str, Any]], min_edge_score: float) -> List[InfluenceEdge]:
        edges: List[InfluenceEdge] = []
        for (source, target), raw in bucket.items():
            evidence_count = int(raw["evidence_count"])
            score = _clamp(raw["score"])
            confidence = _clamp(raw["confidence_sum"] / max(1, evidence_count))
            if score < min_edge_score:
                continue
            edges.append(
                InfluenceEdge(
                    source=source,
                    target=target,
                    influence_score=round(score, 4),
                    confidence=round(confidence, 4),
                    edge_type=self._edge_type(score, confidence),
                    evidence_count=evidence_count,
                    reasons=list(dict.fromkeys(raw["reasons"]))[:8],
                )
            )
        edges.sort(key=lambda e: (e.influence_score, e.confidence, e.evidence_count), reverse=True)
        return edges

    def _edge_type(self, score: float, confidence: float) -> str:
        if score >= 75 and confidence >= 70:
            return "dominant_influence"
        if score >= 50:
            return "strong_influence"
        if score >= 30:
            return "moderate_influence"
        return "weak_influence"

    def _build_nodes(self, edges: List[InfluenceEdge]) -> List[InfluenceNode]:
        outgoing = defaultdict(float)
        incoming = defaultdict(float)
        out_count = defaultdict(int)
        in_count = defaultdict(int)
        markets = set()

        for edge in edges:
            markets.add(edge.source)
            markets.add(edge.target)
            outgoing[edge.source] += edge.influence_score
            incoming[edge.target] += edge.influence_score
            out_count[edge.source] += 1
            in_count[edge.target] += 1

        nodes: List[InfluenceNode] = []
        for market in markets:
            out_val = outgoing[market]
            in_val = incoming[market]
            net = out_val - in_val
            degree = out_count[market] + in_count[market]
            bridge = min(out_val, in_val) + degree * 2.5

            if net >= 75:
                role = "dominant_source"
            elif net >= 25:
                role = "source"
            elif net <= -75:
                role = "dominant_sink"
            elif net <= -25:
                role = "sink"
            elif bridge >= 40:
                role = "bridge"
            else:
                role = "balanced"

            nodes.append(
                InfluenceNode(
                    market=market,
                    outgoing_influence=round(out_val, 4),
                    incoming_influence=round(in_val, 4),
                    net_influence=round(net, 4),
                    bridge_score=round(bridge, 4),
                    total_degree=degree,
                    role=role,
                )
            )

        nodes.sort(key=lambda n: (abs(n.net_influence), n.bridge_score, n.total_degree), reverse=True)
        return nodes

    def _build_clusters(self, edges: List[InfluenceEdge]) -> List[Dict[str, Any]]:
        adjacency = defaultdict(set)
        for edge in edges:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)

        seen = set()
        clusters: List[Dict[str, Any]] = []

        for market in sorted(adjacency.keys()):
            if market in seen:
                continue
            q = deque([market])
            seen.add(market)
            members = []
            while q:
                cur = q.popleft()
                members.append(cur)
                for nxt in adjacency[cur]:
                    if nxt not in seen:
                        seen.add(nxt)
                        q.append(nxt)

            cluster_edges = [e for e in edges if e.source in members and e.target in members]
            clusters.append(
                {
                    "cluster_id": f"influence_cluster_{len(clusters) + 1}",
                    "market_count": len(members),
                    "edge_count": len(cluster_edges),
                    "markets": sorted(members),
                    "avg_edge_score": round(sum(e.influence_score for e in cluster_edges) / max(1, len(cluster_edges)), 4),
                }
            )

        clusters.sort(key=lambda c: (c["edge_count"], c["avg_edge_score"]), reverse=True)
        return clusters

    def _strongest_paths(self, edges: List[InfluenceEdge], max_paths: int = 12) -> List[Dict[str, Any]]:
        adjacency = defaultdict(list)
        for edge in edges:
            adjacency[edge.source].append(edge)

        paths: List[Dict[str, Any]] = []
        for start in adjacency:
            q = deque([(start, [start], 0.0, 0)])
            while q:
                current, path, score, depth = q.popleft()
                if depth >= 3:
                    continue
                for edge in adjacency.get(current, []):
                    if edge.target in path:
                        continue
                    new_path = path + [edge.target]
                    new_score = score + edge.influence_score
                    if len(new_path) >= 3:
                        paths.append(
                            {
                                "path": new_path,
                                "path_length": len(new_path) - 1,
                                "path_score": round(new_score, 4),
                            }
                        )
                    q.append((edge.target, new_path, new_score, depth + 1))

        paths.sort(key=lambda p: p["path_score"], reverse=True)
        return paths[:max_paths]

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_graph": bool(self.last_graph),
            "node_count": self.last_graph.get("node_count", 0),
            "edge_count": self.last_graph.get("edge_count", 0),
            "read_only": True,
        }


market_influence_graph_engine = MarketInfluenceGraphEngine()
