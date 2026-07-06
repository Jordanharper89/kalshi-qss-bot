
"""
OI-115 Oracle Intelligence Handoff Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle executive and strategic briefings into a clean handoff packet.
- Package Oracle insights for Q Series evaluation without giving execution permission.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone


class OracleIntelligenceHandoffEngine:
    module = "oi_115_oracle_intelligence_handoff_engine"

    def __init__(self):
        self.last_handoff = {}

    def build_handoff(
        self,
        executive_packet=None,
        strategic_briefing=None,
        oracle_digest=None,
        decision_support=None,
    ):
        executive_packet = executive_packet or {}
        strategic_briefing = strategic_briefing or {}
        oracle_digest = oracle_digest or {}
        decision_support = decision_support or {}

        executive_score = self._float(executive_packet.get("executive_score"))
        strategic_score = self._float(strategic_briefing.get("strategic_score"))
        digest_items = [x for x in oracle_digest.get("digest_items", []) if isinstance(x, dict)]
        support_packets = [x for x in decision_support.get("support_packets", []) if isinstance(x, dict)]

        handoff_items = self._build_handoff_items(digest_items, support_packets)

        handoff_score = self._handoff_score(
            executive_score=executive_score,
            strategic_score=strategic_score,
            handoff_items=handoff_items,
        )

        packet = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_modules": [
                "oi_113_oracle_executive_intelligence_engine",
                "oi_114_oracle_strategic_briefing_engine",
                "oi_112_oracle_digest_engine",
                "oi_110_oracle_decision_support_packet_engine",
            ],
            "handoff_score": round(handoff_score, 4),
            "handoff_posture": self._posture(handoff_score),
            "executive_score": round(executive_score, 4),
            "strategic_score": round(strategic_score, 4),
            "handoff_count": len(handoff_items),
            "handoff_items": handoff_items,
            "top_handoff_items": handoff_items[:10],
            "handoff_summary": self._summary(handoff_score, executive_packet, strategic_briefing, handoff_items),
            "q_series_instruction": "Use this packet for evaluation only. Oracle does not execute.",
            "oracle_limits": [
                "Oracle is read-only.",
                "Oracle does not place trades.",
                "Oracle does not approve execution.",
                "Q Series owns execution decisions.",
            ],
        }

        self.last_handoff = packet
        return packet

    def _build_handoff_items(self, digest_items, support_packets):
        support_lookup = {}
        for packet in support_packets:
            market = str(packet.get("market") or "").strip()
            if market:
                support_lookup[market] = packet

        items = []
        seen = set()

        for digest in digest_items:
            market = str(digest.get("market") or "").strip()
            if not market:
                continue

            support = support_lookup.get(market, {})
            handoff_score = self._item_score(digest, support)

            item = {
                "market": market,
                "handoff_score": round(handoff_score, 4),
                "handoff_tier": self._tier(handoff_score),
                "digest_tier": digest.get("digest_tier"),
                "digest_score": self._float(digest.get("digest_score")),
                "support_tier": support.get("support_tier"),
                "support_packet_score": self._float(support.get("support_packet_score")),
                "review_conclusion": support.get("review_conclusion"),
                "oracle_observation": digest.get("oracle_observation") or support.get("oracle_observation"),
                "handoff_note": self._handoff_note(market, digest, support, handoff_score),
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            }
            items.append(item)
            seen.add(market)

        for support in support_packets:
            market = str(support.get("market") or "").strip()
            if not market or market in seen:
                continue

            handoff_score = self._float(support.get("support_packet_score"))
            items.append({
                "market": market,
                "handoff_score": round(handoff_score, 4),
                "handoff_tier": self._tier(handoff_score),
                "digest_tier": None,
                "digest_score": 0.0,
                "support_tier": support.get("support_tier"),
                "support_packet_score": round(handoff_score, 4),
                "review_conclusion": support.get("review_conclusion"),
                "oracle_observation": support.get("oracle_observation"),
                "handoff_note": f"{market} included from decision support packet only.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            })

        items.sort(key=lambda x: x["handoff_score"], reverse=True)

        for idx, item in enumerate(items, start=1):
            item["handoff_rank"] = idx

        return items

    def _item_score(self, digest, support):
        digest_score = self._float(digest.get("digest_score"))
        support_score = self._float(support.get("support_packet_score"))
        alert_count = self._float(digest.get("alert_count"))
        bonus = min(alert_count * 3.0, 9.0)

        if support:
            score = digest_score * 0.55 + support_score * 0.40 + bonus
        else:
            score = digest_score * 0.88 + bonus

        return max(0.0, min(100.0, score))

    def _handoff_score(self, executive_score, strategic_score, handoff_items):
        if not handoff_items:
            return max(0.0, min(100.0, executive_score * 0.50 + strategic_score * 0.50))

        avg_item = sum(x["handoff_score"] for x in handoff_items) / max(1, len(handoff_items))
        top_item = handoff_items[0]["handoff_score"]
        return max(0.0, min(100.0, executive_score * 0.25 + strategic_score * 0.25 + avg_item * 0.25 + top_item * 0.25))

    def _posture(self, score):
        if score >= 85:
            return "urgent_handoff"
        if score >= 70:
            return "priority_handoff"
        if score >= 50:
            return "standard_handoff"
        if score >= 30:
            return "watch_handoff"
        return "low_handoff"

    def _tier(self, score):
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "elevated"
        if score >= 30:
            return "watch"
        return "low"

    def _handoff_note(self, market, digest, support, score):
        return (
            f"{market} handoff tier is {self._tier(score)}. "
            f"Digest tier={digest.get('digest_tier')}; support tier={support.get('support_tier')}. "
            "Oracle read-only packet is ready for Q Series evaluation."
        )

    def _summary(self, handoff_score, executive_packet, strategic_briefing, items):
        counts = {}
        for item in items:
            tier = item["handoff_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = items[0] if items else None
        headline = (
            f"Oracle handoff posture is {self._posture(handoff_score)}."
            if top is None
            else f"Oracle handoff posture is {self._posture(handoff_score)}; top market is {top['market']}."
        )

        return {
            "headline": headline,
            "handoff_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_handoff_tier": top["handoff_tier"] if top else None,
            "executive_posture": executive_packet.get("executive_posture"),
            "strategic_posture": strategic_briefing.get("strategic_posture"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
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
            "has_handoff": bool(self.last_handoff),
            "handoff_count": self.last_handoff.get("handoff_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_intelligence_handoff_engine = OracleIntelligenceHandoffEngine()
