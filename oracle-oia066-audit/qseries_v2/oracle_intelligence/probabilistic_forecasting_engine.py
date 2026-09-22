"""
OI-031 Probabilistic Forecasting Engine

Purpose:
- Convert OI-030 historical outcome curves into read-only probability forecasts.
- Forecast YES/NO movement probabilities by horizon.
- No execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass
class ForecastPacket:
    module: str
    status: str
    generated_at: str
    market: Dict[str, Any]
    forecast_curve: List[Dict[str, Any]]
    horizon_forecasts: Dict[str, Any]
    overall_forecast: Dict[str, Any]
    source_confidence: Dict[str, Any]
    notes: List[str]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProbabilisticForecastingEngine:
    """
    Read-only forecasting engine built from historical outcomes.
    """

    def __init__(self, outcome_engine=None):
        self.outcome_engine = outcome_engine
        self.last_packet: Optional[Dict[str, Any]] = None

        if self.outcome_engine is None:
            try:
                from .historical_outcome_tracking_engine import oracle_outcome_engine
                self.outcome_engine = oracle_outcome_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-031 Probabilistic Forecasting Engine",
            "status": "ok" if self.outcome_engine is not None else "missing_outcome_engine",
            "outcome_engine_ready": self.outcome_engine is not None,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def forecast_market(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        outcomes = self._get_outcomes(live_market)
        packet = self._build_forecast(live_market, outcomes)
        self.last_packet = packet
        return packet

    def forecast_curve(self, live_market: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.forecast_market(live_market).get("forecast_curve", [])

    def horizon_forecast(self, live_market: Dict[str, Any], horizon_minutes: int) -> Dict[str, Any]:
        packet = self.forecast_market(live_market)
        return packet.get("horizon_forecasts", {}).get(str(horizon_minutes), {})

    def latest(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-031 Probabilistic Forecasting Engine",
                "status": "no_forecast_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

    def _get_outcomes(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.outcome_engine is None:
            return {
                "status": "missing_outcome_engine",
                "horizon_statistics": {},
                "outcome_curve": {"curve": []},
                "confidence": {"score": 0.0, "label": "missing"},
                "read_only": True,
                "execution_allowed": False,
            }

        if hasattr(self.outcome_engine, "forward_outcomes"):
            return self.outcome_engine.forward_outcomes(live_market)

        return {
            "status": "invalid_outcome_engine",
            "horizon_statistics": {},
            "outcome_curve": {"curve": []},
            "confidence": {"score": 0.0, "label": "invalid"},
            "read_only": True,
            "execution_allowed": False,
        }

    def _build_forecast(self, live_market: Dict[str, Any], outcomes: Dict[str, Any]) -> Dict[str, Any]:
        horizon_stats = outcomes.get("horizon_statistics", {}) or {}
        forecasts: Dict[str, Any] = {}
        curve: List[Dict[str, Any]] = []

        for horizon, data in horizon_stats.items():
            forecast = self._forecast_horizon(horizon, data)
            forecasts[str(horizon)] = forecast
            curve.append({
                "horizon_minutes": int(horizon),
                "yes_up_probability": forecast["yes_up_probability"],
                "yes_down_probability": forecast["yes_down_probability"],
                "no_up_probability": forecast["no_up_probability"],
                "confidence_score": forecast["confidence"]["score"],
                "expected_yes_change": forecast["expected_yes_change"],
            })

        curve.sort(key=lambda x: x["horizon_minutes"])

        overall = self._overall_forecast(curve, forecasts)

        return ForecastPacket(
            module="OI-031 Probabilistic Forecasting Engine",
            status=outcomes.get("status", "unknown"),
            generated_at=self._now(),
            market=self._market_identity(live_market),
            forecast_curve=curve,
            horizon_forecasts=forecasts,
            overall_forecast=overall,
            source_confidence=outcomes.get("confidence", {}),
            notes=[
                "Forecasts are derived from historical forward outcomes.",
                "Probabilities are descriptive and read-only.",
                "Oracle does not execute trades.",
            ],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

    def _forecast_horizon(self, horizon: str, data: Dict[str, Any]) -> Dict[str, Any]:
        yes_stats = data.get("yes_price_change", {}) or {}
        no_stats = data.get("no_price_change", {}) or {}
        conf = data.get("confidence", {}) or {}

        yes_positive = _safe_float(yes_stats.get("positive_frequency"))
        no_positive = _safe_float(no_stats.get("positive_frequency"))

        yes_mean = _safe_float(yes_stats.get("mean"))
        no_mean = _safe_float(no_stats.get("mean"))

        yes_up = self._adjust_probability(yes_positive, yes_mean, conf)
        no_up = self._adjust_probability(no_positive, no_mean, conf)

        return {
            "horizon_minutes": int(horizon),
            "observations": data.get("observations", 0),
            "yes_up_probability": yes_up,
            "yes_down_probability": round(100.0 - yes_up, 4),
            "no_up_probability": no_up,
            "no_down_probability": round(100.0 - no_up, 4),
            "expected_yes_change": yes_mean,
            "expected_no_change": no_mean,
            "confidence": {
                "score": _safe_float(conf.get("score")),
                "label": conf.get("label", "unknown"),
                "sample_size": conf.get("sample_size", 0),
                "consistency": conf.get("consistency", 0.0),
            },
            "interpretation": self._interpret_horizon(yes_up, yes_mean, conf),
            "read_only": True,
            "execution_allowed": False,
        }

    def _adjust_probability(self, base_probability: float, expected_change: float, confidence: Dict[str, Any]) -> float:
        conf_score = _safe_float(confidence.get("score"))
        confidence_weight = conf_score / 100.0

        directional_boost = max(-15.0, min(15.0, expected_change * 4.0))
        adjusted = 50.0 + ((base_probability - 50.0) * confidence_weight) + directional_boost

        return round(_clamp(adjusted), 4)

    def _overall_forecast(self, curve: List[Dict[str, Any]], forecasts: Dict[str, Any]) -> Dict[str, Any]:
        if not curve:
            return {
                "direction": "insufficient_data",
                "score": 0.0,
                "confidence": "thin",
                "interpretation": "No usable forecast curve available.",
            }

        weighted_yes = 0.0
        total_weight = 0.0

        for point in curve:
            weight = max(1.0, _safe_float(point.get("confidence_score")))
            weighted_yes += _safe_float(point.get("yes_up_probability")) * weight
            total_weight += weight

        score = round(weighted_yes / max(total_weight, 1.0), 4)

        if score >= 60:
            direction = "yes_up_bias"
        elif score <= 40:
            direction = "yes_down_bias"
        else:
            direction = "balanced"

        return {
            "direction": direction,
            "score": score,
            "confidence": self._label(abs(score - 50.0) * 2.0),
            "interpretation": self._overall_interpretation(direction, score),
        }

    def _interpret_horizon(self, yes_up_probability: float, expected_yes_change: float, confidence: Dict[str, Any]) -> str:
        if yes_up_probability >= 60:
            bias = "YES upward movement historically appeared more often."
        elif yes_up_probability <= 40:
            bias = "YES downward movement historically appeared more often."
        else:
            bias = "Historical YES movement was balanced."

        return (
            f"{bias} Expected YES change: {round(expected_yes_change, 6)}. "
            f"Confidence: {confidence.get('label', 'unknown')}."
        )

    def _overall_interpretation(self, direction: str, score: float) -> str:
        if direction == "yes_up_bias":
            return f"Historical outcomes show a YES-up bias with aggregate probability {score}."
        if direction == "yes_down_bias":
            return f"Historical outcomes show a YES-down bias with aggregate probability {score}."
        if direction == "balanced":
            return f"Historical outcomes are balanced with aggregate probability {score}."
        return "Insufficient data for overall forecast."

    def _market_identity(self, market: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": market.get("ticker") or market.get("market_ticker") or market.get("symbol"),
            "category": market.get("category") or market.get("market_category") or "unknown",
            "timestamp": market.get("timestamp"),
        }

    def _label(self, score: float) -> str:
        score = _safe_float(score)
        if score >= 85:
            return "very_high"
        if score >= 70:
            return "high"
        if score >= 50:
            return "moderate"
        if score >= 25:
            return "low"
        return "thin"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_forecast_engine = ProbabilisticForecastingEngine()
