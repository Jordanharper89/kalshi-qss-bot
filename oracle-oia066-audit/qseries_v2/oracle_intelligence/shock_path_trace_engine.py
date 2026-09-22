"""
OI-090 Shock Path Trace Engine

Read-only Oracle Intelligence module.

Purpose:
- Trace possible shock paths through market influence and contagion graphs.
- Explain how a source shock can travel from source market to impacted markets.
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
class ShockPath:
    source: str
    target: str
    path: List[str]
    shock_score: float
    decay_adjusted_score: float
    hop_count: int
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ShockPathTraceEngine:
    module = "oi_090_shock_path_trace_engine"

    def __init__(self) -> None:
        self.last_trace: Dict[str, Any] = {}

    def trace_shock_paths(
        self,
        source_market: str,
        influence_graph: Optional[Dict[str, Any]] = None,
        contagion_report: Optional[Dict[str, Any]] = None,
        max_depth: int = 4,
        min_score: float = 15.0,
    ) -> Dict[str, Any]:
        source_market = _safe_str(source_market).strip()
        influence_graph = influence_graph or {}
        contagion_report = contagion_report or {}

        edges = [e for e in influence_graph.get("edges", []) if isinstance(e, dict)]
        market_scores = self._market_score_lookup(contagion_report.get("market_scores", []))
        adjacency = self._adjacency(edges)

        paths = self._search(source_market, adjacency, market_scores, max_depth, min_score)

        trace = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "source_market": source_market,
            "path_count": len(paths),
            "paths": [p.to_dict() for p in paths],
            "top_paths": [p.to_dict() for p in paths[:10]],
            "impacted_markets": self._impacted_markets(paths),
            "max_depth": max_depth,
            "min_score": min_score,
        }

        self.last_trace = trace
        return trace

    def _market_score_lookup(self, rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out = {}
        for row in rows:
            if isinstance(row, dict):
                market = _safe_str(row.get("market")).strip()
                if market:
                    out[market] = row
        return out

    def _adjacency(self, edges: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        out = defaultdict(list)
        for edge in edges:
            source = _safe_str(edge.get("source")).strip()
            target = _safe_str(edge.get("target")).strip()
            if source and target and source != target:
                out[source].append(edge)

        for source in out:
            out[source].sort(key=lambda e: _safe_float(e.get("influence_score")), reverse=True)
        return out

    def _search(
        self,
        source: str,
        adjacency: Dict[str, List[Dict[str, Any]]],
        market_scores: Dict[str, Dict[str, Any]],
        max_depth: int,
        min_score: float,
    ) -> List[ShockPath]:
        if not source:
            return []

        found: List[ShockPath] = []
        q = deque([(source, [source], 0.0, 1.0)])

        while q:
            current, path, score_sum, decay = q.popleft()
            hop_count = len(path) - 1
            if hop_count >= max_depth:
                continue

            for edge in adjacency.get(current, []):
                target = _safe_str(edge.get("target")).strip()
                if not target or target in path:
                    continue

                influence = _safe_float(edge.get("influence_score"))
                confidence = _safe_float(edge.get("confidence"), 50.0)
                systemic = _safe_float(market_scores.get(target, {}).get("systemic_importance_score"))
                vulnerability = _safe_float(market_scores.get(target, {}).get("vulnerability_score"))

                edge_score = influence * 0.52 + confidence * 0.18 + systemic * 0.18 + vulnerability * 0.12
                new_decay = decay * 0.82
                new_score_sum = score_sum + edge_score
                new_path = path + [target]
                new_hops = len(new_path) - 1
                raw_score = _clamp(new_score_sum / max(1, new_hops))
                decay_adjusted = _clamp(raw_score * new_decay)

                if decay_adjusted >= min_score:
                    found.append(
                        ShockPath(
                            source=source,
                            target=target,
                            path=new_path,
                            shock_score=round(raw_score, 4),
                            decay_adjusted_score=round(decay_adjusted, 4),
                            hop_count=new_hops,
                            explanation=f"Shock path {' -> '.join(new_path)} retains {round(decay_adjusted, 2)} adjusted pressure after {new_hops} hops.",
                        )
                    )

                q.append((target, new_path, new_score_sum, new_decay))

        found.sort(key=lambda p: (p.decay_adjusted_score, p.shock_score), reverse=True)
        return found

    def _impacted_markets(self, paths: List[ShockPath]) -> List[Dict[str, Any]]:
        bucket: Dict[str, Dict[str, Any]] = {}
        for path in paths:
            item = bucket.setdefault(path.target, {"market": path.target, "best_score": 0.0, "path_count": 0})
            item["best_score"] = max(item["best_score"], path.decay_adjusted_score)
            item["path_count"] += 1

        out = list(bucket.values())
        for item in out:
            item["best_score"] = round(item["best_score"], 4)
        out.sort(key=lambda x: (x["best_score"], x["path_count"]), reverse=True)
        return out

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_trace": bool(self.last_trace),
            "path_count": self.last_trace.get("path_count", 0),
            "read_only": True,
        }


shock_path_trace_engine = ShockPathTraceEngine()
