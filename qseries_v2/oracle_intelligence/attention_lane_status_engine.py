
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
