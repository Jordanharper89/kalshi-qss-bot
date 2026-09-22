
"""
OI-107 Oracle Review Schedule Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle workload balance and attention routing into a read-only review schedule.
- Assign review cadence labels: immediate, hourly, frequent, normal, deferred.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleReviewScheduleEngine:
    module = "oi_107_oracle_review_schedule_engine"

    def __init__(self):
        self.last_schedule = {}

    def build_review_schedule(self, workload_balance_report=None, attention_routes=None):
        workload_balance_report = workload_balance_report or {}
        attention_routes = attention_routes or {}

        redistribution = [
            x for x in workload_balance_report.get("redistribution_plan", [])
            if isinstance(x, dict)
        ]

        routes = [
            x for x in attention_routes.get("routes", [])
            if isinstance(x, dict)
        ]

        route_lookup = {}
        for route in routes:
            market = str(route.get("market") or "").strip()
            if market:
                route_lookup[market] = route

        schedule = []
        for item in redistribution:
            market = str(item.get("market") or "").strip()
            route = route_lookup.get(market, {})

            priority_score = self._float(item.get("priority_score", route.get("priority_score", 0)))
            route_priority = str(item.get("route_priority", route.get("route_priority", "normal")) or "normal")
            current_lane = str(item.get("current_lane", route.get("attention_lane", "standard_monitoring")) or "standard_monitoring")
            suggested_lane = str(item.get("suggested_lane", current_lane) or current_lane)
            redistribution_needed = bool(item.get("redistribution_needed", False))
            alert_count = int(self._float(route.get("alert_count", item.get("alert_count", 0))))
            anomaly_count = int(self._float(route.get("anomaly_count", item.get("anomaly_count", 0))))
            top_alert_priority = str(route.get("top_alert_priority", item.get("top_alert_priority", "none")) or "none")

            cadence = self._cadence(
                priority_score=priority_score,
                route_priority=route_priority,
                redistribution_needed=redistribution_needed,
                alert_count=alert_count,
                anomaly_count=anomaly_count,
                top_alert_priority=top_alert_priority,
            )

            schedule.append({
                "market": market,
                "review_cadence": cadence,
                "review_bucket": self._bucket(cadence),
                "priority_score": round(priority_score, 4),
                "route_priority": route_priority,
                "current_lane": current_lane,
                "suggested_lane": suggested_lane,
                "redistribution_needed": redistribution_needed,
                "alert_count": alert_count,
                "anomaly_count": anomaly_count,
                "top_alert_priority": top_alert_priority,
                "review_reason": self._reason(market, cadence, priority_score, route_priority, suggested_lane),
                "read_only": True,
            })

        schedule.sort(
            key=lambda x: (
                self._cadence_rank(x["review_cadence"]),
                x["priority_score"],
                x["alert_count"],
                x["anomaly_count"],
            ),
            reverse=True,
        )

        for idx, item in enumerate(schedule, start=1):
            item["schedule_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_modules": [
                "oi_106_oracle_workload_balance_engine",
                "oi_104_oracle_attention_router",
            ],
            "schedule_count": len(schedule),
            "schedule": schedule,
            "immediate_reviews": [x for x in schedule if x["review_cadence"] == "immediate"],
            "hourly_reviews": [x for x in schedule if x["review_cadence"] == "hourly"],
            "summary": self._summary(schedule),
        }

        self.last_schedule = report
        return report

    def _cadence(
        self,
        priority_score,
        route_priority,
        redistribution_needed,
        alert_count,
        anomaly_count,
        top_alert_priority,
    ):
        if top_alert_priority == "critical" or route_priority == "immediate" or priority_score >= 85:
            return "immediate"
        if route_priority == "priority" or priority_score >= 70 or alert_count >= 2 or anomaly_count >= 2:
            return "hourly"
        if redistribution_needed or route_priority == "active" or priority_score >= 55:
            return "frequent"
        if route_priority == "watch" or priority_score >= 30:
            return "normal"
        return "deferred"

    def _bucket(self, cadence):
        return {
            "immediate": "review_now",
            "hourly": "same_day_review",
            "frequent": "active_rotation",
            "normal": "standard_rotation",
            "deferred": "low_priority_rotation",
        }.get(cadence, "standard_rotation")

    def _cadence_rank(self, cadence):
        return {
            "immediate": 5,
            "hourly": 4,
            "frequent": 3,
            "normal": 2,
            "deferred": 1,
        }.get(cadence, 0)

    def _reason(self, market, cadence, score, route_priority, suggested_lane):
        return (
            f"{market} assigned {cadence} review cadence with priority score "
            f"{round(score, 2)}, route priority {route_priority}, and lane {suggested_lane}."
        )

    def _summary(self, schedule):
        counts = {}
        for item in schedule:
            cadence = item["review_cadence"]
            counts[cadence] = counts.get(cadence, 0) + 1

        return {
            "cadence_counts": counts,
            "top_market": schedule[0]["market"] if schedule else None,
            "top_cadence": schedule[0]["review_cadence"] if schedule else None,
            "review_now_count": counts.get("immediate", 0),
            "same_day_count": counts.get("hourly", 0),
        }

    def _float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_schedule": bool(self.last_schedule),
            "schedule_count": self.last_schedule.get("schedule_count", 0),
            "read_only": True,
        }


oracle_review_schedule_engine = OracleReviewScheduleEngine()
