from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_034_explainable_forecast_report_engine.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = OI_DIR / "explainable_forecast_report_engine.py"

ENGINE.write_text(textwrap.dedent(r'''
"""
OI-034 Explainable Forecast Report Engine

Purpose:
- Combine OI-031 forecast, OI-032 calibration, and OI-033 scenarios
  into one professional Oracle forecast report.
- Read-only.
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


@dataclass
class ForecastReportPacket:
    module: str
    status: str
    generated_at: str
    market: Dict[str, Any]
    headline: str
    forecast_summary: Dict[str, Any]
    probability_curve: List[Dict[str, Any]]
    calibration_summary: Dict[str, Any]
    scenario_summary: Dict[str, Any]
    risk_notes: List[str]
    oracle_report_text: str
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExplainableForecastReportEngine:
    def __init__(self, forecast_engine=None, calibration_engine=None, scenario_engine=None):
        self.forecast_engine = forecast_engine
        self.calibration_engine = calibration_engine
        self.scenario_engine = scenario_engine
        self.last_report: Optional[Dict[str, Any]] = None

        if self.forecast_engine is None:
            try:
                from .probabilistic_forecasting_engine import oracle_forecast_engine
                self.forecast_engine = oracle_forecast_engine
            except Exception:
                pass

        if self.calibration_engine is None:
            try:
                from .confidence_calibration_engine import oracle_calibration_engine
                self.calibration_engine = oracle_calibration_engine
            except Exception:
                pass

        if self.scenario_engine is None:
            try:
                from .scenario_simulation_engine import oracle_scenario_engine
                self.scenario_engine = oracle_scenario_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-034 Explainable Forecast Report Engine",
            "status": "ok",
            "forecast_engine_ready": self.forecast_engine is not None,
            "calibration_engine_ready": self.calibration_engine is not None,
            "scenario_engine_ready": self.scenario_engine is not None,
            "last_report_ready": self.last_report is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def build_report(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        forecast = self._get_forecast(live_market)
        calibration = self._get_calibration(live_market)
        scenario = self._get_scenario(live_market)

        market = (
            forecast.get("market")
            or calibration.get("market")
            or scenario.get("market")
            or self._market_identity(live_market)
        )

        forecast_summary = self._forecast_summary(forecast)
        calibration_summary = self._calibration_summary(calibration)
        scenario_summary = self._scenario_summary(scenario)
        probability_curve = forecast.get("forecast_curve", []) or []
        risk_notes = self._risk_notes(forecast, calibration, scenario)

        headline = self._headline(market, forecast_summary, calibration_summary, scenario_summary)
        report_text = self._report_text(
            headline,
            forecast_summary,
            probability_curve,
            calibration_summary,
            scenario_summary,
            risk_notes,
        )

        packet = ForecastReportPacket(
            module="OI-034 Explainable Forecast Report Engine",
            status=self._status(forecast, calibration, scenario),
            generated_at=self._now(),
            market=market,
            headline=headline,
            forecast_summary=forecast_summary,
            probability_curve=probability_curve,
            calibration_summary=calibration_summary,
            scenario_summary=scenario_summary,
            risk_notes=risk_notes,
            oracle_report_text=report_text,
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_report = packet
        return packet

    def api_payload(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        report = self.build_report(live_market)
        return {
            "module": "oracle_explainable_forecast_report_payload",
            "status": report.get("status"),
            "market": report.get("market"),
            "headline": report.get("headline"),
            "forecast_summary": report.get("forecast_summary"),
            "calibration_summary": report.get("calibration_summary"),
            "scenario_summary": report.get("scenario_summary"),
            "risk_notes": report.get("risk_notes"),
            "read_only": True,
            "execution_allowed": False,
        }

    def latest(self) -> Dict[str, Any]:
        if self.last_report is None:
            return {
                "module": "OI-034 Explainable Forecast Report Engine",
                "status": "no_report_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_report

    def _get_forecast(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.forecast_engine and hasattr(self.forecast_engine, "forecast_market"):
            return self.forecast_engine.forecast_market(live_market)
        return {"status": "missing_forecast_engine", "market": self._market_identity(live_market), "forecast_curve": []}

    def _get_calibration(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.calibration_engine and hasattr(self.calibration_engine, "calibrate_forecast"):
            return self.calibration_engine.calibrate_forecast(live_market)
        return {"status": "missing_calibration_engine", "market": self._market_identity(live_market), "calibrated_forecasts": {}}

    def _get_scenario(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.scenario_engine and hasattr(self.scenario_engine, "simulate_market"):
            return self.scenario_engine.simulate_market(live_market)
        return {"status": "missing_scenario_engine", "market": self._market_identity(live_market), "scenarios": {}}

    def _forecast_summary(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        overall = forecast.get("overall_forecast", {}) or {}
        curve = forecast.get("forecast_curve", []) or []

        return {
            "direction": overall.get("direction", "unknown"),
            "score": _safe_float(overall.get("score")),
            "confidence": overall.get("confidence", "unknown"),
            "interpretation": overall.get("interpretation", "No forecast interpretation available."),
            "curve_points": len(curve),
        }

    def _calibration_summary(self, calibration: Dict[str, Any]) -> Dict[str, Any]:
        report = calibration.get("reliability_report", {}) or {}
        calibrated = calibration.get("calibrated_forecasts", {}) or {}

        best_horizon = None
        if calibrated:
            best_horizon = max(
                calibrated.values(),
                key=lambda x: _safe_float((x.get("reliability") or {}).get("score")),
            )

        return {
            "overall_grade": report.get("overall_grade", "unknown"),
            "average_reliability": _safe_float(report.get("average_reliability")),
            "average_error_band": _safe_float(report.get("average_error_band")),
            "horizons": report.get("horizons", len(calibrated)),
            "best_horizon": best_horizon or {},
        }

    def _scenario_summary(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        dominant = scenario.get("dominant_scenario", {}) or {}
        scenarios = scenario.get("scenarios", {}) or {}

        return {
            "dominant_scenario": dominant,
            "scenario_count": len(scenarios),
            "source_reliability": scenario.get("source_reliability", {}),
        }

    def _risk_notes(self, forecast: Dict[str, Any], calibration: Dict[str, Any], scenario: Dict[str, Any]) -> List[str]:
        notes = [
            "Oracle report is read-only analysis.",
            "Execution remains disabled inside Oracle.",
        ]

        grade = (calibration.get("reliability_report", {}) or {}).get("overall_grade")
        if grade in {"C", "D", "unknown", None}:
            notes.append("Calibration grade is weak or unavailable; treat forecast with caution.")

        dominant = (scenario.get("dominant_scenario", {}) or {}).get("name")
        if dominant in {"volatility_expansion"}:
            notes.append("Volatility expansion scenario may widen uncertainty bands.")

        if not forecast.get("forecast_curve"):
            notes.append("Forecast curve is missing or thin.")

        return notes

    def _headline(
        self,
        market: Dict[str, Any],
        forecast_summary: Dict[str, Any],
        calibration_summary: Dict[str, Any],
        scenario_summary: Dict[str, Any],
    ) -> str:
        ticker = market.get("ticker") or "Unknown Market"
        direction = forecast_summary.get("direction")
        grade = calibration_summary.get("overall_grade")
        scenario = (scenario_summary.get("dominant_scenario") or {}).get("name", "unknown_scenario")

        return f"{ticker}: {direction} | Grade {grade} | Scenario {scenario}"

    def _report_text(
        self,
        headline: str,
        forecast_summary: Dict[str, Any],
        probability_curve: List[Dict[str, Any]],
        calibration_summary: Dict[str, Any],
        scenario_summary: Dict[str, Any],
        risk_notes: List[str],
    ) -> str:
        lines = [
            headline,
            "",
            "Forecast Summary:",
            f"- Direction: {forecast_summary.get('direction')}",
            f"- Score: {forecast_summary.get('score')}",
            f"- Confidence: {forecast_summary.get('confidence')}",
            f"- Interpretation: {forecast_summary.get('interpretation')}",
            "",
            "Probability Curve:",
        ]

        for point in probability_curve:
            lines.append(
                f"- {point.get('horizon_minutes')}m: YES up {point.get('yes_up_probability')}%, "
                f"confidence {point.get('confidence_score')}"
            )

        best = calibration_summary.get("best_horizon", {}) or {}
        lines += [
            "",
            "Calibration:",
            f"- Overall grade: {calibration_summary.get('overall_grade')}",
            f"- Average reliability: {calibration_summary.get('average_reliability')}",
            f"- Average error band: {calibration_summary.get('average_error_band')}",
        ]

        if best:
            lines.append(
                f"- Best horizon: {best.get('horizon_minutes')}m, grade {best.get('grade')}, "
                f"probability {best.get('calibrated_yes_up_probability')}"
            )

        dominant = scenario_summary.get("dominant_scenario", {}) or {}
        lines += [
            "",
            "Scenario Simulation:",
            f"- Dominant scenario: {dominant.get('name')}",
            f"- Scenario score: {dominant.get('score')}",
            f"- Interpretation: {dominant.get('interpretation')}",
            "",
            "Risk Notes:",
        ]

        for note in risk_notes:
            lines.append(f"- {note}")

        return "\n".join(lines)

    def _status(self, forecast: Dict[str, Any], calibration: Dict[str, Any], scenario: Dict[str, Any]) -> str:
        statuses = {forecast.get("status"), calibration.get("status"), scenario.get("status")}
        return "ok" if "ok" in statuses else "degraded"

    def _market_identity(self, market: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": market.get("ticker") or market.get("market_ticker") or market.get("symbol"),
            "category": market.get("category") or market.get("market_category") or "unknown",
            "timestamp": market.get("timestamp"),
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_forecast_report_engine = ExplainableForecastReportEngine()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
from qseries_v2.oracle_intelligence.explainable_forecast_report_engine import ExplainableForecastReportEngine


class FakeForecastEngine:
    def forecast_market(self, live_market):
        return {
            "status": "ok",
            "market": {"ticker": live_market["ticker"], "category": live_market["category"], "timestamp": live_market["timestamp"]},
            "forecast_curve": [
                {"horizon_minutes": 5, "yes_up_probability": 62.0, "confidence_score": 85.0},
                {"horizon_minutes": 15, "yes_up_probability": 70.2, "confidence_score": 92.0},
            ],
            "overall_forecast": {
                "direction": "yes_up_bias",
                "score": 66.4,
                "confidence": "high",
                "interpretation": "Historical outcomes show a YES-up bias.",
            },
        }


class FakeCalibrationEngine:
    def calibrate_forecast(self, live_market):
        return {
            "status": "ok",
            "market": {"ticker": live_market["ticker"], "category": live_market["category"], "timestamp": live_market["timestamp"]},
            "calibrated_forecasts": {
                "15": {
                    "horizon_minutes": 15,
                    "grade": "A",
                    "calibrated_yes_up_probability": 70.2,
                    "reliability": {"score": 92.0},
                }
            },
            "reliability_report": {
                "overall_grade": "A",
                "average_reliability": 90.0,
                "average_error_band": 4.2,
                "horizons": 2,
            },
        }


class FakeScenarioEngine:
    def simulate_market(self, live_market):
        return {
            "status": "ok",
            "market": {"ticker": live_market["ticker"], "category": live_market["category"], "timestamp": live_market["timestamp"]},
            "dominant_scenario": {
                "name": "compression",
                "score": 66.7,
                "interpretation": "Compressed outcome range.",
            },
            "scenarios": {"compression": {}, "bullish_yes": {}},
            "source_reliability": {"overall_grade": "A"},
        }


def test_oi_034_explainable_forecast_report_engine():
    engine = ExplainableForecastReportEngine(
        forecast_engine=FakeForecastEngine(),
        calibration_engine=FakeCalibrationEngine(),
        scenario_engine=FakeScenarioEngine(),
    )

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["forecast_engine_ready"] is True
    assert diagnostics["calibration_engine_ready"] is True
    assert diagnostics["scenario_engine_ready"] is True

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    report = engine.build_report(live_market)

    assert report["status"] == "ok"
    assert report["headline"]
    assert "BTC-TEST" in report["headline"]
    assert report["forecast_summary"]["direction"] == "yes_up_bias"
    assert report["calibration_summary"]["overall_grade"] == "A"
    assert report["scenario_summary"]["dominant_scenario"]["name"] == "compression"
    assert report["oracle_report_text"]
    assert report["read_only"] is True
    assert report["execution_allowed"] is False

    payload = engine.api_payload(live_market)
    assert payload["headline"]
    assert payload["read_only"] is True
    assert payload["execution_allowed"] is False

    latest = engine.latest()
    assert latest["headline"] == report["headline"]

    print("[PASS] OI-034 Explainable Forecast Report Engine")
    print({
        "headline": report["headline"],
        "grade": report["calibration_summary"]["overall_grade"],
        "dominant_scenario": report["scenario_summary"]["dominant_scenario"]["name"],
    })


if __name__ == "__main__":
    test_oi_034_explainable_forecast_report_engine()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .explainable_forecast_report_engine import ExplainableForecastReportEngine, oracle_forecast_report_engine\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-034 INSTALLER")
print(" Explainable Forecast Report Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-034 installed")
print("")
print("Run:")
print("python test_oi_034_explainable_forecast_report_engine.py")