
"""
OI-111 Oracle Briefing Packet Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle decision support packets into clean briefing packets.
- Produce concise read-only summaries for downstream dashboards.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleBriefingPacketEngine:
    module = "oi_111_oracle_briefing_packet_engine"

    def __init__(self):
        self.last_briefing = {}

    def build_briefing_packets(self, support_packet_report=None, market_health_dashboard=None, alert_report=None):
        support_packet_report = support_packet_report or {}
        market_health_dashboard = market_health_dashboard or {}
        alert_report = alert_report or {}

        packets = [x for x in support_packet_report.get("support_packets", []) if isinstance(x, dict)]
        health = self._index(market_health_dashboard.get("cards", []), "market")
        alerts = self._alerts_by_market(alert_report.get("alerts", []))

        briefings = []
        for packet in packets:
            market = str(packet.get("market") or "UNKNOWN")
            h = health.get(market, {})
            market_alerts = alerts.get(market, [])

            support_score = self._float(packet.get("support_packet_score"))
            health_score = self._float(h.get("health_score"), 50)
            alert_priority = self._top_alert_priority(market_alerts)

            briefing_score = self._briefing_score(
                support_score=support_score,
                health_score=health_score,
                alert_priority=alert_priority,
                alert_count=len(market_alerts),
            )

            briefing = {
                "market": market,
                "briefing_score": round(briefing_score, 4),
                "briefing_tier": self._tier(briefing_score),
                "support_tier": packet.get("support_tier"),
                "support_packet_score": round(support_score, 4),
                "health_score": round(health_score, 4),
                "dashboard_status": h.get("dashboard_status"),
                "alert_count": len(market_alerts),
                "top_alert_priority": alert_priority,
                "briefing_title": self._title(market, briefing_score, packet),
                "briefing_summary": self._summary_text(market, packet, h, alert_priority),
                "oracle_observation": packet.get("oracle_observation"),
                "execution_allowed": False,
                "read_only": True,
            }
            briefings.append(briefing)

        briefings.sort(key=lambda x: x["briefing_score"], reverse=True)

        for idx, item in enumerate(briefings, start=1):
            item["briefing_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_110_oracle_decision_support_packet_engine",
                "oi_096_market_health_dashboard_engine",
                "oi_095_market_stability_alert_engine",
            ],
            "briefing_count": len(briefings),
            "briefing_packets": briefings,
            "top_briefings": briefings[:10],
            "urgent_briefings": [x for x in briefings if x["briefing_tier"] in {"critical", "high"}],
            "summary": self._report_summary(briefings),
        }

        self.last_briefing = report
        return report

    def _briefing_score(self, support_score, health_score, alert_priority, alert_count):
        alert_weight = {
            "critical": 100,
            "high": 75,
            "elevated": 55,
            "watch": 35,
            "info": 10,
            "none": 0,
        }.get(alert_priority, 0)

        score = (
            support_score * 0.52
            + (100 - health_score) * 0.18
            + alert_weight * 0.22
            + min(alert_count * 8, 20)
        )
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "elevated"
        if score >= 30:
            return "watch"
        return "normal"

    def _title(self, market, score, packet):
        tier = self._tier(score)
        support_tier = packet.get("support_tier")
        return f"{market} Oracle briefing: {tier} attention, {support_tier} support"

    def _summary_text(self, market, packet, health, alert_priority):
        return (
            f"{market} briefing combines support tier {packet.get('support_tier')}, "
            f"review conclusion {packet.get('review_conclusion')}, health tier "
            f"{health.get('health_tier')}, and top alert priority {alert_priority}."
        )

    def _report_summary(self, briefings):
        counts = {}
        for item in briefings:
            tier = item["briefing_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        return {
            "tier_counts": counts,
            "top_market": briefings[0]["market"] if briefings else None,
            "top_tier": briefings[0]["briefing_tier"] if briefings else None,
            "urgent_count": len([x for x in briefings if x["briefing_tier"] in {"critical", "high"}]),
            "execution_allowed": False,
        }

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = str(row.get(key) or "").strip()
                if value:
                    out[value] = row
        return out

    def _alerts_by_market(self, rows):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                market = str(row.get("market") or "").strip()
                if market:
                    out.setdefault(market, []).append(row)
        return out

    def _top_alert_priority(self, rows):
        rank = {"critical": 5, "high": 4, "elevated": 3, "watch": 2, "info": 1}
        best = "none"
        best_rank = 0
        for row in rows:
            priority = str(row.get("priority") or "none")
            if rank.get(priority, 0) > best_rank:
                best = priority
                best_rank = rank.get(priority, 0)
        return best

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
            "has_briefing": bool(self.last_briefing),
            "briefing_count": self.last_briefing.get("briefing_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_briefing_packet_engine = OracleBriefingPacketEngine()
