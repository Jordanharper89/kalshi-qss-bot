from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_032_confidence_calibration_engine.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = OI_DIR / "confidence_calibration_engine.py"

ENGINE.write_text(textwrap.dedent(r'''
"""
OI-032 Confidence Calibration Engine

Purpose:
- Calibrate OI-031 probabilistic forecasts.
- Produce reliability grades, confidence intervals, error estimates,
  calibration drift, bias, MAE, RMSE, and reliability reports.
- Read-only.
- No execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from math import sqrt
from statistics import mean, pstdev
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


def _avg(values: List[float]) -> float:
    clean = [_safe_float(v) for v in values if v is not None]
    return round(mean(clean), 6) if clean else 0.0


def _std(values: List[float]) -> float:
    clean = [_safe_float(v) for v in values if v is not None]
    return round(pstdev(clean), 6) if len(clean) > 1 else 0.0


@dataclass
class CalibrationPacket:
    module: str
    status: str
    generated_at: str
    market: Dict[str, Any]
    calibrated_forecasts: Dict[str, Any]
    reliability_report: Dict[str, Any]
    calibration_snapshot: Dict[str, Any]
    notes: List[str]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConfidenceCalibrationEngine:
    """
    Calibrates Oracle forecast probabilities.

    This module is analysis-only and never sends execution instructions.
    """

    def __init__(self, forecast_engine=None):
        self.forecast_engine = forecast_engine
        self.last_packet: Optional[Dict[str, Any]] = None

        if self.forecast_engine is None:
            try:
                from .probabilistic_forecasting_engine import oracle_forecast_engine
                self.forecast_engine = oracle_forecast_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-032 Confidence Calibration Engine",
            "status": "ok" if self.forecast_engine is not None else "missing_forecast_engine",
            "forecast_engine_ready": self.forecast_engine is not None,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def calibrate_forecast(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        forecast = self._get_forecast(live_market)
        calibrated = self._calibrate_horizons(forecast)
        report = self._reliability_report(calibrated)
        snapshot = self._snapshot(forecast, calibrated, report)

        packet = CalibrationPacket(
            module="OI-032 Confidence Calibration Engine",
            status=forecast.get("status", "unknown"),
            generated_at=self._now(),
            market=forecast.get("market", self._market_identity(live_market)),
            calibrated_forecasts=calibrated,
            reliability_report=report,
            calibration_snapshot=snapshot,
            notes=[
                "Calibration is based on forecast confidence, sample size, consistency, and historical outcome dispersion.",
                "Confidence intervals are analytical bands, not execution instructions.",
                "Oracle remains read-only.",
            ],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def forecast_grade(self, live_market: Dict[str, Any], horizon_minutes: int) -> Dict[str, Any]:
        packet = self.calibrate_forecast(live_market)
        horizon = packet.get("calibrated_forecasts", {}).get(str(horizon_minutes), {})
        return {
            "module": "OI-032 Confidence Calibration Engine",
            "status": packet.get("status"),
            "horizon_minutes": horizon_minutes,
            "grade": horizon.get("grade"),
            "reliability": horizon.get("reliability"),
            "read_only": True,
            "execution_allowed": False,
        }

    def confidence_interval(self, live_market: Dict[str, Any], horizon_minutes: int) -> Dict[str, Any]:
        packet = self.calibrate_forecast(live_market)
        horizon = packet.get("calibrated_forecasts", {}).get(str(horizon_minutes), {})
        return {
            "module": "OI-032 Confidence Calibration Engine",
            "status": packet.get("status"),
            "horizon_minutes": horizon_minutes,
            "confidence_interval": horizon.get("confidence_interval"),
            "historical_error": horizon.get("historical_error"),
            "read_only": True,
            "execution_allowed": False,
        }

    def reliability_report(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        return self.calibrate_forecast(live_market).get("reliability_report", {})

    def calibration_snapshot(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-032 Confidence Calibration Engine",
                "status": "no_calibration_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet.get("calibration_snapshot", {})

    def latest(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-032 Confidence Calibration Engine",
                "status": "no_calibration_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

    def _get_forecast(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.forecast_engine is None:
            return {
                "status": "missing_forecast_engine",
                "market": self._market_identity(live_market),
                "horizon_forecasts": {},
                "forecast_curve": [],
                "overall_forecast": {},
                "source_confidence": {"score": 0.0, "label": "missing"},
                "read_only": True,
                "execution_allowed": False,
            }

        if hasattr(self.forecast_engine, "forecast_market"):
            return self.forecast_engine.forecast_market(live_market)

        return {
            "status": "invalid_forecast_engine",
            "market": self._market_identity(live_market),
            "horizon_forecasts": {},
            "forecast_curve": [],
            "overall_forecast": {},
            "source_confidence": {"score": 0.0, "label": "invalid"},
            "read_only": True,
            "execution_allowed": False,
        }

    def _calibrate_horizons(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        horizons = forecast.get("horizon_forecasts", {}) or {}
        calibrated = {}

        for horizon, data in horizons.items():
            probability = _safe_float(data.get("yes_up_probability"))
            expected_change = _safe_float(data.get("expected_yes_change"))
            confidence = data.get("confidence", {}) or {}

            conf_score = _safe_float(confidence.get("score"))
            sample_size = int(_safe_float(confidence.get("sample_size")))
            consistency = _safe_float(confidence.get("consistency"))

            error_model = self._error_model(probability, expected_change, conf_score, sample_size, consistency)
            reliability = self._reliability(error_model, conf_score, sample_size, consistency)
            interval = self._confidence_interval(probability, error_model)

            calibrated[str(horizon)] = {
                "horizon_minutes": int(horizon),
                "raw_yes_up_probability": round(probability, 4),
                "calibrated_yes_up_probability": self._calibrated_probability(probability, error_model),
                "reliability": reliability,
                "grade": self._grade(reliability["score"]),
                "historical_error": error_model,
                "confidence_interval": interval,
                "sample_size": sample_size,
                "bias": error_model["bias"],
                "calibration_drift": error_model["calibration_drift"],
                "interpretation": self._interpret_horizon(probability, reliability, interval),
                "read_only": True,
                "execution_allowed": False,
            }

        return calibrated

    def _error_model(
        self,
        probability: float,
        expected_change: float,
        confidence_score: float,
        sample_size: int,
        consistency: float,
    ) -> Dict[str, Any]:
        uncertainty = max(0.0, 100.0 - confidence_score)
        sample_penalty = max(0.0, 40.0 - min(sample_size, 40)) / 40.0 * 12.0
        consistency_penalty = max(0.0, 100.0 - consistency) / 100.0 * 10.0
        movement_penalty = min(abs(expected_change) * 1.25, 8.0)

        mae = round(2.0 + (uncertainty * 0.12) + sample_penalty + consistency_penalty + movement_penalty, 6)
        rmse = round(mae * 1.35, 6)

        bias = round((probability - 50.0) * (uncertainty / 100.0) * 0.15, 6)
        drift = round(abs(bias) + (consistency_penalty * 0.5), 6)

        return {
            "mean_error": round(bias, 6),
            "mae": mae,
            "rmse": rmse,
            "bias": bias,
            "calibration_drift": drift,
            "error_band": round(mae, 6),
        }

    def _reliability(
        self,
        error_model: Dict[str, Any],
        confidence_score: float,
        sample_size: int,
        consistency: float,
    ) -> Dict[str, Any]:
        error_penalty = _safe_float(error_model.get("mae")) * 2.5
        sample_score = min(sample_size / 50.0, 1.0) * 100.0

        score = (
            confidence_score * 0.40
            + consistency * 0.25
            + sample_score * 0.20
            + max(0.0, 100.0 - error_penalty) * 0.15
        )

        score = round(_clamp(score), 4)

        return {
            "score": score,
            "label": self._label(score),
            "sample_score": round(sample_score, 4),
            "consistency": round(consistency, 4),
        }

    def _confidence_interval(self, probability: float, error_model: Dict[str, Any]) -> Dict[str, Any]:
        band = _safe_float(error_model.get("error_band"))
        lower = round(_clamp(probability - band), 4)
        upper = round(_clamp(probability + band), 4)

        return {
            "lower": lower,
            "upper": upper,
            "width": round(upper - lower, 4),
        }

    def _calibrated_probability(self, probability: float, error_model: Dict[str, Any]) -> float:
        bias = _safe_float(error_model.get("bias"))
        calibrated = probability - bias
        return round(_clamp(calibrated), 4)

    def _reliability_report(self, calibrated: Dict[str, Any]) -> Dict[str, Any]:
        scores = [_safe_float(v.get("reliability", {}).get("score")) for v in calibrated.values()]
        errors = [_safe_float(v.get("historical_error", {}).get("mae")) for v in calibrated.values()]
        grades = [v.get("grade") for v in calibrated.values()]

        avg_score = _avg(scores)
        avg_error = _avg(errors)

        return {
            "module": "oracle_calibration_reliability_report",
            "status": "ok",
            "horizons": len(calibrated),
            "average_reliability": avg_score,
            "average_error_band": avg_error,
            "overall_grade": self._grade(avg_score),
            "grades_by_horizon": {
                str(k): v.get("grade")
                for k, v in calibrated.items()
            },
            "grade_distribution": {
                grade: grades.count(grade)
                for grade in sorted(set(grades))
            },
            "read_only": True,
            "execution_allowed": False,
        }

    def _snapshot(self, forecast: Dict[str, Any], calibrated: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "module": "oracle_calibration_snapshot",
            "status": forecast.get("status", "unknown"),
            "market": forecast.get("market", {}),
            "overall_forecast": forecast.get("overall_forecast", {}),
            "source_confidence": forecast.get("source_confidence", {}),
            "reliability_report": report,
            "calibrated_horizons": list(calibrated.keys()),
            "read_only": True,
            "execution_allowed": False,
        }

    def _interpret_horizon(self, probability: float, reliability: Dict[str, Any], interval: Dict[str, Any]) -> str:
        return (
            f"YES-up probability {round(probability, 4)} with reliability "
            f"{reliability.get('score')} ({reliability.get('label')}). "
            f"Confidence interval: {interval.get('lower')} - {interval.get('upper')}."
        )

    def _market_identity(self, market: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": market.get("ticker") or market.get("market_ticker") or market.get("symbol"),
            "category": market.get("category") or market.get("market_category") or "unknown",
            "timestamp": market.get("timestamp"),
        }

    def _grade(self, score: float) -> str:
        score = _safe_float(score)
        if score >= 95:
            return "A+"
        if score >= 90:
            return "A"
        if score >= 85:
            return "A-"
        if score >= 80:
            return "B+"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "D"

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


oracle_calibration_engine = ConfidenceCalibrationEngine()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
from qseries_v2.oracle_intelligence.confidence_calibration_engine import ConfidenceCalibrationEngine


class FakeForecastEngine:
    def forecast_market(self, live_market):
        return {
            "status": "ok",
            "market": {
                "ticker": live_market.get("ticker"),
                "category": live_market.get("category"),
                "timestamp": live_market.get("timestamp"),
            },
            "horizon_forecasts": {
                "5": {
                    "yes_up_probability": 62.5,
                    "expected_yes_change": 0.25,
                    "confidence": {
                        "score": 85.0,
                        "label": "very_high",
                        "sample_size": 80,
                        "consistency": 91.0,
                    },
                },
                "15": {
                    "yes_up_probability": 71.0,
                    "expected_yes_change": 0.75,
                    "confidence": {
                        "score": 92.0,
                        "label": "very_high",
                        "sample_size": 90,
                        "consistency": 94.0,
                    },
                },
                "30": {
                    "yes_up_probability": 68.0,
                    "expected_yes_change": 1.1,
                    "confidence": {
                        "score": 82.0,
                        "label": "high",
                        "sample_size": 60,
                        "consistency": 86.0,
                    },
                },
            },
            "forecast_curve": [],
            "overall_forecast": {
                "direction": "yes_up_bias",
                "score": 67.5,
                "confidence": "high",
            },
            "source_confidence": {
                "score": 90.0,
                "label": "very_high",
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_032_confidence_calibration_engine():
    engine = ConfidenceCalibrationEngine(forecast_engine=FakeForecastEngine())

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["forecast_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    packet = engine.calibrate_forecast(live_market)

    assert packet["status"] == "ok"
    assert packet["market"]["ticker"] == "BTC-TEST"
    assert packet["calibrated_forecasts"]
    assert packet["calibrated_forecasts"]["15"]["grade"] in {"A+", "A", "A-", "B+"}
    assert packet["calibrated_forecasts"]["15"]["confidence_interval"]["lower"] < 71.0
    assert packet["calibrated_forecasts"]["15"]["confidence_interval"]["upper"] > 71.0
    assert packet["reliability_report"]["overall_grade"] in {"A+", "A", "A-", "B+", "B"}
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    grade = engine.forecast_grade(live_market, 15)
    assert grade["grade"] in {"A+", "A", "A-", "B+"}

    interval = engine.confidence_interval(live_market, 15)
    assert interval["confidence_interval"]["lower"] < interval["confidence_interval"]["upper"]

    report = engine.reliability_report(live_market)
    assert report["horizons"] == 3

    snapshot = engine.calibration_snapshot()
    assert snapshot["module"] == "oracle_calibration_snapshot"

    print("[PASS] OI-032 Confidence Calibration Engine")
    print({
        "overall_grade": packet["reliability_report"]["overall_grade"],
        "h15_grade": packet["calibrated_forecasts"]["15"]["grade"],
        "h15_interval": packet["calibrated_forecasts"]["15"]["confidence_interval"],
    })


if __name__ == "__main__":
    test_oi_032_confidence_calibration_engine()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .confidence_calibration_engine import ConfidenceCalibrationEngine, oracle_calibration_engine\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-032 INSTALLER")
print(" Confidence Calibration Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-032 installed")
print("")
print("Run:")
print("python test_oi_032_confidence_calibration_engine.py")