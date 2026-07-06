from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_033_scenario_simulation_engine.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = OI_DIR / "scenario_simulation_engine.py"

ENGINE.write_text(textwrap.dedent(r'''
"""
OI-033 Scenario Simulation Engine

Purpose:
- Convert calibrated forecasts into read-only scenario paths.
- Simulate bullish, bearish, neutral, volatility-expansion, and compression cases.
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
class ScenarioPacket:
    module: str
    status: str
    generated_at: str
    market: Dict[str, Any]
    scenarios: Dict[str, Any]
    dominant_scenario: Dict[str, Any]
    scenario_curve: List[Dict[str, Any]]
    source_reliability: Dict[str, Any]
    notes: List[str]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ScenarioSimulationEngine:
    def __init__(self, calibration_engine=None):
        self.calibration_engine = calibration_engine
        self.last_packet: Optional[Dict[str, Any]] = None

        if self.calibration_engine is None:
            try:
                from .confidence_calibration_engine import oracle_calibration_engine
                self.calibration_engine = oracle_calibration_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-033 Scenario Simulation Engine",
            "status": "ok" if self.calibration_engine is not None else "missing_calibration_engine",
            "calibration_engine_ready": self.calibration_engine is not None,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def simulate_market(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        calibration = self._get_calibration(live_market)
        scenarios = self._build_scenarios(calibration)
        dominant = self._dominant_scenario(scenarios)
        curve = self._scenario_curve(calibration, scenarios)

        packet = ScenarioPacket(
            module="OI-033 Scenario Simulation Engine",
            status=calibration.get("status", "unknown"),
            generated_at=self._now(),
            market=calibration.get("market", self._market_identity(live_market)),
            scenarios=scenarios,
            dominant_scenario=dominant,
            scenario_curve=curve,
            source_reliability=calibration.get("reliability_report", {}),
            notes=[
                "Scenario simulation is based on calibrated probabilistic forecasts.",
                "Scenarios are analytical only and do not represent execution commands.",
                "Oracle remains read-only.",
            ],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def scenario_curve(self, live_market: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.simulate_market(live_market).get("scenario_curve", [])

    def dominant_scenario(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        return self.simulate_market(live_market).get("dominant_scenario", {})

    def scenario_report(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        packet = self.simulate_market(live_market)
        return {
            "module": "OI-033 Scenario Simulation Engine",
            "status": packet.get("status"),
            "market": packet.get("market"),
            "dominant_scenario": packet.get("dominant_scenario"),
            "scenarios": packet.get("scenarios"),
            "read_only": True,
            "execution_allowed": False,
        }

    def latest(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-033 Scenario Simulation Engine",
                "status": "no_simulation_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

    def _get_calibration(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.calibration_engine is None:
            return {
                "status": "missing_calibration_engine",
                "market": self._market_identity(live_market),
                "calibrated_forecasts": {},
                "reliability_report": {},
                "read_only": True,
                "execution_allowed": False,
            }

        if hasattr(self.calibration_engine, "calibrate_forecast"):
            return self.calibration_engine.calibrate_forecast(live_market)

        return {
            "status": "invalid_calibration_engine",
            "market": self._market_identity(live_market),
            "calibrated_forecasts": {},
            "reliability_report": {},
            "read_only": True,
            "execution_allowed": False,
        }

    def _build_scenarios(self, calibration: Dict[str, Any]) -> Dict[str, Any]:
        horizons = calibration.get("calibrated_forecasts", {}) or {}

        scenario_points = {
            "bullish_yes": [],
            "bearish_yes": [],
            "neutral": [],
            "volatility_expansion": [],
            "compression": [],
        }

        for horizon, data in horizons.items():
            probability = _safe_float(data.get("calibrated_yes_up_probability"))
            raw_probability = _safe_float(data.get("raw_yes_up_probability"))
            interval = data.get("confidence_interval", {}) or {}
            lower = _safe_float(interval.get("lower"))
            upper = _safe_float(interval.get("upper"))
            width = _safe_float(interval.get("width"))
            reliability = _safe_float((data.get("reliability") or {}).get("score"))
            expected_error = _safe_float((data.get("historical_error") or {}).get("mae"))

            bullish = self._scenario_strength(probability, reliability, upper, "bullish")
            bearish = self._scenario_strength(probability, reliability, lower, "bearish")
            neutral = self._neutral_strength(probability, width, reliability)
            expansion = self._expansion_strength(width, expected_error, reliability)
            compression = self._compression_strength(width, expected_error, reliability)

            point_base = {
                "horizon_minutes": int(horizon),
                "probability": probability,
                "raw_probability": raw_probability,
                "reliability": reliability,
                "interval": interval,
            }

            scenario_points["bullish_yes"].append({**point_base, "strength": bullish})
            scenario_points["bearish_yes"].append({**point_base, "strength": bearish})
            scenario_points["neutral"].append({**point_base, "strength": neutral})
            scenario_points["volatility_expansion"].append({**point_base, "strength": expansion})
            scenario_points["compression"].append({**point_base, "strength": compression})

        return {
            name: self._summarize_scenario(name, points)
            for name, points in scenario_points.items()
        }

    def _scenario_strength(self, probability: float, reliability: float, boundary: float, side: str) -> float:
        if side == "bullish":
            directional = max(0.0, probability - 50.0) * 2.0
            boundary_bonus = max(0.0, boundary - 55.0)
        else:
            directional = max(0.0, 50.0 - probability) * 2.0
            boundary_bonus = max(0.0, 45.0 - boundary)

        return round(_clamp((directional * 0.65) + (reliability * 0.25) + (boundary_bonus * 0.10)), 4)

    def _neutral_strength(self, probability: float, width: float, reliability: float) -> float:
        balance = max(0.0, 100.0 - abs(probability - 50.0) * 4.0)
        tightness = max(0.0, 100.0 - width * 3.0)
        return round(_clamp((balance * 0.55) + (tightness * 0.25) + (reliability * 0.20)), 4)

    def _expansion_strength(self, width: float, error: float, reliability: float) -> float:
        raw = min(100.0, (width * 4.0) + (error * 5.0))
        return round(_clamp((raw * 0.75) + ((100.0 - reliability) * 0.25)), 4)

    def _compression_strength(self, width: float, error: float, reliability: float) -> float:
        raw = max(0.0, 100.0 - (width * 4.0) - (error * 5.0))
        return round(_clamp((raw * 0.70) + (reliability * 0.30)), 4)

    def _summarize_scenario(self, name: str, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not points:
            return {
                "name": name,
                "score": 0.0,
                "label": "thin",
                "points": [],
                "interpretation": "No scenario data available.",
            }

        score = round(sum(_safe_float(p.get("strength")) for p in points) / len(points), 4)

        return {
            "name": name,
            "score": score,
            "label": self._label(score),
            "points": sorted(points, key=lambda x: x["horizon_minutes"]),
            "interpretation": self._scenario_interpretation(name, score),
        }

    def _dominant_scenario(self, scenarios: Dict[str, Any]) -> Dict[str, Any]:
        if not scenarios:
            return {"name": "insufficient_data", "score": 0.0, "label": "thin"}

        dominant = max(scenarios.values(), key=lambda x: _safe_float(x.get("score")))
        return {
            "name": dominant.get("name"),
            "score": dominant.get("score"),
            "label": dominant.get("label"),
            "interpretation": dominant.get("interpretation"),
        }

    def _scenario_curve(self, calibration: Dict[str, Any], scenarios: Dict[str, Any]) -> List[Dict[str, Any]]:
        horizons = calibration.get("calibrated_forecasts", {}) or {}
        curve = []

        for horizon in sorted(horizons.keys(), key=lambda x: int(x)):
            row = {"horizon_minutes": int(horizon)}
            for scenario_name, scenario in scenarios.items():
                points = scenario.get("points", [])
                match = [p for p in points if int(p.get("horizon_minutes")) == int(horizon)]
                row[scenario_name] = match[0]["strength"] if match else 0.0
            curve.append(row)

        return curve

    def _scenario_interpretation(self, name: str, score: float) -> str:
        descriptions = {
            "bullish_yes": "YES-up scenario strength based on calibrated probabilities and reliability.",
            "bearish_yes": "YES-down scenario strength based on calibrated probabilities and reliability.",
            "neutral": "Balanced scenario where calibrated outcomes remain close to 50/50.",
            "volatility_expansion": "Wider interval and error behavior imply more uncertainty or expansion.",
            "compression": "Tighter interval and lower error behavior imply compressed outcome range.",
        }
        return f"{descriptions.get(name, 'Scenario analysis.')} Score: {score}."

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


oracle_scenario_engine = ScenarioSimulationEngine()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
from qseries_v2.oracle_intelligence.scenario_simulation_engine import ScenarioSimulationEngine


class FakeCalibrationEngine:
    def calibrate_forecast(self, live_market):
        return {
            "status": "ok",
            "market": {
                "ticker": live_market.get("ticker"),
                "category": live_market.get("category"),
                "timestamp": live_market.get("timestamp"),
            },
            "calibrated_forecasts": {
                "5": {
                    "raw_yes_up_probability": 62.5,
                    "calibrated_yes_up_probability": 62.0,
                    "reliability": {"score": 86.0, "label": "very_high"},
                    "grade": "A-",
                    "historical_error": {"mae": 3.1},
                    "confidence_interval": {"lower": 58.9, "upper": 65.1, "width": 6.2},
                },
                "15": {
                    "raw_yes_up_probability": 71.0,
                    "calibrated_yes_up_probability": 70.2,
                    "reliability": {"score": 92.0, "label": "very_high"},
                    "grade": "A",
                    "historical_error": {"mae": 2.6},
                    "confidence_interval": {"lower": 68.4, "upper": 73.6, "width": 5.2},
                },
                "30": {
                    "raw_yes_up_probability": 68.0,
                    "calibrated_yes_up_probability": 67.1,
                    "reliability": {"score": 84.0, "label": "high"},
                    "grade": "B+",
                    "historical_error": {"mae": 4.0},
                    "confidence_interval": {"lower": 64.0, "upper": 72.0, "width": 8.0},
                },
            },
            "reliability_report": {
                "overall_grade": "A-",
                "average_reliability": 87.3333,
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_033_scenario_simulation_engine():
    engine = ScenarioSimulationEngine(calibration_engine=FakeCalibrationEngine())

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["calibration_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    packet = engine.simulate_market(live_market)

    assert packet["status"] == "ok"
    assert packet["market"]["ticker"] == "BTC-TEST"
    assert packet["scenarios"]["bullish_yes"]["score"] > packet["scenarios"]["bearish_yes"]["score"]
    assert packet["dominant_scenario"]["name"] in packet["scenarios"]
    assert len(packet["scenario_curve"]) == 3
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    curve = engine.scenario_curve(live_market)
    assert curve[0]["horizon_minutes"] == 5

    dominant = engine.dominant_scenario(live_market)
    assert dominant["name"]

    report = engine.scenario_report(live_market)
    assert report["dominant_scenario"]["name"]

    print("[PASS] OI-033 Scenario Simulation Engine")
    print({
        "dominant": packet["dominant_scenario"],
        "bullish_score": packet["scenarios"]["bullish_yes"]["score"],
        "curve_points": len(packet["scenario_curve"]),
    })


if __name__ == "__main__":
    test_oi_033_scenario_simulation_engine()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .scenario_simulation_engine import ScenarioSimulationEngine, oracle_scenario_engine\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-033 INSTALLER")
print(" Scenario Simulation Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-033 installed")
print("")
print("Run:")
print("python test_oi_033_scenario_simulation_engine.py")