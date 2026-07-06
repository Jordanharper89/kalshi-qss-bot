"""
OI-048 Outcome Distribution Engine

Turns retrieved historical analogs into probabilistic outcome distributions.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from statistics import mean, median, pstdev
from typing import Any, Dict, List, Optional

from .analog_market_retrieval_engine import (
    analog_market_retrieval_engine,
    AnalogMarketRetrievalEngine,
)


class OutcomeDistributionEngine:
    module_name = "oi_048_outcome_distribution_engine"

    def __init__(self, retrieval_engine: Optional[AnalogMarketRetrievalEngine] = None) -> None:
        self.retrieval_engine = retrieval_engine or analog_market_retrieval_engine

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "retrieval_engine": self.retrieval_engine.status()["status"],
        }

    def build_distribution(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 50,
        min_retrieval_score: float = 0.0,
    ) -> Dict[str, Any]:
        retrieval = self.retrieval_engine.retrieve_analogs(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
            min_retrieval_score=min_retrieval_score,
        )

        analogs = retrieval.get("top_analogs", [])

        resolution = self._resolution_distribution(analogs)
        movement = self._numeric_distribution(self._extract_moves(analogs))
        timing = self._numeric_distribution(self._extract_times(analogs))
        confidence_interval = self._confidence_interval(resolution)
        tail_risk = self._tail_risk(movement, resolution)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "query": current_setup,
            "analog_count": len(analogs),
            "resolution_distribution": resolution,
            "movement_distribution": movement,
            "timing_distribution_minutes": timing,
            "confidence_interval": confidence_interval,
            "tail_risk": tail_risk,
            "retrieval_summary": retrieval.get("summary", {}),
            "retrieval": retrieval,
        }

    def _resolution_distribution(self, analogs: List[Dict[str, Any]]) -> Dict[str, Any]:
        yes_weight = 0.0
        no_weight = 0.0
        unknown_weight = 0.0
        total_weight = 0.0

        for analog in analogs:
            weight = max(float(analog.get("retrieval_score", 0.0)), 0.01)
            result = self._extract_result(analog.get("memory", {}))

            total_weight += weight

            if result == "YES":
                yes_weight += weight
            elif result == "NO":
                no_weight += weight
            else:
                unknown_weight += weight

        if total_weight <= 0:
            return {
                "yes_probability": None,
                "no_probability": None,
                "unknown_probability": None,
                "expected_resolution": "UNKNOWN",
                "known_outcome_count": 0,
            }

        known = yes_weight + no_weight

        yes_probability = yes_weight / known if known else None
        no_probability = no_weight / known if known else None

        if yes_probability is None:
            expected = "UNKNOWN"
        else:
            expected = "YES" if yes_probability >= no_probability else "NO"

        return {
            "yes_probability": round(yes_probability, 4) if yes_probability is not None else None,
            "no_probability": round(no_probability, 4) if no_probability is not None else None,
            "unknown_probability": round(unknown_weight / total_weight, 4),
            "expected_resolution": expected,
            "known_outcome_count": int(sum(1 for a in analogs if self._extract_result(a.get("memory", {})) in {"YES", "NO"})),
            "weighted_yes": round(yes_weight, 4),
            "weighted_no": round(no_weight, 4),
            "weighted_unknown": round(unknown_weight, 4),
        }

    def _extract_moves(self, analogs: List[Dict[str, Any]]) -> List[float]:
        values = []

        for analog in analogs:
            memory = analog.get("memory", {})
            payload = memory.get("payload", {}) or {}
            outcome = payload.get("outcome", {}) if isinstance(payload.get("outcome"), dict) else {}

            candidates = [
                outcome.get("move_pct"),
                outcome.get("price_change_pct"),
                outcome.get("delta_pct"),
                payload.get("move_pct"),
                payload.get("price_change_pct"),
                payload.get("delta_pct"),
            ]

            for value in candidates:
                if self._is_number(value):
                    values.append(float(value))
                    break

        return values

    def _extract_times(self, analogs: List[Dict[str, Any]]) -> List[float]:
        values = []

        for analog in analogs:
            memory = analog.get("memory", {})
            payload = memory.get("payload", {}) or {}
            outcome = payload.get("outcome", {}) if isinstance(payload.get("outcome"), dict) else {}

            candidates = [
                outcome.get("time_to_resolution_minutes"),
                outcome.get("resolution_minutes"),
                outcome.get("expected_time_minutes"),
                payload.get("time_to_resolution_minutes"),
                payload.get("resolution_minutes"),
                payload.get("expected_time_minutes"),
            ]

            for value in candidates:
                if self._is_number(value):
                    values.append(float(value))
                    break

        return values

    def _numeric_distribution(self, values: List[float]) -> Dict[str, Any]:
        if not values:
            return {
                "count": 0,
                "mean": None,
                "median": None,
                "std_dev": None,
                "p10": None,
                "p25": None,
                "p75": None,
                "p90": None,
                "min": None,
                "max": None,
            }

        ordered = sorted(values)

        return {
            "count": len(values),
            "mean": round(mean(values), 4),
            "median": round(median(values), 4),
            "std_dev": round(pstdev(values), 4) if len(values) > 1 else 0.0,
            "p10": round(self._percentile(ordered, 10), 4),
            "p25": round(self._percentile(ordered, 25), 4),
            "p75": round(self._percentile(ordered, 75), 4),
            "p90": round(self._percentile(ordered, 90), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }

    def _confidence_interval(self, resolution: Dict[str, Any]) -> Dict[str, Any]:
        p = resolution.get("yes_probability")
        n = resolution.get("known_outcome_count", 0)

        if p is None or n <= 0:
            return {
                "target": "YES",
                "lower": None,
                "upper": None,
                "method": "wilson_approx",
            }

        z = 1.64
        denom = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denom
        margin = (z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)) / denom

        return {
            "target": "YES",
            "lower": round(max(0.0, center - margin), 4),
            "upper": round(min(1.0, center + margin), 4),
            "method": "wilson_approx",
        }

    def _tail_risk(self, movement: Dict[str, Any], resolution: Dict[str, Any]) -> Dict[str, Any]:
        p10 = movement.get("p10")
        no_probability = resolution.get("no_probability")

        if p10 is None and no_probability is None:
            return {
                "tail_risk_score": None,
                "tail_risk_level": "unknown",
            }

        downside_score = 0.0

        if p10 is not None and p10 < 0:
            downside_score += min(abs(p10) / 20.0, 1.0) * 0.55

        if no_probability is not None:
            downside_score += no_probability * 0.45

        if downside_score < 0.20:
            level = "low"
        elif downside_score < 0.45:
            level = "medium"
        else:
            level = "high"

        return {
            "tail_risk_score": round(downside_score, 4),
            "tail_risk_level": level,
        }

    def _percentile(self, ordered: List[float], pct: float) -> float:
        if not ordered:
            return 0.0

        if len(ordered) == 1:
            return ordered[0]

        k = (len(ordered) - 1) * (pct / 100.0)
        lower = int(k)
        upper = min(lower + 1, len(ordered) - 1)
        weight = k - lower

        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    def _extract_result(self, memory: Dict[str, Any]) -> str:
        payload = memory.get("payload", {}) or {}
        outcome = payload.get("outcome", {}) if isinstance(payload.get("outcome"), dict) else {}

        result = (
            outcome.get("result")
            or outcome.get("resolved_side")
            or outcome.get("winner")
            or payload.get("result")
            or payload.get("resolved_side")
        )

        if result is None:
            return "UNKNOWN"

        result = str(result).upper()
        return result if result in {"YES", "NO"} else "UNKNOWN"

    def _is_number(self, value: Any) -> bool:
        try:
            float(value)
            return True
        except Exception:
            return False


outcome_distribution_engine = OutcomeDistributionEngine()
