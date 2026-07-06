from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_timeline_intelligence_engine.py"
TEST = ROOT / "test_oi_144_oracle_timeline_intelligence_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-144 Oracle Timeline Intelligence Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert executive historical trends, confidence evolution, market memory, and archive
  records into timeline intelligence.
- Build chronological market timelines with trend phase, confidence phase,
  memory phase, and archive phase snapshots.
- Produce read-only timeline packets for downstream knowledge cataloging.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleTimelineIntelligenceEngine:
    module = "oi_144_oracle_timeline_intelligence_engine"

    def __init__(self):
        self.last_timeline_report = {}

    def build_timeline(
        self,
        trend_report=None,
        confidence_evolution_report=None,
        memory_report=None,
        catalog_report=None,
    ):
        trend_report = trend_report or {}
        confidence_evolution_report = confidence_evolution_report or {}
        memory_report = memory_report or {}
        catalog_report = catalog_report or {}

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
        catalog_records = [
            x for x in catalog_report.get("catalog_records", [])
            if isinstance(x, dict)
        ]

        trend_index = self._index_list(trend_cards, "market")
        evolution_index = self._index_list(evolution_packets, "market")
        memory_index = self._index_list(memory_profiles, "market")
        catalog_index = self._index_list(catalog_records, "market")

        markets = self._markets(trend_cards, evolution_packets, memory_profiles, catalog_records)

        timelines = []
        for market in markets:
            timeline = self._market_timeline(
                market=market,
                trend_cards=trend_index.get(market, []),
                evolution_packets=evolution_index.get(market, []),
                memory_profiles=memory_index.get(market, []),
                catalog_records=catalog_index.get(market, []),
            )
            timelines.append(timeline)

        timelines.sort(
            key=lambda x: (
                x["timeline_score"],
                x["event_count"],
                x["market"],
            ),
            reverse=True,
        )

        for idx, timeline in enumerate(timelines, start=1):
            timeline["timeline_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_143_executive_historical_trend_engine",
                "oi_142_historical_confidence_evolution_engine",
                "oi_140_oracle_market_memory_engine",
                "oi_137_q_series_visibility_archive_catalog_engine",
            ],
            "timeline_count": len(timelines),
            "market_timelines": timelines,
            "top_timelines": timelines[:10],
            "timeline_summary": self._summary(timelines),
            "executive_timeline_brief": self._executive_brief(timelines),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "timeline_intelligence_context_only",
            },
        }

        self.last_timeline_report = report
        return report

    def _market_timeline(self, market, trend_cards, evolution_packets, memory_profiles, catalog_records):
        events = []

        for record in catalog_records:
            events.append(self._event(
                market=market,
                event_type="archive_record",
                source="catalog",
                timestamp=self._float(record.get("archive_timestamp"), 0),
                score=self._float(record.get("catalog_priority"), 0),
                tier=record.get("catalog_tier"),
                label=record.get("catalog_label") or record.get("archive_type"),
                payload=record,
            ))

        for memory in memory_profiles:
            events.append(self._event(
                market=market,
                event_type="market_memory",
                source="memory",
                timestamp=self._float(memory.get("timestamp"), 0),
                score=self._float(memory.get("memory_strength"), 0),
                tier=memory.get("memory_tier"),
                label=memory.get("historical_signature", {}).get("signature_label") if isinstance(memory.get("historical_signature"), dict) else "market_memory",
                payload=memory,
            ))

        for evolution in evolution_packets:
            events.append(self._event(
                market=market,
                event_type="confidence_evolution",
                source="confidence",
                timestamp=self._float(evolution.get("timestamp"), 0),
                score=self._float(evolution.get("evolved_confidence"), 0),
                tier=evolution.get("confidence_tier"),
                label=evolution.get("confidence_trajectory"),
                payload=evolution,
            ))

        for trend in trend_cards:
            events.append(self._event(
                market=market,
                event_type="executive_trend",
                source="trend",
                timestamp=self._float(trend.get("timestamp"), 0),
                score=self._float(trend.get("trend_score"), 0),
                tier=trend.get("trend_tier"),
                label=trend.get("executive_trend_posture"),
                payload=trend,
            ))

        events.sort(
            key=lambda x: (
                x["event_timestamp"],
                x["event_score"],
                x["event_type"],
            )
        )

        for idx, event in enumerate(events, start=1):
            event["timeline_position"] = idx

        timeline_score = self._timeline_score(events)
        phase = self._phase(events, timeline_score)

        return {
            "market": market,
            "timeline_score": round(timeline_score, 4),
            "timeline_tier": self._tier(timeline_score),
            "timeline_phase": phase,
            "event_count": len(events),
            "archive_event_count": len([x for x in events if x["event_type"] == "archive_record"]),
            "memory_event_count": len([x for x in events if x["event_type"] == "market_memory"]),
            "confidence_event_count": len([x for x in events if x["event_type"] == "confidence_evolution"]),
            "trend_event_count": len([x for x in events if x["event_type"] == "executive_trend"]),
            "first_event_timestamp": events[0]["event_timestamp"] if events else None,
            "latest_event_timestamp": events[-1]["event_timestamp"] if events else None,
            "timeline_events": events,
            "timeline_note": self._note(market, timeline_score, phase, len(events)),
            "read_only": True,
            "execution_allowed": False,
        }

    def _event(self, market, event_type, source, timestamp, score, tier, label, payload):
        return {
            "market": market,
            "event_type": event_type,
            "event_source": source,
            "event_timestamp": timestamp,
            "event_score": round(score, 4),
            "event_tier": tier,
            "event_label": label,
            "event_summary": self._event_summary(market, event_type, score, tier, label),
            "source_keys": self._source_keys(payload),
            "read_only": True,
            "execution_allowed": False,
        }

    def _event_summary(self, market, event_type, score, tier, label):
        return (
            f"{market} timeline event {event_type} recorded with score "
            f"{round(score, 2)}, tier {tier}, label {label}. Oracle timeline "
            "intelligence is read-only context for Q Series."
        )

    def _source_keys(self, payload):
        if not isinstance(payload, dict):
            return {}

        keys = {}
        for key in [
            "case_id",
            "catalog_key",
            "archive_id",
            "receipt_id",
            "market",
            "archive_type",
            "trend_tier",
            "confidence_tier",
            "memory_tier",
            "catalog_tier",
        ]:
            if key in payload:
                keys[key] = payload.get(key)
        return keys

    def _timeline_score(self, events):
        if not events:
            return 0.0

        avg_score = sum(self._float(x.get("event_score"), 0) for x in events) / len(events)
        diversity = len(set(x.get("event_type") for x in events))
        diversity_boost = min(diversity * 5, 20)
        event_boost = min(len(events) * 3, 18)
        latest_score = self._float(events[-1].get("event_score"), 0) if events else 0

        score = avg_score * 0.58 + latest_score * 0.18 + diversity_boost + event_boost
        return max(0.0, min(100.0, score))

    def _phase(self, events, score):
        event_types = {x.get("event_type") for x in events}
        latest = events[-1] if events else {}
        latest_type = latest.get("event_type")

        if score >= 85 and "executive_trend" in event_types:
            return "executive_timeline_active"
        if latest_type == "confidence_evolution":
            return "confidence_phase"
        if latest_type == "market_memory":
            return "memory_phase"
        if latest_type == "archive_record":
            return "archive_phase"
        if event_types:
            return "historical_context_phase"
        return "empty_timeline"

    def _tier(self, score):
        if score >= 85:
            return "institutional_timeline"
        if score >= 70:
            return "strong_timeline"
        if score >= 50:
            return "developing_timeline"
        if score >= 30:
            return "thin_timeline"
        return "timeline_trace"

    def _note(self, market, score, phase, event_count):
        return (
            f"{market} timeline has {event_count} event(s), score {round(score, 2)}, "
            f"and phase {phase}. Oracle provides timeline intelligence only; "
            "Q Series owns execution decisions."
        )

    def _summary(self, timelines):
        tier_counts = {}
        phase_counts = {}

        for timeline in timelines:
            tier = timeline["timeline_tier"]
            phase = timeline["timeline_phase"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

        top = timelines[0] if timelines else None

        return {
            "timeline_count": len(timelines),
            "timeline_tier_counts": tier_counts,
            "timeline_phase_counts": phase_counts,
            "top_market": top["market"] if top else None,
            "top_timeline_tier": top["timeline_tier"] if top else None,
            "top_timeline_score": top["timeline_score"] if top else None,
            "institutional_timeline_count": tier_counts.get("institutional_timeline", 0),
            "execution_allowed": False,
            "read_only": True,
        }

    def _executive_brief(self, timelines):
        top = timelines[0] if timelines else None

        if top:
            headline = (
                f"Top Oracle timeline is {top['market']} with phase "
                f"{top['timeline_phase']} and tier {top['timeline_tier']}."
            )
        else:
            headline = "No Oracle historical timeline available."

        return {
            "headline": headline,
            "top_market": top["market"] if top else None,
            "top_phase": top["timeline_phase"] if top else None,
            "top_tier": top["timeline_tier"] if top else None,
            "timeline_count": len(timelines),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
        }

    def _markets(self, *groups):
        markets = []
        for group in groups:
            for row in group:
                if isinstance(row, dict):
                    market = str(row.get("market") or "UNKNOWN")
                    if market not in markets:
                        markets.append(market)

        if not markets:
            markets.append("UNKNOWN")

        return markets

    def _index_list(self, rows, key):
        out = {}
        for row in rows:
            value = str(row.get(key) or "UNKNOWN")
            out.setdefault(value, []).append(row)
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
            "has_timeline_report": bool(self.last_timeline_report),
            "timeline_count": self.last_timeline_report.get("timeline_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_timeline_intelligence_engine = OracleTimelineIntelligenceEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_timeline_intelligence_engine import (
    oracle_timeline_intelligence_engine,
)


def test_oi_144_oracle_timeline_intelligence_engine():
    trends = {
        "historical_trend_cards": [
            {
                "market": "CRYPTO",
                "case_id": "case-crypto-001",
                "case_type": "digest_snapshot",
                "trend_score": 89.4486,
                "trend_tier": "dominant_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "executive_priority_watch",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "case_id": "case-nasdaq-001",
                "case_type": "strategic_briefing",
                "trend_score": 58.2,
                "trend_tier": "developing_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "standard_historical_review",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    evolution = {
        "confidence_evolution_packets": [
            {
                "case_id": "case-crypto-001",
                "market": "CRYPTO",
                "case_type": "digest_snapshot",
                "evolved_confidence": 89.175,
                "confidence_tier": "institutional_confidence",
                "confidence_trajectory": "stable",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "case_id": "case-nasdaq-001",
                "market": "NASDAQ",
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
                "historical_signature": {
                    "signature_label": "CRYPTO memory signature: digest_snapshot / market_visibility"
                },
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "memory_strength": 56.1,
                "memory_tier": "developing_memory",
                "historical_signature": {
                    "signature_label": "NASDAQ memory signature: strategic_briefing / market_visibility"
                },
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    catalog = {
        "catalog_records": [
            {
                "catalog_key": "arc-001",
                "archive_id": "arc-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "catalog_priority": 94,
                "catalog_tier": "institutional_priority",
                "catalog_label": "CRYPTO digest_snapshot catalog record",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "catalog_key": "arc-002",
                "archive_id": "arc-002",
                "market": "NASDAQ",
                "archive_type": "strategic_briefing",
                "archive_timestamp": 1799999000,
                "catalog_priority": 76,
                "catalog_tier": "high_value",
                "catalog_label": "NASDAQ strategic_briefing catalog record",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = oracle_timeline_intelligence_engine.build_timeline(
        trends,
        evolution,
        memory,
        catalog,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["timeline_count"] == 2
    assert report["market_timelines"][0]["timeline_rank"] == 1
    assert report["market_timelines"][0]["market"] == "CRYPTO"
    assert report["market_timelines"][0]["event_count"] == 4
    assert report["market_timelines"][0]["execution_allowed"] is False
    assert report["market_timelines"][0]["read_only"] is True
    assert report["market_timelines"][0]["timeline_events"][0]["execution_allowed"] is False
    assert report["timeline_summary"]["execution_allowed"] is False
    assert report["timeline_summary"]["read_only"] is True
    assert report["executive_timeline_brief"]["execution_allowed"] is False
    assert report["executive_timeline_brief"]["execution_owner"] == "Q Series"

    diag = oracle_timeline_intelligence_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["timeline_count"] == report["timeline_count"]

    print("[PASS] OI-144 Oracle Timeline Intelligence Engine")
    print({
        "timeline_count": report["timeline_count"],
        "summary": report["timeline_summary"],
        "brief": report["executive_timeline_brief"],
        "top": report["market_timelines"][0],
    })


if __name__ == "__main__":
    test_oi_144_oracle_timeline_intelligence_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_timeline_intelligence_engine import oracle_timeline_intelligence_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-144 INSTALLER")
print(" Oracle Timeline Intelligence Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-144 installed")
print()
print("Run:")
print("py test_oi_144_oracle_timeline_intelligence_engine.py")