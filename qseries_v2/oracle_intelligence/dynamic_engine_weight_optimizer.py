"""
OI-075 Dynamic Engine Weight Optimizer

Purpose:
- Convert OI-074 meta intelligence into normalized engine weights.
- Increase influence of reliable/stable engines.
- Reduce influence of weak, drifting, or poorly calibrated engines.
- Provide future consensus layers with adaptive weights.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .oracle_meta_intelligence_engine import (
    oracle_meta_intelligence_engine,
    OracleMetaIntelligenceEngine,
)


DEFAULT_BASE_WEIGHTS = {
    "case_reasoning_engine": 0.24,
    "outcome_distribution_engine": 0.24,
    "analog_retrieval_engine": 0.18,
    "adaptive_confidence_engine": 0.16,
    "market_dna_engine": 0.10,
    "knowledge_graph_engine": 0.08,
}


class DynamicEngineWeightOptimizer:
    module_name = "oi_075_dynamic_engine_weight_optimizer"

    def __init__(
        self,
        meta_engine: Optional[OracleMetaIntelligenceEngine] = None,
        base_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.meta_engine = meta_engine or oracle_meta_intelligence_engine
        self.base_weights = dict(base_weights or DEFAULT_BASE_WEIGHTS)
        self._last_weights: Dict[str, Any] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "base_weights": self.base_weights,
            "has_last_weights": bool(self._last_weights),
        }

    def optimize_weights(
        self,
        meta_report: Optional[Dict[str, Any]] = None,
        min_weight: float = 0.03,
        max_weight: float = 0.40,
    ) -> Dict[str, Any]:
        meta_report = meta_report or self.meta_engine.evaluate_engines()
        engine_scores = meta_report.get("engine_scores", {})
        recommended_changes = meta_report.get("recommended_weight_changes", {})

        raw_weights = {}

        for engine, base_weight in self.base_weights.items():
            score = engine_scores.get(engine, {})
            meta_score = float(score.get("meta_score", 50.0))
            avg_drift = float(score.get("avg_drift", 0.0))
            calibration_gap = score.get("calibration_gap")
            change = float(recommended_changes.get(engine, 0.0))

            multiplier = self._multiplier(
                meta_score=meta_score,
                avg_drift=avg_drift,
                calibration_gap=calibration_gap,
                recommended_change=change,
            )

            raw = base_weight * multiplier
            raw = max(min_weight, min(max_weight, raw))
            raw_weights[engine] = raw

        normalized = self._normalize(raw_weights)

        result = {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "base_weights": dict(self.base_weights),
            "raw_weights": {k: round(v, 6) for k, v in raw_weights.items()},
            "optimized_weights": normalized,
            "weight_deltas": self._deltas(normalized),
            "meta_summary": {
                "overall_health": meta_report.get("overall_health"),
                "research_quality": meta_report.get("research_quality"),
                "best_engine": meta_report.get("best_engine"),
                "weakest_engine": meta_report.get("weakest_engine"),
                "highest_drift_engine": meta_report.get("highest_drift_engine"),
            },
            "recommended_changes": recommended_changes,
        }

        self._last_weights = result
        return result

    def get_weight(self, engine_name: str, default: Optional[float] = None) -> float:
        weights = self._last_weights.get("optimized_weights") or self.base_weights

        if engine_name in weights:
            return float(weights[engine_name])

        if default is not None:
            return float(default)

        return 0.0

    def last_weights(self) -> Dict[str, Any]:
        return self._last_weights or {
            "status": "empty",
            "read_only": True,
            "optimized_weights": dict(self.base_weights),
        }

    def _multiplier(
        self,
        meta_score: float,
        avg_drift: float,
        calibration_gap: Any,
        recommended_change: float,
    ) -> float:
        multiplier = 1.0

        multiplier += (meta_score - 50.0) / 100.0
        multiplier += recommended_change / 20.0

        if calibration_gap is not None:
            multiplier -= min(abs(float(calibration_gap)), 30.0) / 120.0

        multiplier -= min(abs(avg_drift), 40.0) / 100.0

        return max(0.35, min(1.75, multiplier))

    def _normalize(self, weights: Dict[str, float]) -> Dict[str, float]:
        total = sum(weights.values())

        if total <= 0:
            return dict(self.base_weights)

        return {
            k: round(v / total, 6)
            for k, v in sorted(weights.items())
        }

    def _deltas(self, optimized: Dict[str, float]) -> Dict[str, float]:
        return {
            engine: round(optimized.get(engine, 0.0) - base, 6)
            for engine, base in self.base_weights.items()
        }


dynamic_engine_weight_optimizer = DynamicEngineWeightOptimizer()
