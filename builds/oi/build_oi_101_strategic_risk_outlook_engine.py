from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "strategic_risk_outlook_engine.py"
TEST = ROOT / "test_oi_101_strategic_risk_outlook_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-101 Strategic Risk Outlook Engine
Read-only Oracle Intelligence module.
"""

from typing import Any, Dict, List, Optional
import math, time


def _f(v, d=0.0):
    try:
        x = float(v)
        return d if math.isnan(x) or math.isinf(x) else x
    except Exception:
        return d


def _s(v, d=""):
    return d if v is None else str(v)


def _clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(x)))


class StrategicRiskOutlookEngine:
    module = "oi_101_strategic_risk_outlook_engine"

    def __init__(self):
        self.last_outlook = {}

    def build_outlook(
        self,
        network_intelligence=None,
        stability_index=None,
        recovery_forecast=None,
        anomaly_report=None,
        alert_report=None,
    ):
        network_intelligence = network_intelligence or {}
        stability_index = stability_index or {}
        recovery_forecast = recovery_forecast or {}
        anomaly_report = anomaly_report or {}
        alert_report = alert_report or {}

        nodes = [n for n in network_intelligence.get("nodes", []) if isinstance(n, dict)]
        forecasts = self._index(recovery_forecast.get("forecasts", []), "market")
        alerts_by_market = self._alerts(alert_report.get("alerts", []))
        anomaly_counts = self._anomaly_counts(anomaly_report.get("anomalies", []))

        outlooks = []
        for node in nodes:
            market = _s(node.get("market"), "UNKNOWN")
            network_score = _f(node.get("network_score"), 50)
            recovery = _f(forecasts.get(market, {}).get("recovery_score"), 50)
            anomalies = anomaly_counts.get(market, 0)
            alert_pressure = self._alert_pressure(alerts_by_market.get(market, []))

            risk_score = _clamp(
                (100 - network_score) * 0.38
                + (100 - recovery) * 0.22
                + anomalies * 14
                + alert_pressure * 0.22
            )

            outlooks.append({
                "market": market,
                "strategic_risk_score": round(risk_score, 4),
                "outlook": self._outlook(risk_score),
                "timeframe": self._timeframe(risk_score, recovery),
                "network_score": round(network_score, 4),
                "recovery_score": round(recovery, 4),
                "anomaly_count": anomalies,
                "alert_pressure": round(alert_pressure, 4),
                "summary": self._summary_text(market, risk_score, network_score, recovery, anomalies),
                "read_only": True,
            })

        outlooks.sort(key=lambda x: x["strategic_risk_score"], reverse=True)

        global_score = self._global_score(outlooks, stability_index)
        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "global_strategic_risk_score": global_score,
            "global_outlook": self._outlook(global_score),
            "risk_posture": stability_index.get("risk_posture"),
            "market_count": len(outlooks),
            "outlooks": outlooks,
            "highest_risk_markets": outlooks[:10],
            "lowest_risk_markets": sorted(outlooks, key=lambda x: x["strategic_risk_score"])[:10],
            "outlook_counts": self._counts(outlooks),
        }
        self.last_outlook = report
        return report

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = _s(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _alerts(self, rows):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                market = _s(row.get("market")).strip()
                if market:
                    out.setdefault(market, []).append(row)
        return out

    def _anomaly_counts(self, rows):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                for m in row.get("markets", []):
                    market = _s(m).strip()
                    if market:
                        out[market] = out.get(market, 0) + 1
        return out

    def _alert_pressure(self, rows):
        weights = {"critical": 100, "high": 75, "elevated": 55, "watch": 35, "info": 10}
        return max([weights.get(_s(r.get("priority")), 0) for r in rows] or [0])

    def _global_score(self, outlooks, stability_index):
        if not outlooks:
            return 0.0
        avg = sum(o["strategic_risk_score"] for o in outlooks) / len(outlooks)
        stability_penalty = max(0, 65 - _f(stability_index.get("global_stability_score"), 50)) * 0.30
        return round(_clamp(avg + stability_penalty), 4)

    def _outlook(self, score):
        if score >= 80:
            return "critical_risk"
        if score >= 65:
            return "high_risk"
        if score >= 45:
            return "elevated_risk"
        if score >= 25:
            return "watch"
        return "constructive"

    def _timeframe(self, score, recovery):
        if score >= 65 and recovery < 45:
            return "near_term"
        if score >= 45:
            return "short_to_medium_term"
        return "medium_term"

    def _summary_text(self, market, risk, network, recovery, anomalies):
        return f"{market} strategic risk is {self._outlook(risk)} with network score {round(network,2)}, recovery score {round(recovery,2)}, and {anomalies} anomaly signal(s)."

    def _counts(self, outlooks):
        out = {}
        for o in outlooks:
            out[o["outlook"]] = out.get(o["outlook"], 0) + 1
        return out

    def diagnostics(self):
        return {"module": self.module, "status": "ok", "has_outlook": bool(self.last_outlook), "market_count": self.last_outlook.get("market_count", 0), "read_only": True}


strategic_risk_outlook_engine = StrategicRiskOutlookEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.strategic_risk_outlook_engine import strategic_risk_outlook_engine


def test_oi_101_strategic_risk_outlook_engine():
    network = {"nodes": [{"market": "NASDAQ", "network_score": 38}, {"market": "FED-RATE", "network_score": 76}]}
    stability = {"global_stability_score": 62, "risk_posture": "heightened_monitoring"}
    recovery = {"forecasts": [{"market": "NASDAQ", "recovery_score": 40}, {"market": "FED-RATE", "recovery_score": 78}]}
    anomalies = {"anomalies": [{"markets": ["NASDAQ"], "anomaly_score": 96}]}
    alerts = {"alerts": [{"market": "NASDAQ", "priority": "high"}, {"market": "FED-RATE", "priority": "info"}]}

    report = strategic_risk_outlook_engine.build_outlook(network, stability, recovery, anomalies, alerts)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 2
    assert report["highest_risk_markets"][0]["strategic_risk_score"] >= report["highest_risk_markets"][-1]["strategic_risk_score"]
    assert report["global_outlook"] in {"critical_risk", "high_risk", "elevated_risk", "watch", "constructive"}

    print("[PASS] OI-101 Strategic Risk Outlook Engine")
    print({"markets": report["market_count"], "global": report["global_outlook"], "top": report["highest_risk_markets"][0]})


if __name__ == "__main__":
    test_oi_101_strategic_risk_outlook_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .strategic_risk_outlook_engine import strategic_risk_outlook_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-101 INSTALLER")
print(" Strategic Risk Outlook Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-101 installed")
print()
print("Run:")
print("py test_oi_101_strategic_risk_outlook_engine.py")