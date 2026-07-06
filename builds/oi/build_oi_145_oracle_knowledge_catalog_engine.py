from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_knowledge_catalog_engine.py"
TEST = ROOT / "test_oi_145_oracle_knowledge_catalog_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-145 Oracle Knowledge Catalog Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle timeline intelligence into a searchable knowledge catalog.
- Catalog market timelines, events, confidence states, memory states, trend states,
  archive references, and executive timeline briefs.
- Produce institutional read-only knowledge records for downstream Oracle intelligence.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleKnowledgeCatalogEngine:
    module = "oi_145_oracle_knowledge_catalog_engine"

    def __init__(self):
        self.last_knowledge_catalog = {}

    def build_knowledge_catalog(
        self,
        timeline_report=None,
        trend_report=None,
        confidence_evolution_report=None,
        memory_report=None,
    ):
        timeline_report = timeline_report or {}
        trend_report = trend_report or {}
        confidence_evolution_report = confidence_evolution_report or {}
        memory_report = memory_report or {}

        timelines = [
            x for x in timeline_report.get("market_timelines", [])
            if isinstance(x, dict)
        ]
        trend_cards = [
            x for x in trend_report.get("historical_trend_cards", [])
            if isinstance(x, dict)
        ]
        evolution_packets = [
            x for x in confidence_evolution_report.get("confidence_evolution_packets", [])
            if isinstance(x, dict)
        ]
        memory_profiles = [
            x for x in memory_report.get("market_memory_profiles", [])
            if isinstance(x, dict)
        ]

        trend_index = self._index_one(trend_cards, "market")
        evolution_index = self._index_one(evolution_packets, "market")
        memory_index = self._index_one(memory_profiles, "market")

        knowledge_records = []
        for timeline in timelines:
            market = str(timeline.get("market") or "UNKNOWN")
            record = self._knowledge_record(
                timeline=timeline,
                trend=trend_index.get(market, {}),
                evolution=evolution_index.get(market, {}),
                memory=memory_index.get(market, {}),
            )
            knowledge_records.append(record)

        knowledge_records.sort(
            key=lambda x: (
                x["knowledge_score"],
                x["event_count"],
                x["market"],
            ),
            reverse=True,
        )

        for idx, record in enumerate(knowledge_records, start=1):
            record["knowledge_rank"] = idx

        catalog = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_144_oracle_timeline_intelligence_engine",
                "oi_143_executive_historical_trend_engine",
                "oi_142_historical_confidence_evolution_engine",
                "oi_140_oracle_market_memory_engine",
            ],
            "knowledge_record_count": len(knowledge_records),
            "knowledge_records": knowledge_records,
            "top_knowledge_records": knowledge_records[:10],
            "knowledge_summary": self._summary(knowledge_records),
            "executive_knowledge_brief": self._executive_brief(knowledge_records),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "oracle_knowledge_catalog_context_only",
            },
        }

        self.last_knowledge_catalog = catalog
        return catalog

    def _knowledge_record(self, timeline, trend, evolution, memory):
        market = str(timeline.get("market") or "UNKNOWN")
        timeline_score = self._float(timeline.get("timeline_score"), 0)
        trend_score = self._float(trend.get("trend_score"), 0)
        evolved_confidence = self._float(evolution.get("evolved_confidence"), 0)
        memory_strength = self._float(memory.get("memory_strength"), 0)
        event_count = int(self._float(timeline.get("event_count"), 0))

        knowledge_score = self._knowledge_score(
            timeline_score=timeline_score,
            trend_score=trend_score,
            evolved_confidence=evolved_confidence,
            memory_strength=memory_strength,
            event_count=event_count,
        )

        events = [
            x for x in timeline.get("timeline_events", [])
            if isinstance(x, dict)
        ]

        return {
            "market": market,
            "knowledge_score": round(knowledge_score, 4),
            "knowledge_tier": self._tier(knowledge_score),
            "knowledge_status": self._status(knowledge_score, timeline),
            "timeline_score": round(timeline_score, 4),
            "timeline_tier": timeline.get("timeline_tier"),
            "timeline_phase": timeline.get("timeline_phase"),
            "trend_score": round(trend_score, 4),
            "trend_tier": trend.get("trend_tier"),
            "trend_direction": trend.get("trend_direction"),
            "executive_trend_posture": trend.get("executive_trend_posture"),
            "evolved_confidence": round(evolved_confidence, 4),
            "confidence_tier": evolution.get("confidence_tier"),
            "confidence_trajectory": evolution.get("confidence_trajectory"),
            "memory_strength": round(memory_strength, 4),
            "memory_tier": memory.get("memory_tier"),
            "event_count": event_count,
            "knowledge_topics": self._topics(timeline, trend, evolution, memory),
            "knowledge_terms": self._terms(market, timeline, trend, evolution, memory, events),
            "knowledge_note": self._note(market, knowledge_score, timeline),
            "event_catalog": self._event_catalog(events),
            "read_only": True,
            "execution_allowed": False,
        }

    def _knowledge_score(self, timeline_score, trend_score, evolved_confidence, memory_strength, event_count):
        event_component = min(event_count * 4, 18)
        score = (
            timeline_score * 0.34
            + trend_score * 0.24
            + evolved_confidence * 0.20
            + memory_strength * 0.12
            + event_component
        )
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "institutional_knowledge"
        if score >= 70:
            return "strong_knowledge"
        if score >= 50:
            return "developing_knowledge"
        if score >= 30:
            return "thin_knowledge"
        return "knowledge_trace"

    def _status(self, score, timeline):
        phase = str(timeline.get("timeline_phase") or "")

        if score >= 85 and phase == "executive_timeline_active":
            return "executive_ready_knowledge"
        if score >= 70:
            return "catalog_ready"
        if score >= 50:
            return "developing_catalog"
        return "archive_reference_only"

    def _topics(self, timeline, trend, evolution, memory):
        topics = []

        for value in [
            timeline.get("timeline_phase"),
            timeline.get("timeline_tier"),
            trend.get("trend_tier"),
            trend.get("trend_direction"),
            trend.get("executive_trend_posture"),
            evolution.get("confidence_tier"),
            evolution.get("confidence_trajectory"),
            memory.get("memory_tier"),
        ]:
            if value and value not in topics:
                topics.append(value)

        return topics

    def _terms(self, market, timeline, trend, evolution, memory, events):
        terms = {str(market).lower()}

        for source in [timeline, trend, evolution, memory]:
            for key in [
                "timeline_tier",
                "timeline_phase",
                "trend_tier",
                "trend_direction",
                "executive_trend_posture",
                "confidence_tier",
                "confidence_trajectory",
                "memory_tier",
                "case_id",
                "case_type",
            ]:
                value = source.get(key) if isinstance(source, dict) else None
                if value is not None:
                    terms.add(str(value).lower())

        for event in events:
            for key in [
                "event_type",
                "event_source",
                "event_tier",
                "event_label",
            ]:
                value = event.get(key)
                if value is not None:
                    terms.add(str(value).lower())

            source_keys = event.get("source_keys", {}) or {}
            if isinstance(source_keys, dict):
                for value in source_keys.values():
                    if value is not None:
                        terms.add(str(value).lower())

        return sorted(x for x in terms if x and x != "none")

    def _event_catalog(self, events):
        catalog = []

        for idx, event in enumerate(events, start=1):
            catalog.append({
                "event_catalog_id": f"event-{idx:03d}",
                "event_type": event.get("event_type"),
                "event_source": event.get("event_source"),
                "event_score": self._float(event.get("event_score"), 0),
                "event_tier": event.get("event_tier"),
                "event_label": event.get("event_label"),
                "timeline_position": event.get("timeline_position"),
                "read_only": True,
                "execution_allowed": False,
            })

        return catalog

    def _note(self, market, score, timeline):
        return (
            f"{market} knowledge catalog score is {round(score, 2)} with timeline "
            f"phase {timeline.get('timeline_phase')} and tier {timeline.get('timeline_tier')}. "
            "Oracle knowledge catalog is read-only context only; Q Series owns execution."
        )

    def _summary(self, records):
        tier_counts = {}
        status_counts = {}
        topic_counts = {}

        for record in records:
            tier = record["knowledge_tier"]
            status = record["knowledge_status"]

            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1

            for topic in record.get("knowledge_topics", []) or []:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        top = records[0] if records else None

        return {
            "knowledge_record_count": len(records),
            "knowledge_tier_counts": tier_counts,
            "knowledge_status_counts": status_counts,
            "topic_counts": topic_counts,
            "top_market": top["market"] if top else None,
            "top_knowledge_tier": top["knowledge_tier"] if top else None,
            "top_knowledge_score": top["knowledge_score"] if top else None,
            "institutional_knowledge_count": tier_counts.get("institutional_knowledge", 0),
            "execution_allowed": False,
            "read_only": True,
        }

    def _executive_brief(self, records):
        top = records[0] if records else None

        if top:
            headline = (
                f"Top Oracle knowledge record is {top['market']} with status "
                f"{top['knowledge_status']} and tier {top['knowledge_tier']}."
            )
        else:
            headline = "No Oracle knowledge records available."

        return {
            "headline": headline,
            "top_market": top["market"] if top else None,
            "top_status": top["knowledge_status"] if top else None,
            "top_tier": top["knowledge_tier"] if top else None,
            "knowledge_record_count": len(records),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
        }

    def _index_one(self, rows, key):
        out = {}
        for row in rows:
            value = str(row.get(key) or "UNKNOWN")
            if value not in out:
                out[value] = row
        return out

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
            "has_knowledge_catalog": bool(self.last_knowledge_catalog),
            "knowledge_record_count": self.last_knowledge_catalog.get("knowledge_record_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_knowledge_catalog_engine = OracleKnowledgeCatalogEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_knowledge_catalog_engine import (
    oracle_knowledge_catalog_engine,
)


def test_oi_145_oracle_knowledge_catalog_engine():
    timeline = {
        "market_timelines": [
            {
                "market": "CRYPTO",
                "timeline_score": 100,
                "timeline_tier": "institutional_timeline",
                "timeline_phase": "executive_timeline_active",
                "event_count": 4,
                "timeline_events": [
                    {
                        "event_type": "confidence_evolution",
                        "event_source": "confidence",
                        "event_score": 89.175,
                        "event_tier": "institutional_confidence",
                        "event_label": "stable",
                        "timeline_position": 1,
                        "source_keys": {
                            "case_id": "case-crypto-001",
                            "market": "CRYPTO",
                            "confidence_tier": "institutional_confidence",
                        },
                        "read_only": True,
                        "execution_allowed": False,
                    },
                    {
                        "event_type": "executive_trend",
                        "event_source": "trend",
                        "event_score": 89.4486,
                        "event_tier": "dominant_historical_trend",
                        "event_label": "executive_priority_watch",
                        "timeline_position": 2,
                        "source_keys": {
                            "case_id": "case-crypto-001",
                            "market": "CRYPTO",
                            "trend_tier": "dominant_historical_trend",
                        },
                        "read_only": True,
                        "execution_allowed": False,
                    },
                ],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "timeline_score": 72,
                "timeline_tier": "strong_timeline",
                "timeline_phase": "archive_phase",
                "event_count": 2,
                "timeline_events": [],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    trends = {
        "historical_trend_cards": [
            {
                "market": "CRYPTO",
                "trend_score": 89.4486,
                "trend_tier": "dominant_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "executive_priority_watch",
                "case_id": "case-crypto-001",
                "case_type": "digest_snapshot",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "trend_score": 58.2,
                "trend_tier": "developing_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "standard_historical_review",
                "case_id": "case-nasdaq-001",
                "case_type": "strategic_briefing",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    evolution = {
        "confidence_evolution_packets": [
            {
                "market": "CRYPTO",
                "case_id": "case-crypto-001",
                "case_type": "digest_snapshot",
                "evolved_confidence": 89.175,
                "confidence_tier": "institutional_confidence",
                "confidence_trajectory": "stable",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "case_id": "case-nasdaq-001",
                "case_type": "strategic_briefing",
                "evolved_confidence": 72.015,
                "confidence_tier": "strong_confidence",
                "confidence_trajectory": "stable",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    memory = {
        "market_memory_profiles": [
            {
                "market": "CRYPTO",
                "memory_strength": 92.62,
                "memory_tier": "institutional_memory",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "memory_strength": 56.1,
                "memory_tier": "developing_memory",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = oracle_knowledge_catalog_engine.build_knowledge_catalog(
        timeline,
        trends,
        evolution,
        memory,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["knowledge_record_count"] == 2
    assert report["knowledge_records"][0]["knowledge_rank"] == 1
    assert report["knowledge_records"][0]["market"] == "CRYPTO"
    assert report["knowledge_records"][0]["knowledge_status"] == "executive_ready_knowledge"
    assert report["knowledge_records"][0]["execution_allowed"] is False
    assert report["knowledge_records"][0]["read_only"] is True
    assert report["knowledge_records"][0]["event_catalog"][0]["execution_allowed"] is False
    assert report["knowledge_summary"]["execution_allowed"] is False
    assert report["knowledge_summary"]["read_only"] is True
    assert report["executive_knowledge_brief"]["execution_allowed"] is False
    assert report["executive_knowledge_brief"]["execution_owner"] == "Q Series"

    diag = oracle_knowledge_catalog_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["knowledge_record_count"] == report["knowledge_record_count"]

    print("[PASS] OI-145 Oracle Knowledge Catalog Engine")
    print({
        "knowledge_record_count": report["knowledge_record_count"],
        "summary": report["knowledge_summary"],
        "brief": report["executive_knowledge_brief"],
        "top": report["knowledge_records"][0],
    })


if __name__ == "__main__":
    test_oi_145_oracle_knowledge_catalog_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_knowledge_catalog_engine import oracle_knowledge_catalog_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-145 INSTALLER")
print(" Oracle Knowledge Catalog Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-145 installed")
print()
print("Run:")
print("py test_oi_145_oracle_knowledge_catalog_engine.py")