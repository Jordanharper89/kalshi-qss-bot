from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class ForecastServicePacket:
    module: str
    status: str
    generated_at: str
    market: Dict[str, Any]
    forecast: Dict[str, Any]
    calibration: Dict[str, Any]
    scenario: Dict[str, Any]
    report: Dict[str, Any]
    api_summary: Dict[str, Any]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ForecastIntelligenceService:
    def __init__(self, forecast_engine=None, calibration_engine=None, scenario_engine=None, report_engine=None):
        self.forecast_engine = forecast_engine
        self.calibration_engine = calibration_engine
        self.scenario_engine = scenario_engine
        self.report_engine = report_engine
        self.last_packet: Optional[Dict[str, Any]] = None

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

        if self.report_engine is None:
            try:
                from .explainable_forecast_report_engine import oracle_forecast_report_engine
                self.report_engine = oracle_forecast_report_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-035 Forecast Intelligence Service",
            "status": "ok",
            "forecast_engine_ready": self.forecast_engine is not None,
            "calibration_engine_ready": self.calibration_engine is not None,
            "scenario_engine_ready": self.scenario_engine is not None,
            "report_engine_ready": self.report_engine is not None,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def analyze(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        forecast = self._forecast(live_market)
        calibration = self._calibration(live_market)
        scenario = self._scenario(live_market)
        report = self._report(live_market)

        packet = ForecastServicePacket(
            module="OI-035 Forecast Intelligence Service",
            status=self._status(forecast, calibration, scenario, report),
            generated_at=self._now(),
            market=self._market_identity(live_market, forecast, calibration, scenario, report),
            forecast=forecast,
            calibration=calibration,
            scenario=scenario,
            report=report,
            api_summary=self._api_summary(forecast, calibration, scenario, report),
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def api_payload(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        packet = self.analyze(live_market)
        return {
            "module": "oracle_forecast_intelligence_payload",
            "status": packet.get("status"),
            "market": packet.get("market"),
            "summary": packet.get("api_summary"),
            "headline": (packet.get("report") or {}).get("headline"),
            "read_only": True,
            "execution_allowed": False,
        }

    def latest(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-035 Forecast Intelligence Service",
                "status": "no_analysis_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

    def _forecast(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.forecast_engine and hasattr(self.forecast_engine, "forecast_market"):
            return self.forecast_engine.forecast_market(live_market)
        return {"status": "missing_forecast_engine"}

    def _calibration(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.calibration_engine and hasattr(self.calibration_engine, "calibrate_forecast"):
            return self.calibration_engine.calibrate_forecast(live_market)
        return {"status": "missing_calibration_engine"}

    def _scenario(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.scenario_engine and hasattr(self.scenario_engine, "simulate_market"):
            return self.scenario_engine.simulate_market(live_market)
        return {"status": "missing_scenario_engine"}

    def _report(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.report_engine and hasattr(self.report_engine, "build_report"):
            return self.report_engine.build_report(live_market)
        return {"status": "missing_report_engine"}

    def _api_summary(self, forecast: Dict[str, Any], calibration: Dict[str, Any], scenario: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "forecast_direction": (forecast.get("overall_forecast") or {}).get("direction"),
            "forecast_score": (forecast.get("overall_forecast") or {}).get("score"),
            "overall_grade": (calibration.get("reliability_report") or {}).get("overall_grade"),
            "dominant_scenario": (scenario.get("dominant_scenario") or {}).get("name"),
            "headline": report.get("headline"),
            "read_only": True,
            "execution_allowed": False,
        }

    def _market_identity(self, live_market: Dict[str, Any], *sources: Dict[str, Any]) -> Dict[str, Any]:
        for source in sources:
            market = source.get("market") if isinstance(source, dict) else None
            if market:
                return market

        return {
            "ticker": live_market.get("ticker") or live_market.get("market_ticker") or live_market.get("symbol"),
            "category": live_market.get("category") or live_market.get("market_category") or "unknown",
            "timestamp": live_market.get("timestamp"),
        }

    def _status(self, *sources: Dict[str, Any]) -> str:
        statuses = [s.get("status") for s in sources if isinstance(s, dict)]
        return "ok" if "ok" in statuses else "degraded"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_forecast_intelligence_service = ForecastIntelligenceService()
