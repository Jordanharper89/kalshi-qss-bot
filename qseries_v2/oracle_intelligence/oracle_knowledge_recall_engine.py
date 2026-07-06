
"""
OI-147 Oracle Knowledge Recall Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle knowledge search results into structured recall packets.
- Recall the highest-value historical knowledge records by market, topic, confidence,
  memory, timeline phase, trend posture, and event catalog.
- Produce concise read-only recall output for downstream Oracle intelligence layers.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleKnowledgeRecallEngine:
    module = "oi_147_oracle_knowledge_recall_engine"

    def __init__(self):
        self.last_recall_report = {}

    def build_recall(
        self,
        knowledge_search_report=None,
        recall_market=None,
        recall_topic=None,
        min_recall_score=None,
        limit=10,
    ):
        knowledge_search_report = knowledge_search_report or {}

        results = [
            x for x in knowledge_search_report.get("knowledge_results", [])
            if isinstance(x, dict)
        ]

        market_filter = self._filter_value(recall_market)
        topic_filter = self._filter_value(recall_topic)
        min_recall_score = self._float(min_recall_score, None)

        recall_packets = []

        for result in results:
            packet = self._recall_packet(result)

            if market_filter and market_filter not in str(packet.get("market") or "").lower():
                continue

            if topic_filter and not self._topic_match(packet, topic_filter):
                continue

            if min_recall_score is not None and packet["recall_score"] < min_recall_score:
                continue

            recall_packets.append(packet)

        recall_packets.sort(
            key=lambda x: (
                x["recall_score"],
                x["knowledge_score"],
                x["market"],
            ),
            reverse=True,
        )

        max_limit = int(self._float(limit, 10))
        if max_limit <= 0:
            max_limit = 10

        recall_packets = recall_packets[:max_limit]

        for idx, packet in enumerate(recall_packets, start=1):
            packet["recall_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_146_oracle_knowledge_search_engine",
                "oi_145_oracle_knowledge_catalog_engine",
            ],
            "recall_filters": {
                "recall_market": recall_market,
                "recall_topic": recall_topic,
                "min_recall_score": min_recall_score,
                "limit": max_limit,
            },
            "source_result_count": len(results),
            "recall_count": len(recall_packets),
            "recall_packets": recall_packets,
            "top_recall_packets": recall_packets[:10],
            "recall_summary": self._summary(recall_packets, len(results)),
            "executive_recall_brief": self._executive_brief(recall_packets),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "oracle_knowledge_recall_context_only",
            },
        }

        self.last_recall_report = report
        return report

    def _recall_packet(self, result):
        market = str(result.get("market") or "UNKNOWN")
        knowledge_score = self._float(result.get("knowledge_score"), 0)
        search_score = self._float(result.get("search_score"), 0)
        event_count = int(self._float(result.get("event_count"), 0))
        topic_count = len(result.get("knowledge_topics", []) or [])
        matched_count = len(result.get("matched_terms", []) or [])

        recall_score = self._recall_score(
            knowledge_score=knowledge_score,
            search_score=search_score,
            event_count=event_count,
            topic_count=topic_count,
            matched_count=matched_count,
        )

        return {
            "market": market,
            "recall_score": round(recall_score, 4),
            "recall_tier": self._tier(recall_score),
            "recall_status": self._status(recall_score, result),
            "knowledge_score": round(knowledge_score, 4),
            "search_score": round(search_score, 4),
            "knowledge_tier": result.get("knowledge_tier"),
            "knowledge_status": result.get("knowledge_status"),
            "timeline_phase": result.get("timeline_phase"),
            "timeline_tier": result.get("timeline_tier"),
            "trend_tier": result.get("trend_tier"),
            "trend_direction": result.get("trend_direction"),
            "confidence_tier": result.get("confidence_tier"),
            "confidence_trajectory": result.get("confidence_trajectory"),
            "memory_tier": result.get("memory_tier"),
            "event_count": event_count,
            "matched_terms": result.get("matched_terms", []),
            "knowledge_topics": result.get("knowledge_topics", []),
            "event_recall": self._event_recall(result.get("event_catalog", [])),
            "recall_note": self._note(market, recall_score, result),
            "read_only": True,
            "execution_allowed": False,
        }

    def _recall_score(self, knowledge_score, search_score, event_count, topic_count, matched_count):
        event_component = min(event_count * 3, 15)
        topic_component = min(topic_count * 1.5, 12)
        match_component = min(matched_count * 4, 16)

        score = (
            knowledge_score * 0.44
            + search_score * 0.32
            + event_component
            + topic_component
            + match_component
        )

        return max(0.0, min(100.0, score))

    def _event_recall(self, event_catalog):
        recalled = []

        for idx, event in enumerate(event_catalog or [], start=1):
            if not isinstance(event, dict):
                continue

            recalled.append({
                "event_recall_id": f"recall-event-{idx:03d}",
                "event_type": event.get("event_type"),
                "event_source": event.get("event_source"),
                "event_score": self._float(event.get("event_score"), 0),
                "event_tier": event.get("event_tier"),
                "event_label": event.get("event_label"),
                "timeline_position": event.get("timeline_position"),
                "recall_weight": self._event_weight(event),
                "read_only": True,
                "execution_allowed": False,
            })

        recalled.sort(
            key=lambda x: (
                x["recall_weight"],
                x["event_score"],
                x["event_type"] or "",
            ),
            reverse=True,
        )

        for idx, event in enumerate(recalled, start=1):
            event["event_recall_rank"] = idx

        return recalled

    def _event_weight(self, event):
        score = self._float(event.get("event_score"), 0)
        event_type = str(event.get("event_type") or "")
        tier = str(event.get("event_tier") or "")

        type_boost = {
            "executive_trend": 12,
            "confidence_evolution": 10,
            "market_memory": 8,
            "archive_record": 6,
        }.get(event_type, 3)

        tier_boost = 0
        if "institutional" in tier or "dominant" in tier:
            tier_boost = 8
        elif "strong" in tier:
            tier_boost = 5
        elif "developing" in tier:
            tier_boost = 3

        return round(max(0.0, min(100.0, score * 0.70 + type_boost + tier_boost)), 4)

    def _tier(self, score):
        if score >= 85:
            return "institutional_recall"
        if score >= 70:
            return "strong_recall"
        if score >= 50:
            return "developing_recall"
        if score >= 30:
            return "thin_recall"
        return "recall_trace"

    def _status(self, score, result):
        knowledge_status = str(result.get("knowledge_status") or "")

        if score >= 85 and knowledge_status == "executive_ready_knowledge":
            return "executive_recall_ready"
        if score >= 70:
            return "recall_ready"
        if score >= 50:
            return "partial_recall"
        return "limited_recall"

    def _topic_match(self, packet, topic_filter):
        topics = [str(x).lower() for x in packet.get("knowledge_topics", []) or []]
        terms = [str(x).lower() for x in packet.get("matched_terms", []) or []]
        haystack = " ".join(topics + terms + [
            str(packet.get("knowledge_tier") or "").lower(),
            str(packet.get("knowledge_status") or "").lower(),
            str(packet.get("timeline_phase") or "").lower(),
            str(packet.get("trend_tier") or "").lower(),
            str(packet.get("confidence_tier") or "").lower(),
            str(packet.get("memory_tier") or "").lower(),
        ])

        return topic_filter in haystack

    def _note(self, market, score, result):
        return (
            f"{market} recall score is {round(score, 2)} from knowledge tier "
            f"{result.get('knowledge_tier')} and search score {result.get('search_score')}. "
            "Oracle recall is read-only context only; Q Series owns execution."
        )

    def _summary(self, packets, source_count):
        tier_counts = {}
        status_counts = {}
        market_counts = {}

        for packet in packets:
            tier = packet["recall_tier"]
            status = packet["recall_status"]
            market = packet["market"]

            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
            market_counts[market] = market_counts.get(market, 0) + 1

        top = packets[0] if packets else None

        return {
            "source_result_count": source_count,
            "recall_count": len(packets),
            "recall_tier_counts": tier_counts,
            "recall_status_counts": status_counts,
            "market_counts": market_counts,
            "top_market": top["market"] if top else None,
            "top_recall_tier": top["recall_tier"] if top else None,
            "top_recall_score": top["recall_score"] if top else None,
            "institutional_recall_count": tier_counts.get("institutional_recall", 0),
            "execution_allowed": False,
            "read_only": True,
        }

    def _executive_brief(self, packets):
        top = packets[0] if packets else None

        if top:
            headline = (
                f"Top Oracle recall is {top['market']} with status "
                f"{top['recall_status']} and tier {top['recall_tier']}."
            )
        else:
            headline = "No Oracle knowledge recall packets available."

        return {
            "headline": headline,
            "top_market": top["market"] if top else None,
            "top_status": top["recall_status"] if top else None,
            "top_tier": top["recall_tier"] if top else None,
            "recall_count": len(packets),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
        }

    def _filter_value(self, value):
        if value is None:
            return None
        clean = str(value).lower().strip()
        return clean or None

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
            "has_recall_report": bool(self.last_recall_report),
            "recall_count": self.last_recall_report.get("recall_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_knowledge_recall_engine = OracleKnowledgeRecallEngine()
