from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_review_plan_engine.py"
TEST = ROOT / "test_oi_108_oracle_review_plan_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-108 Oracle Review Plan Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert OI-107 review schedule into a structured Oracle review plan.
- Organize markets into review groups, checklist categories, and review order.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleReviewPlanEngine:
    module = "oi_108_oracle_review_plan_engine"

    def __init__(self):
        self.last_plan = {}

    def build_review_plan(self, review_schedule_report=None, lane_status_report=None):
        review_schedule_report = review_schedule_report or {}
        lane_status_report = lane_status_report or {}

        schedule = [
            x for x in review_schedule_report.get("schedule", [])
            if isinstance(x, dict)
        ]

        lane_lookup = self._lane_lookup(lane_status_report.get("lanes", []))

        plan_items = []
        for item in schedule:
            market = str(item.get("market") or "UNKNOWN")
            cadence = str(item.get("review_cadence") or "normal")
            bucket = str(item.get("review_bucket") or "standard_rotation")
            lane = str(item.get("suggested_lane") or item.get("current_lane") or "standard_monitoring")
            priority_score = self._float(item.get("priority_score"))
            alert_count = int(self._float(item.get("alert_count")))
            anomaly_count = int(self._float(item.get("anomaly_count")))
            lane_info = lane_lookup.get(lane, {})

            checklist = self._checklist(
                cadence=cadence,
                lane=lane,
                alert_count=alert_count,
                anomaly_count=anomaly_count,
            )

            plan_items.append({
                "market": market,
                "review_order_score": round(self._order_score(priority_score, cadence, alert_count, anomaly_count), 4),
                "review_cadence": cadence,
                "review_bucket": bucket,
                "assigned_lane": lane,
                "lane_status": lane_info.get("lane_status", "unknown"),
                "priority_score": round(priority_score, 4),
                "alert_count": alert_count,
                "anomaly_count": anomaly_count,
                "checklist": checklist,
                "review_depth": self._review_depth(cadence, alert_count, anomaly_count),
                "review_plan_reason": self._reason(market, cadence, lane, priority_score),
                "read_only": True,
            })

        plan_items.sort(key=lambda x: x["review_order_score"], reverse=True)
        for idx, item in enumerate(plan_items, start=1):
            item["review_order"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_modules": [
                "oi_107_oracle_review_schedule_engine",
                "oi_105_attention_lane_status_engine",
            ],
            "plan_count": len(plan_items),
            "review_plan": plan_items,
            "immediate_plan": [x for x in plan_items if x["review_cadence"] == "immediate"],
            "hourly_plan": [x for x in plan_items if x["review_cadence"] == "hourly"],
            "deep_review_plan": [x for x in plan_items if x["review_depth"] == "deep"],
            "summary": self._summary(plan_items),
        }

        self.last_plan = report
        return report

    def _lane_lookup(self, lanes):
        out = {}
        for lane in lanes:
            if isinstance(lane, dict):
                name = str(lane.get("attention_lane") or "").strip()
                if name:
                    out[name] = lane
        return out

    def _checklist(self, cadence, lane, alert_count, anomaly_count):
        checklist = ["review_latest_oracle_snapshot", "confirm_read_only_context"]

        if cadence in {"immediate", "hourly"}:
            checklist.append("review_priority_queue_context")
            checklist.append("review_risk_posture_synthesis")

        if "systemic" in lane:
            checklist.append("review_systemic_risk_contagion")
            checklist.append("review_global_market_stability")

        if "alert" in lane or alert_count:
            checklist.append("review_active_alerts")
            checklist.append("review_alert_evidence")

        if "anomaly" in lane or anomaly_count:
            checklist.append("review_cross_market_anomalies")
            checklist.append("compare_previous_snapshot")

        if "health" in lane:
            checklist.append("review_market_health_dashboard")

        if "recovery" in lane:
            checklist.append("review_recovery_forecast")

        checklist.append("produce_oracle_read_only_note")
        return list(dict.fromkeys(checklist))

    def _review_depth(self, cadence, alert_count, anomaly_count):
        if cadence == "immediate" or alert_count >= 2 or anomaly_count >= 2:
            return "deep"
        if cadence in {"hourly", "frequent"} or alert_count or anomaly_count:
            return "standard"
        return "light"

    def _order_score(self, priority_score, cadence, alert_count, anomaly_count):
        cadence_bonus = {
            "immediate": 35,
            "hourly": 24,
            "frequent": 16,
            "normal": 8,
            "deferred": 0,
        }.get(cadence, 5)
        return min(100.0, priority_score * 0.65 + cadence_bonus + alert_count * 4 + anomaly_count * 5)

    def _reason(self, market, cadence, lane, score):
        return (
            f"{market} added to {cadence} review plan under {lane} "
            f"with priority score {round(score, 2)}."
        )

    def _summary(self, plan_items):
        depth_counts = {}
        cadence_counts = {}
        for item in plan_items:
            depth_counts[item["review_depth"]] = depth_counts.get(item["review_depth"], 0) + 1
            cadence_counts[item["review_cadence"]] = cadence_counts.get(item["review_cadence"], 0) + 1

        return {
            "top_market": plan_items[0]["market"] if plan_items else None,
            "top_lane": plan_items[0]["assigned_lane"] if plan_items else None,
            "depth_counts": depth_counts,
            "cadence_counts": cadence_counts,
            "deep_review_count": depth_counts.get("deep", 0),
            "total_plan_items": len(plan_items),
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
            "has_plan": bool(self.last_plan),
            "plan_count": self.last_plan.get("plan_count", 0),
            "read_only": True,
        }


oracle_review_plan_engine = OracleReviewPlanEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_review_plan_engine import oracle_review_plan_engine


def test_oi_108_oracle_review_plan_engine():
    review_schedule = {
        "schedule": [
            {
                "market": "CRYPTO",
                "review_cadence": "immediate",
                "review_bucket": "review_now",
                "priority_score": 88,
                "route_priority": "immediate",
                "current_lane": "standard_monitoring",
                "suggested_lane": "systemic_risk_review",
                "redistribution_needed": True,
                "alert_count": 2,
                "anomaly_count": 2,
                "top_alert_priority": "critical",
            },
            {
                "market": "NASDAQ",
                "review_cadence": "hourly",
                "review_bucket": "same_day_review",
                "priority_score": 72.94,
                "route_priority": "priority",
                "current_lane": "alert_review",
                "suggested_lane": "alert_review",
                "redistribution_needed": False,
                "alert_count": 1,
                "anomaly_count": 1,
                "top_alert_priority": "high",
            },
            {
                "market": "AI-SECTOR",
                "review_cadence": "frequent",
                "review_bucket": "active_rotation",
                "priority_score": 35,
                "route_priority": "watch",
                "current_lane": "alert_review",
                "suggested_lane": "standard_monitoring",
                "redistribution_needed": True,
                "alert_count": 0,
                "anomaly_count": 0,
                "top_alert_priority": "none",
            },
        ]
    }

    lane_status = {
        "lanes": [
            {"attention_lane": "systemic_risk_review", "lane_status": "active"},
            {"attention_lane": "alert_review", "lane_status": "hot"},
            {"attention_lane": "standard_monitoring", "lane_status": "normal"},
        ]
    }

    report = oracle_review_plan_engine.build_review_plan(review_schedule, lane_status)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["plan_count"] == 3
    assert report["review_plan"][0]["review_order"] == 1
    assert report["review_plan"][0]["market"] == "CRYPTO"
    assert report["review_plan"][0]["review_depth"] == "deep"
    assert "review_systemic_risk_contagion" in report["review_plan"][0]["checklist"]
    assert report["summary"]["deep_review_count"] >= 1

    diag = oracle_review_plan_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-108 Oracle Review Plan Engine")
    print({
        "plan_count": report["plan_count"],
        "summary": report["summary"],
        "top": report["review_plan"][0],
    })


if __name__ == "__main__":
    test_oi_108_oracle_review_plan_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_review_plan_engine import oracle_review_plan_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-108 INSTALLER")
print(" Oracle Review Plan Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-108 installed")
print()
print("Run:")
print("py test_oi_108_oracle_review_plan_engine.py")