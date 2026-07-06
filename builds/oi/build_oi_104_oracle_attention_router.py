from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_attention_router.py"
TEST = ROOT / "test_oi_104_oracle_attention_router.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-104 Oracle Attention Router
Read-only Oracle Intelligence module.

Purpose:
- Route Oracle attention based on the Market Priority Queue.
- Decide which read-only Oracle lane should review each market next.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List, Optional
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


class OracleAttentionRouter:
    module = "oi_104_oracle_attention_router"

    def __init__(self):
        self.last_routes = {}

    def route_attention(self, priority_queue_report=None, max_routes=50):
        priority_queue_report = priority_queue_report or {}
        queue = [x for x in priority_queue_report.get("priority_queue", []) if isinstance(x, dict)]

        routes = []
        for item in queue[:max_routes]:
            market = _s(item.get("market"), "UNKNOWN")
            priority_score = _f(item.get("priority_score"))
            tier = _s(item.get("priority_tier"), "watch")
            posture = _f(item.get("risk_posture_score"))
            health = _f(item.get("health_score"), 50)
            recovery = _f(item.get("recovery_score"), 50)
            alert_count = int(_f(item.get("alert_count")))
            anomaly_count = int(_f(item.get("anomaly_count")))
            top_alert = _s(item.get("top_alert_priority"), "none")

            lane = self._lane(tier, health, recovery, alert_count, anomaly_count, top_alert)
            route_priority = self._route_priority(priority_score, tier, alert_count, anomaly_count)

            routes.append({
                "market": market,
                "route_priority": route_priority,
                "attention_lane": lane,
                "priority_score": round(priority_score, 4),
                "priority_tier": tier,
                "risk_posture_score": round(posture, 4),
                "health_score": round(health, 4),
                "recovery_score": round(recovery, 4),
                "alert_count": alert_count,
                "anomaly_count": anomaly_count,
                "top_alert_priority": top_alert,
                "routing_reason": self._reason(market, lane, tier, health, recovery, alert_count, anomaly_count),
                "read_only": True,
            })

        routes.sort(key=lambda x: (self._route_rank(x["route_priority"]), x["priority_score"]), reverse=True)
        for idx, route in enumerate(routes, start=1):
            route["route_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_module": "oi_103_market_priority_queue_engine",
            "route_count": len(routes),
            "routes": routes,
            "immediate_routes": [r for r in routes if r["route_priority"] == "immediate"],
            "priority_routes": [r for r in routes if r["route_priority"] == "priority"],
            "lane_counts": self._lane_counts(routes),
            "summary": self._summary(routes),
        }

        self.last_routes = report
        return report

    def _lane(self, tier, health, recovery, alert_count, anomaly_count, top_alert):
        if tier == "critical" or top_alert == "critical":
            return "systemic_risk_review"
        if anomaly_count >= 2:
            return "anomaly_review"
        if alert_count >= 1 and top_alert in {"high", "elevated"}:
            return "alert_review"
        if health < 35:
            return "market_health_review"
        if recovery < 45:
            return "recovery_review"
        if tier in {"high", "elevated"}:
            return "priority_monitoring"
        return "standard_monitoring"

    def _route_priority(self, priority_score, tier, alert_count, anomaly_count):
        if tier == "critical" or priority_score >= 85:
            return "immediate"
        if tier == "high" or priority_score >= 65 or alert_count >= 2 or anomaly_count >= 2:
            return "priority"
        if tier == "elevated" or priority_score >= 45:
            return "active"
        if tier == "watch" or priority_score >= 25:
            return "watch"
        return "normal"

    def _route_rank(self, priority):
        return {"immediate": 5, "priority": 4, "active": 3, "watch": 2, "normal": 1}.get(priority, 0)

    def _reason(self, market, lane, tier, health, recovery, alert_count, anomaly_count):
        return (
            f"{market} routed to {lane} because priority tier is {tier}, "
            f"health is {round(health, 2)}, recovery is {round(recovery, 2)}, "
            f"alerts={alert_count}, anomalies={anomaly_count}."
        )

    def _lane_counts(self, routes):
        counts = {}
        for route in routes:
            lane = route["attention_lane"]
            counts[lane] = counts.get(lane, 0) + 1
        return counts

    def _summary(self, routes):
        return {
            "top_route": routes[0] if routes else None,
            "immediate_count": len([r for r in routes if r["route_priority"] == "immediate"]),
            "priority_count": len([r for r in routes if r["route_priority"] == "priority"]),
            "active_count": len([r for r in routes if r["route_priority"] == "active"]),
        }

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_routes": bool(self.last_routes),
            "route_count": self.last_routes.get("route_count", 0),
            "read_only": True,
        }


oracle_attention_router = OracleAttentionRouter()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_attention_router import oracle_attention_router


def test_oi_104_oracle_attention_router():
    priority_queue = {
        "priority_queue": [
            {
                "market": "NASDAQ",
                "priority_score": 72.94,
                "priority_tier": "high",
                "risk_posture_score": 72,
                "health_score": 32,
                "recovery_score": 40,
                "alert_count": 1,
                "anomaly_count": 1,
                "top_alert_priority": "high",
            },
            {
                "market": "AI-SECTOR",
                "priority_score": 55.2,
                "priority_tier": "elevated",
                "risk_posture_score": 68,
                "health_score": 45,
                "recovery_score": 46,
                "alert_count": 1,
                "anomaly_count": 1,
                "top_alert_priority": "elevated",
            },
            {
                "market": "FED-RATE",
                "priority_score": 22.0,
                "priority_tier": "low",
                "risk_posture_score": 24,
                "health_score": 78,
                "recovery_score": 77,
                "alert_count": 1,
                "anomaly_count": 0,
                "top_alert_priority": "info",
            },
        ]
    }

    report = oracle_attention_router.route_attention(priority_queue)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["route_count"] == 3
    assert report["routes"][0]["route_rank"] == 1
    assert report["routes"][0]["route_priority"] in {"immediate", "priority", "active", "watch", "normal"}
    assert report["summary"]["top_route"]["market"] == report["routes"][0]["market"]
    assert report["lane_counts"]

    diag = oracle_attention_router.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-104 Oracle Attention Router")
    print({
        "routes": report["route_count"],
        "lane_counts": report["lane_counts"],
        "top": report["routes"][0],
    })


if __name__ == "__main__":
    test_oi_104_oracle_attention_router()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_attention_router import oracle_attention_router\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-104 INSTALLER")
print(" Oracle Attention Router")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-104 installed")
print()
print("Run:")
print("py test_oi_104_oracle_attention_router.py")