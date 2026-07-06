from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "market_recovery_forecast_engine.py"
TEST = ROOT / "test_oi_098_market_recovery_forecast_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-098 Market Recovery Forecast Engine

Read-only Oracle Intelligence module.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
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
class RecoveryForecast:
    market: str
    recovery_score: float
    recovery_phase: str
    expected_recovery_window: str
    confidence: float
    blocker_score: float
    support_score: float
    reasons: List[str]

    def to_dict(self):
        return asdict(self)


class MarketRecoveryForecastEngine:
    module = "oi_098_market_recovery_forecast_engine"

    def __init__(self):
        self.last_forecast = {}

    def forecast_recovery(
        self,
        health_dashboard=None,
        resilience_report=None,
        stability_index=None,
        anomaly_report=None,
        alert_report=None,
    ):
        health_dashboard = health_dashboard or {}
        resilience_report = resilience_report or {}
        stability_index = stability_index or {}
        anomaly_report = anomaly_report or {}
        alert_report = alert_report or {}

        health = self._index(health_dashboard.get("cards", []), "market")
        resilience = self._index(resilience_report.get("scores", []), "market")
        stability = self._index(stability_index.get("scores", []), "market")
        anomalies = self._anomaly_by_market(anomaly_report.get("anomalies", []))
        alerts = self._alert_by_market(alert_report.get("alerts", []))

        markets = set(health) | set(resilience) | set(stability) | set(anomalies) | set(alerts)

        forecasts = []
        for market in markets:
            h = health.get(market, {})
            r = resilience.get(market, {})
            s = stability.get(market, {})

            health_score = _safe_float(h.get("health_score"), 50.0)
            resilience_score = _safe_float(r.get("resilience_score"), 50.0)
            stability_score = _safe_float(s.get("stability_score"), 50.0)
            risk_pressure = _safe_float(s.get("risk_pressure_score"), 50.0)
            persistence = _safe_float(s.get("persistence_penalty"), 0.0)

            market_anomalies = anomalies.get(market, [])
            market_alerts = alerts.get(market, [])

            anomaly_pressure = max([_safe_float(a.get("anomaly_score")) for a in market_anomalies] or [0.0])
            alert_pressure = self._alert_pressure(market_alerts)

            support = _clamp(resilience_score * 0.42 + stability_score * 0.32 + health_score * 0.26)
            blockers = _clamp(risk_pressure * 0.30 + persistence * 0.25 + anomaly_pressure * 0.25 + alert_pressure * 0.20)
            recovery = _clamp(support * 0.62 + (100 - blockers) * 0.38)
            confidence = _clamp(55 + abs(support - blockers) * 0.25 - len(market_anomalies) * 2.0)

            forecasts.append(RecoveryForecast(
                market=market,
                recovery_score=round(recovery, 4),
                recovery_phase=self._phase(recovery, blockers),
                expected_recovery_window=self._window(recovery, blockers),
                confidence=round(confidence, 4),
                blocker_score=round(blockers, 4),
                support_score=round(support, 4),
                reasons=self._reasons(recovery, support, blockers, len(market_anomalies), len(market_alerts)),
            ))

        forecasts.sort(key=lambda x: x.recovery_score, reverse=True)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "market_count": len(forecasts),
            "forecasts": [f.to_dict() for f in forecasts],
            "strong_recovery_candidates": [f.to_dict() for f in forecasts if f.recovery_phase in {"recovering", "stabilized"}][:10],
            "delayed_recovery_markets": [f.to_dict() for f in sorted(forecasts, key=lambda x: x.recovery_score) if f.recovery_phase in {"delayed", "blocked"}][:10],
            "phase_counts": self._counts(forecasts),
        }
        self.last_forecast = report
        return report

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = _safe_str(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _anomaly_by_market(self, rows):
        out = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            markets = row.get("markets", [])
            if not isinstance(markets, list):
                continue
            for market in markets:
                key = _safe_str(market).strip()
                if key:
                    out.setdefault(key, []).append(row)
        return out

    def _alert_by_market(self, rows):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                market = _safe_str(row.get("market")).strip()
                if market:
                    out.setdefault(market, []).append(row)
        return out

    def _alert_pressure(self, rows):
        pressure = 0.0
        weights = {"critical": 90, "high": 70, "elevated": 50, "watch": 30, "info": 10}
        for row in rows:
            pressure = max(pressure, weights.get(_safe_str(row.get("priority")), 0))
        return pressure

    def _phase(self, recovery, blockers):
        if recovery >= 75 and blockers < 45:
            return "stabilized"
        if recovery >= 60:
            return "recovering"
        if recovery >= 42:
            return "fragile_recovery"
        if blockers >= 70:
            return "blocked"
        return "delayed"

    def _window(self, recovery, blockers):
        if recovery >= 75 and blockers < 45:
            return "short"
        if recovery >= 60:
            return "medium"
        if recovery >= 42:
            return "extended"
        return "long"

    def _counts(self, forecasts):
        counts = {}
        for forecast in forecasts:
            counts[forecast.recovery_phase] = counts.get(forecast.recovery_phase, 0) + 1
        return counts

    def _reasons(self, recovery, support, blockers, anomalies, alerts):
        reasons = [f"Recovery score is {round(recovery, 2)}."]
        if support >= 65:
            reasons.append("Recovery support is meaningful.")
        if blockers >= 65:
            reasons.append("Recovery blockers are elevated.")
        if anomalies:
            reasons.append(f"{anomalies} anomaly signal(s) may slow recovery.")
        if alerts:
            reasons.append(f"{alerts} active alert(s) remain attached to this market.")
        return reasons[:8]

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_forecast": bool(self.last_forecast),
            "market_count": self.last_forecast.get("market_count", 0),
            "read_only": True,
        }


market_recovery_forecast_engine = MarketRecoveryForecastEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.market_recovery_forecast_engine import market_recovery_forecast_engine


def test_oi_098_market_recovery_forecast_engine():
    health_dashboard = {"cards": [{"market": "NASDAQ", "health_score": 32}, {"market": "FED-RATE", "health_score": 78}]}
    resilience_report = {"scores": [{"market": "NASDAQ", "resilience_score": 35}, {"market": "FED-RATE", "resilience_score": 78}]}
    stability_index = {"scores": [{"market": "NASDAQ", "stability_score": 50, "risk_pressure_score": 82, "persistence_penalty": 71}, {"market": "FED-RATE", "stability_score": 72, "risk_pressure_score": 35, "persistence_penalty": 30}]}
    anomaly_report = {"anomalies": [{"markets": ["NASDAQ"], "anomaly_score": 78, "severity": "high"}]}
    alert_report = {"alerts": [{"market": "NASDAQ", "priority": "high"}, {"market": "FED-RATE", "priority": "info"}]}

    report = market_recovery_forecast_engine.forecast_recovery(health_dashboard, resilience_report, stability_index, anomaly_report, alert_report)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 2
    assert report["forecasts"][0]["recovery_score"] >= report["forecasts"][-1]["recovery_score"]
    assert any(f["market"] == "NASDAQ" for f in report["forecasts"])

    print("[PASS] OI-098 Market Recovery Forecast Engine")
    print({"markets": report["market_count"], "phases": report["phase_counts"], "top": report["forecasts"][0]})


if __name__ == "__main__":
    test_oi_098_market_recovery_forecast_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .market_recovery_forecast_engine import market_recovery_forecast_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-098 INSTALLER")
print(" Market Recovery Forecast Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-098 installed")
print()
print("Run:")
print("python test_oi_098_market_recovery_forecast_engine.py")