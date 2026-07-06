from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "attention_lane_status_engine.py"
TEST = ROOT / "test_oi_105_attention_lane_status_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-105 Attention Lane Status Engine
Read-only Oracle Intelligence module.

Purpose:
- Summarize Oracle attention lanes from OI-104.
- Show which review lanes are overloaded, active, or normal.
- Produce lane-level status for Oracle dashboards.
- Does not execute trades.
"""

from typing import Dict, Any, List
import time


class AttentionLaneStatusEngine:
    module = "oi_105_attention_lane_status_engine"

    def __init__(self):
        self.last_status = {}

    def build_lane_status(self, attention_routes=None):
        attention_routes = attention_routes or {}
        routes = [r for r in attention_routes.get("routes", []) if isinstance(r, dict)]

        lane_map = {}
        for route in routes:
            lane = str(route.get("attention_lane") or "standard_monitoring")
            lane_map.setdefault(lane, []).append(route)

        lanes = []
        for lane, items in lane_map.items():
            immediate = len([x for x in items if x.get("route_priority") == "immediate"])
            priority = len([x for x in items if x.get("route_priority") == "priority"])
            active = len([x for x in items if x.get("route_priority") == "active"])
            avg_score = sum(float(x.get("priority_score", 0) or 0) for x in items) / max(1, len(items))

            load_score = min(100.0, immediate * 35 + priority * 22 + active * 12 + len(items) * 4 + avg_score * 0.20)

            lanes.append({
                "attention_lane": lane,
                "lane_status": self._status(load_score),
                "load_score": round(load_score, 4),
                "route_count": len(items),
                "immediate_count": immediate,
                "priority_count": priority,
                "active_count": active,
                "avg_priority_score": round(avg_score, 4),
                "top_market": self._top_market(items),
                "markets": [str(x.get("market")) for x in sorted(items, key=lambda r: float(r.get("priority_score", 0) or 0), reverse=True)],
                "read_only": True,
            })

        lanes.sort(key=lambda x: x["load_score"], reverse=True)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_module": "oi_104_oracle_attention_router",
            "lane_count": len(lanes),
            "lanes": lanes,
            "overloaded_lanes": [x for x in lanes if x["lane_status"] == "overloaded"],
            "active_lanes": [x for x in lanes if x["lane_status"] in {"overloaded", "hot", "active"}],
            "summary": self._summary(lanes),
        }

        self.last_status = report
        return report

    def _status(self, score):
        if score >= 85:
            return "overloaded"
        if score >= 65:
            return "hot"
        if score >= 40:
            return "active"
        if score >= 15:
            return "watch"
        return "normal"

    def _top_market(self, items):
        if not items:
            return None
        top = sorted(items, key=lambda r: float(r.get("priority_score", 0) or 0), reverse=True)[0]
        return top.get("market")

    def _summary(self, lanes):
        return {
            "top_lane": lanes[0]["attention_lane"] if lanes else None,
            "top_lane_status": lanes[0]["lane_status"] if lanes else None,
            "overloaded_count": len([x for x in lanes if x["lane_status"] == "overloaded"]),
            "hot_count": len([x for x in lanes if x["lane_status"] == "hot"]),
            "active_count": len([x for x in lanes if x["lane_status"] == "active"]),
            "total_routes": sum(x["route_count"] for x in lanes),
        }

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_status": bool(self.last_status),
            "lane_count": self.last_status.get("lane_count", 0),
            "read_only": True,
        }


attention_lane_status_engine = AttentionLaneStatusEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.attention_lane_status_engine import attention_lane_status_engine


def test_oi_105_attention_lane_status_engine():
    routes = {
        "routes": [
            {
                "market": "NASDAQ",
                "attention_lane": "alert_review",
                "route_priority": "priority",
                "priority_score": 72.94,
            },
            {
                "market": "AI-SECTOR",
                "attention_lane": "alert_review",
                "route_priority": "active",
                "priority_score": 55.2,
            },
            {
                "market": "CRYPTO",
                "attention_lane": "anomaly_review",
                "route_priority": "immediate",
                "priority_score": 88.0,
            },
            {
                "market": "FED-RATE",
                "attention_lane": "standard_monitoring",
                "route_priority": "normal",
                "priority_score": 22.0,
            },
        ]
    }

    report = attention_lane_status_engine.build_lane_status(routes)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["lane_count"] == 3
    assert report["lanes"][0]["load_score"] >= report["lanes"][-1]["load_score"]
    assert report["summary"]["total_routes"] == 4
    assert report["summary"]["top_lane"] is not None

    diag = attention_lane_status_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-105 Attention Lane Status Engine")
    print({
        "lanes": report["lane_count"],
        "summary": report["summary"],
        "top": report["lanes"][0],
    })


if __name__ == "__main__":
    test_oi_105_attention_lane_status_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .attention_lane_status_engine import attention_lane_status_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-105 INSTALLER")
print(" Attention Lane Status Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-105 installed")
print()
print("Run:")
print("py test_oi_105_attention_lane_status_engine.py")