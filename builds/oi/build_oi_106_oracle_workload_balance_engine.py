from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_workload_balance_engine.py"
TEST = ROOT / "test_oi_106_oracle_workload_balance_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-106 Oracle Workload Balance Engine
Read-only Oracle Intelligence module.

Purpose:
- Analyze Oracle attention lane load from OI-105.
- Detect overloaded review lanes and suggest read-only workload redistribution.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleWorkloadBalanceEngine:
    module = "oi_106_oracle_workload_balance_engine"

    def __init__(self):
        self.last_balance = {}

    def balance_workload(self, lane_status_report=None, attention_routes=None):
        lane_status_report = lane_status_report or {}
        attention_routes = attention_routes or {}

        lanes = [x for x in lane_status_report.get("lanes", []) if isinstance(x, dict)]
        routes = [x for x in attention_routes.get("routes", []) if isinstance(x, dict)]

        lane_lookup = {str(x.get("attention_lane")): x for x in lanes}
        redistribution = []

        for route in routes:
            lane = str(route.get("attention_lane") or "standard_monitoring")
            lane_info = lane_lookup.get(lane, {})
            lane_status = str(lane_info.get("lane_status") or "normal")
            priority = str(route.get("route_priority") or "normal")
            score = self._float(route.get("priority_score"))

            suggested_lane = self._suggested_lane(route, lane_status)
            redistribution.append({
                "market": route.get("market"),
                "current_lane": lane,
                "current_lane_status": lane_status,
                "route_priority": priority,
                "priority_score": round(score, 4),
                "suggested_lane": suggested_lane,
                "redistribution_needed": suggested_lane != lane,
                "reason": self._reason(route, lane_status, suggested_lane),
                "read_only": True,
            })

        redistribution.sort(
            key=lambda x: (
                1 if x["redistribution_needed"] else 0,
                self._priority_rank(x["route_priority"]),
                x["priority_score"],
            ),
            reverse=True,
        )

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_modules": [
                "oi_105_attention_lane_status_engine",
                "oi_104_oracle_attention_router",
            ],
            "lane_count": len(lanes),
            "route_count": len(routes),
            "redistribution_count": len([x for x in redistribution if x["redistribution_needed"]]),
            "redistribution_plan": redistribution,
            "lane_balance": self._lane_balance(lanes),
            "summary": self._summary(lanes, redistribution),
        }

        self.last_balance = report
        return report

    def _suggested_lane(self, route, lane_status):
        lane = str(route.get("attention_lane") or "standard_monitoring")
        priority = str(route.get("route_priority") or "normal")
        alert_priority = str(route.get("top_alert_priority") or "none")
        health = self._float(route.get("health_score"), 50)
        recovery = self._float(route.get("recovery_score"), 50)
        anomalies = int(self._float(route.get("anomaly_count"), 0))
        alerts = int(self._float(route.get("alert_count"), 0))

        if priority == "immediate" or alert_priority == "critical":
            return "systemic_risk_review"
        if anomalies >= 2:
            return "anomaly_review"
        if alerts >= 1 and alert_priority in {"high", "elevated"}:
            return "alert_review"
        if health < 35:
            return "market_health_review"
        if recovery < 45:
            return "recovery_review"

        if lane_status in {"overloaded", "hot"} and priority in {"watch", "normal"}:
            return "standard_monitoring"

        return lane

    def _lane_balance(self, lanes):
        out = []
        for lane in lanes:
            load_score = self._float(lane.get("load_score"))
            status = str(lane.get("lane_status") or "normal")
            route_count = int(self._float(lane.get("route_count"), 0))

            out.append({
                "attention_lane": lane.get("attention_lane"),
                "load_score": round(load_score, 4),
                "lane_status": status,
                "route_count": route_count,
                "balance_state": self._balance_state(load_score),
                "read_only": True,
            })

        out.sort(key=lambda x: x["load_score"], reverse=True)
        return out

    def _balance_state(self, load_score):
        if load_score >= 85:
            return "overloaded"
        if load_score >= 65:
            return "heavy"
        if load_score >= 40:
            return "balanced_active"
        if load_score >= 15:
            return "light"
        return "idle"

    def _summary(self, lanes, redistribution):
        overloaded = len([x for x in lanes if str(x.get("lane_status")) == "overloaded"])
        hot = len([x for x in lanes if str(x.get("lane_status")) == "hot"])
        needed = len([x for x in redistribution if x["redistribution_needed"]])
        top = redistribution[0] if redistribution else None

        if overloaded:
            state = "overloaded"
        elif hot:
            state = "hot"
        elif needed:
            state = "redistribution_needed"
        else:
            state = "balanced"

        return {
            "workload_state": state,
            "overloaded_lanes": overloaded,
            "hot_lanes": hot,
            "redistribution_needed": needed,
            "top_redistribution": top,
        }

    def _reason(self, route, lane_status, suggested_lane):
        market = route.get("market")
        lane = route.get("attention_lane")
        if suggested_lane != lane:
            return f"{market} should move from {lane} to {suggested_lane} based on lane load and signal type."
        return f"{market} remains in {lane}; lane status is {lane_status}."

    def _priority_rank(self, priority):
        return {"immediate": 5, "priority": 4, "active": 3, "watch": 2, "normal": 1}.get(priority, 0)

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
            "has_balance": bool(self.last_balance),
            "route_count": self.last_balance.get("route_count", 0),
            "redistribution_count": self.last_balance.get("redistribution_count", 0),
            "read_only": True,
        }


oracle_workload_balance_engine = OracleWorkloadBalanceEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_workload_balance_engine import oracle_workload_balance_engine


def test_oi_106_oracle_workload_balance_engine():
    lane_status = {
        "lanes": [
            {
                "attention_lane": "alert_review",
                "lane_status": "hot",
                "load_score": 72,
                "route_count": 2,
            },
            {
                "attention_lane": "standard_monitoring",
                "lane_status": "normal",
                "load_score": 18,
                "route_count": 1,
            },
            {
                "attention_lane": "anomaly_review",
                "lane_status": "active",
                "load_score": 54,
                "route_count": 1,
            },
        ]
    }

    routes = {
        "routes": [
            {
                "market": "NASDAQ",
                "attention_lane": "alert_review",
                "route_priority": "priority",
                "priority_score": 72.94,
                "top_alert_priority": "high",
                "health_score": 32,
                "recovery_score": 40,
                "alert_count": 1,
                "anomaly_count": 1,
            },
            {
                "market": "AI-SECTOR",
                "attention_lane": "alert_review",
                "route_priority": "watch",
                "priority_score": 35,
                "top_alert_priority": "none",
                "health_score": 60,
                "recovery_score": 65,
                "alert_count": 0,
                "anomaly_count": 0,
            },
            {
                "market": "CRYPTO",
                "attention_lane": "standard_monitoring",
                "route_priority": "immediate",
                "priority_score": 88,
                "top_alert_priority": "critical",
                "health_score": 25,
                "recovery_score": 30,
                "alert_count": 2,
                "anomaly_count": 2,
            },
        ]
    }

    report = oracle_workload_balance_engine.balance_workload(lane_status, routes)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["lane_count"] == 3
    assert report["route_count"] == 3
    assert report["redistribution_count"] >= 1
    assert report["lane_balance"][0]["load_score"] >= report["lane_balance"][-1]["load_score"]
    assert report["summary"]["workload_state"] in {"overloaded", "hot", "redistribution_needed", "balanced"}

    diag = oracle_workload_balance_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-106 Oracle Workload Balance Engine")
    print({
        "routes": report["route_count"],
        "redistribution": report["redistribution_count"],
        "summary": report["summary"],
        "top": report["redistribution_plan"][0],
    })


if __name__ == "__main__":
    test_oi_106_oracle_workload_balance_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_workload_balance_engine import oracle_workload_balance_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-106 INSTALLER")
print(" Oracle Workload Balance Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-106 installed")
print()
print("Run:")
print("py test_oi_106_oracle_workload_balance_engine.py")