"""
OI-084 Causal Market Inference Engine

Purpose:
- Estimate whether one market likely causes or leads another rather than merely correlating.
- Score causal confidence using timing, consistency, strength, counterexamples, and lag.
- Read-only Oracle intelligence layer.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import math


class CausalMarketInferenceEngine:
    module_name = "oi_084_causal_market_inference_engine"

    def __init__(self) -> None:
        self._observations: List[Dict[str, Any]] = []
        self._pair_memory: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "observations": len(self._observations),
            "pairs": len(self._pair_memory),
        }

    def record_causal_observation(
        self,
        source_market: str,
        target_market: str,
        source_move_time: float,
        target_move_time: float,
        source_strength: float,
        target_strength: float,
        shared_catalyst: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        lag = float(target_move_time) - float(source_move_time)
        same_direction = (float(source_strength) >= 0 and float(target_strength) >= 0) or (float(source_strength) < 0 and float(target_strength) < 0)

        row = {
            "source_market": str(source_market),
            "target_market": str(target_market),
            "source_move_time": float(source_move_time),
            "target_move_time": float(target_move_time),
            "lag_minutes": lag,
            "source_strength": float(source_strength),
            "target_strength": float(target_strength),
            "same_direction": same_direction,
            "shared_catalyst": shared_catalyst,
            "recorded_at": self._now(),
            "metadata": metadata or {},
        }

        self._observations.append(row)
        self._pair_memory[self._pair_key(source_market, target_market)].append(row)

        return {
            "status": "ok",
            "read_only": True,
            "pair_key": self._pair_key(source_market, target_market),
            "observation": row,
        }

    def infer_causal_link(self, source_market: str, target_market: str) -> Dict[str, Any]:
        key = self._pair_key(source_market, target_market)
        rows = self._pair_memory.get(key, [])

        if not rows:
            return {
                "status": "not_found",
                "read_only": True,
                "source_market": source_market,
                "target_market": target_market,
                "causal_confidence": 0.0,
                "causal_direction": "unknown",
            }

        positive_lag = [r for r in rows if r["lag_minutes"] > 0]
        same_dir = [r for r in rows if r["same_direction"]]
        meaningful = [r for r in rows if abs(r["source_strength"]) >= 1 and abs(r["target_strength"]) >= 1]
        counterexamples = [r for r in rows if r["lag_minutes"] <= 0 or not r["same_direction"]]

        consistency = len(positive_lag) / len(rows)
        direction_consistency = len(same_dir) / len(rows)
        strength_consistency = len(meaningful) / len(rows)
        avg_lag = sum(r["lag_minutes"] for r in rows) / len(rows)
        avg_strength_ratio = sum(abs(r["target_strength"]) / max(abs(r["source_strength"]), 0.1) for r in rows) / len(rows)

        confidence = 20.0
        confidence += consistency * 30.0
        confidence += direction_consistency * 20.0
        confidence += strength_consistency * 15.0
        confidence += min(len(rows), 20) * 1.0
        confidence -= len(counterexamples) * 4.0

        if 0 < avg_lag <= 60:
            confidence += 10.0
        elif avg_lag > 240:
            confidence -= 10.0

        confidence = max(0.0, min(100.0, confidence))

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "source_market": source_market,
            "target_market": target_market,
            "pair_key": key,
            "observations": len(rows),
            "causal_direction": f"{source_market}->{target_market}",
            "causal_confidence": round(confidence, 2),
            "avg_lag_minutes": round(avg_lag, 2),
            "same_direction_rate": round(direction_consistency, 4),
            "positive_lag_rate": round(consistency, 4),
            "strength_consistency_rate": round(strength_consistency, 4),
            "avg_strength_ratio": round(avg_strength_ratio, 4),
            "counterexamples": len(counterexamples),
            "classification": self._classification(confidence),
        }

    def causal_graph(self) -> Dict[str, Any]:
        links = []
        for key in self._pair_memory:
            source, target = key.split("->", 1)
            links.append(self.infer_causal_link(source, target))

        links.sort(key=lambda x: x.get("causal_confidence", 0), reverse=True)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "link_count": len(links),
            "links": links,
            "strongest_link": links[0] if links else None,
        }

    def _classification(self, confidence: float) -> str:
        if confidence >= 85:
            return "strong_causal_candidate"
        if confidence >= 70:
            return "probable_causal_link"
        if confidence >= 55:
            return "weak_causal_link"
        return "correlation_or_noise"

    def _pair_key(self, source: Any, target: Any) -> str:
        return f"{source}->{target}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


causal_market_inference_engine = CausalMarketInferenceEngine()
