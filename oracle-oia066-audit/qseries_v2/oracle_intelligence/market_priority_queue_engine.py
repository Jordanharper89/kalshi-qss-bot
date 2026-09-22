
"""
OI-103 Market Priority Queue Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle risk posture, alerts, anomalies, health, and recovery data
  into a ranked read-only market priority queue.
- This does not execute trades.
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


class MarketPriorityQueueEngine:
    module = "oi_103_market_priority_queue_engine"

    def __init__(self):
        self.last_queue = {}

    def build_priority_queue(
        self,
        risk_posture_report=None,
        alert_report=None,
        anomaly_report=None,
        health_dashboard=None,
        recovery_forecast=None,
        max_items=50,
    ):
        risk_posture_report = risk_posture_report or {}
        alert_report = alert_report or {}
        anomaly_report = anomaly_report or {}
        health_dashboard = health_dashboard or {}
        recovery_forecast = recovery_forecast or {}

        postures = self._index(risk_posture_report.get("postures", []), "market")
        health = self._index(health_dashboard.get("cards", []), "market")
        recovery = self._index(recovery_forecast.get("forecasts", []), "market")
        alerts = self._alerts_by_market(alert_report.get("alerts", []))
        anomalies = self._anomalies_by_market(anomaly_report.get("anomalies", []))

        markets = set(postures) | set(health) | set(recovery) | set(alerts) | set(anomalies)

        queue = []
        for market in markets:
            p = postures.get(market, {})
            h = health.get(market, {})
            r = recovery.get(market, {})
            market_alerts = alerts.get(market, [])
            market_anomalies = anomalies.get(market, [])

            posture_score = _f(p.get("risk_posture_score"), 50)
            health_score = _f(h.get("health_score"), 50)
            recovery_score = _f(r.get("recovery_score"), 50)
            alert_pressure = self._alert_pressure(market_alerts)
            anomaly_pressure = max([_f(a.get("anomaly_score")) for a in market_anomalies] or [0])

            urgency = _clamp(
                posture_score * 0.36
                + (100 - health_score) * 0.20
                + (100 - recovery_score) * 0.14
                + alert_pressure * 0.18
                + anomaly_pressure * 0.12
            )

            item = {
                "market": market,
                "priority_score": round(urgency, 4),
                "priority_tier": self._tier(urgency),
                "queue_action": self._queue_action(urgency),
                "risk_posture_score": round(posture_score, 4),
                "health_score": round(health_score, 4),
                "recovery_score": round(recovery_score, 4),
                "alert_count": len(market_alerts),
                "anomaly_count": len(market_anomalies),
                "top_alert_priority": self._top_alert_priority(market_alerts),
                "top_anomaly_score": round(anomaly_pressure, 4),
                "summary": self._summary_text(market, urgency, posture_score, health_score, recovery_score),
                "read_only": True,
            }
            queue.append(item)

        queue.sort(key=lambda x: x["priority_score"], reverse=True)
        for idx, item in enumerate(queue[:max_items], start=1):
            item["rank"] = idx

        final_queue = queue[:max_items]

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_modules": [
                "oi_102_risk_posture_synthesis_engine",
                "oi_095_market_stability_alert_engine",
                "oi_097_cross_market_anomaly_detection_engine",
                "oi_096_market_health_dashboard_engine",
                "oi_098_market_recovery_forecast_engine",
            ],
            "queue_count": len(final_queue),
            "priority_queue": final_queue,
            "critical_queue": [x for x in final_queue if x["priority_tier"] == "critical"],
            "high_queue": [x for x in final_queue if x["priority_tier"] == "high"],
            "queue_summary": self._queue_summary(final_queue),
        }

        self.last_queue = report
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

    def _anomalies_by_market(self, rows):
        out = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            markets = row.get("markets", [])
            if not isinstance(markets, list):
                continue
            for market in markets:
                key = _s(market).strip()
                if key:
                    out.setdefault(key, []).append(row)
        return out

    def _alert_pressure(self, rows):
        weights = {"critical": 100, "high": 75, "elevated": 55, "watch": 35, "info": 10}
        return max([weights.get(_s(r.get("priority")), 0) for r in rows] or [0])

    def _top_alert_priority(self, rows):
        rank = {"critical": 5, "high": 4, "elevated": 3, "watch": 2, "info": 1}
        best = "none"
        best_rank = 0
        for row in rows:
            priority = _s(row.get("priority"), "none")
            if rank.get(priority, 0) > best_rank:
                best = priority
                best_rank = rank.get(priority, 0)
        return best

    def _tier(self, score):
        if score >= 80:
            return "critical"
        if score >= 65:
            return "high"
        if score >= 45:
            return "elevated"
        if score >= 25:
            return "watch"
        return "low"

    def _queue_action(self, score):
        if score >= 80:
            return "immediate_oracle_review"
        if score >= 65:
            return "priority_oracle_watch"
        if score >= 45:
            return "active_monitoring"
        if score >= 25:
            return "background_monitoring"
        return "normal_rotation"

    def _summary_text(self, market, priority, posture, health, recovery):
        return (
            f"{market} priority is {self._tier(priority)} with posture "
            f"{round(posture, 2)}, health {round(health, 2)}, and recovery {round(recovery, 2)}."
        )

    def _queue_summary(self, queue):
        counts = {}
        for item in queue:
            tier = item["priority_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        return {
            "tier_counts": counts,
            "top_market": queue[0]["market"] if queue else None,
            "top_priority_score": queue[0]["priority_score"] if queue else 0,
            "critical_count": counts.get("critical", 0),
            "high_count": counts.get("high", 0),
        }

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_queue": bool(self.last_queue),
            "queue_count": self.last_queue.get("queue_count", 0),
            "read_only": True,
        }


market_priority_queue_engine = MarketPriorityQueueEngine()
