
"""
OI-102 Risk Posture Synthesis Engine
Read-only Oracle Intelligence module.

Purpose:
- Synthesize Strategic Risk Outlook, Network Intelligence, Stability, Alerts,
  and Recovery Forecast into one clean Oracle risk posture.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Any, Dict, List, Optional
import math
import time


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


class RiskPostureSynthesisEngine:
    module = "oi_102_risk_posture_synthesis_engine"

    def __init__(self):
        self.last_posture = {}

    def synthesize_posture(
        self,
        strategic_outlook=None,
        network_intelligence=None,
        stability_index=None,
        recovery_forecast=None,
        alert_report=None,
    ):
        strategic_outlook = strategic_outlook or {}
        network_intelligence = network_intelligence or {}
        stability_index = stability_index or {}
        recovery_forecast = recovery_forecast or {}
        alert_report = alert_report or {}

        outlooks = self._index(strategic_outlook.get("outlooks", []), "market")
        network_nodes = self._index(network_intelligence.get("nodes", []), "market")
        stability_scores = self._index(stability_index.get("scores", []), "market")
        recovery_scores = self._index(recovery_forecast.get("forecasts", []), "market")
        alerts = self._alerts_by_market(alert_report.get("alerts", []))

        markets = set(outlooks) | set(network_nodes) | set(stability_scores) | set(recovery_scores) | set(alerts)

        postures = []
        for market in markets:
            o = outlooks.get(market, {})
            n = network_nodes.get(market, {})
            s = stability_scores.get(market, {})
            r = recovery_scores.get(market, {})
            market_alerts = alerts.get(market, [])

            strategic_risk = _f(o.get("strategic_risk_score"), 50)
            network_score = _f(n.get("network_score"), 50)
            stability_score = _f(s.get("stability_score"), 50)
            recovery_score = _f(r.get("recovery_score"), 50)
            alert_pressure = self._alert_pressure(market_alerts)

            posture_score = _clamp(
                strategic_risk * 0.34
                + (100 - network_score) * 0.22
                + (100 - stability_score) * 0.18
                + (100 - recovery_score) * 0.14
                + alert_pressure * 0.12
            )

            postures.append({
                "market": market,
                "risk_posture_score": round(posture_score, 4),
                "posture": self._posture(posture_score),
                "strategic_risk_score": round(strategic_risk, 4),
                "network_score": round(network_score, 4),
                "stability_score": round(stability_score, 4),
                "recovery_score": round(recovery_score, 4),
                "alert_pressure": round(alert_pressure, 4),
                "active_alerts": len(market_alerts),
                "summary": self._summary_text(market, posture_score, strategic_risk, network_score, recovery_score),
                "read_only": True,
            })

        postures.sort(key=lambda x: x["risk_posture_score"], reverse=True)

        global_score = self._global_score(postures, strategic_outlook, stability_index)
        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "market_count": len(postures),
            "global_risk_posture_score": global_score,
            "global_posture": self._posture(global_score),
            "source_global_outlook": strategic_outlook.get("global_outlook"),
            "source_risk_posture": stability_index.get("risk_posture"),
            "postures": postures,
            "highest_risk_postures": postures[:10],
            "lowest_risk_postures": sorted(postures, key=lambda x: x["risk_posture_score"])[:10],
            "posture_counts": self._counts(postures),
        }

        self.last_posture = report
        return report

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = _s(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _alerts_by_market(self, rows):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                market = _s(row.get("market")).strip()
                if market:
                    out.setdefault(market, []).append(row)
        return out

    def _alert_pressure(self, rows):
        weights = {"critical": 100, "high": 75, "elevated": 55, "watch": 35, "info": 10}
        return max([weights.get(_s(r.get("priority")), 0) for r in rows] or [0])

    def _global_score(self, postures, strategic_outlook, stability_index):
        if not postures:
            return 0.0
        avg = sum(p["risk_posture_score"] for p in postures) / len(postures)
        top_risk = max(p["risk_posture_score"] for p in postures)
        strategic_global = _f(strategic_outlook.get("global_strategic_risk_score"), avg)
        stability_gap = max(0.0, 65 - _f(stability_index.get("global_stability_score"), 50))
        return round(_clamp(avg * 0.45 + top_risk * 0.25 + strategic_global * 0.20 + stability_gap * 0.10), 4)

    def _posture(self, score):
        if score >= 80:
            return "systemic_alert"
        if score >= 65:
            return "defensive"
        if score >= 45:
            return "heightened_monitoring"
        if score >= 25:
            return "selective_risk"
        return "normal"

    def _summary_text(self, market, posture, strategic, network, recovery):
        return (
            f"{market} posture is {self._posture(posture)} with strategic risk "
            f"{round(strategic, 2)}, network score {round(network, 2)}, "
            f"and recovery score {round(recovery, 2)}."
        )

    def _counts(self, postures):
        out = {}
        for p in postures:
            out[p["posture"]] = out.get(p["posture"], 0) + 1
        return out

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_posture": bool(self.last_posture),
            "market_count": self.last_posture.get("market_count", 0),
            "read_only": True,
        }


risk_posture_synthesis_engine = RiskPostureSynthesisEngine()
