from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_knowledge_search_engine.py"
TEST = ROOT / "test_oi_146_oracle_knowledge_search_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-146 Oracle Knowledge Search Engine
Read-only Oracle Intelligence module.

Purpose:
- Search Oracle knowledge catalog records.
- Support keyword, market, topic, tier, status, minimum score, and event-type filters.
- Produce ranked read-only knowledge search results for downstream historical recall.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleKnowledgeSearchEngine:
    module = "oi_146_oracle_knowledge_search_engine"

    def __init__(self):
        self.last_search_report = {}

    def search_knowledge(
        self,
        knowledge_catalog=None,
        query=None,
        market=None,
        topic=None,
        tier=None,
        status=None,
        event_type=None,
        min_score=None,
        limit=25,
    ):
        knowledge_catalog = knowledge_catalog or {}
        records = [
            x for x in knowledge_catalog.get("knowledge_records", [])
            if isinstance(x, dict)
        ]

        query_terms = self._query_terms(query)
        market_filter = self._filter_value(market)
        topic_filter = self._filter_value(topic)
        tier_filter = self._filter_value(tier)
        status_filter = self._filter_value(status)
        event_type_filter = self._filter_value(event_type)
        min_score = self._float(min_score, None)

        results = []
        for record in records:
            if not self._matches(
                record=record,
                query_terms=query_terms,
                market_filter=market_filter,
                topic_filter=topic_filter,
                tier_filter=tier_filter,
                status_filter=status_filter,
                event_type_filter=event_type_filter,
                min_score=min_score,
            ):
                continue

            search_score = self._search_score(
                record=record,
                query_terms=query_terms,
                market_filter=market_filter,
                topic_filter=topic_filter,
                tier_filter=tier_filter,
                status_filter=status_filter,
                event_type_filter=event_type_filter,
            )

            results.append(self._result_record(record, search_score, query_terms))

        results.sort(
            key=lambda x: (
                x["search_score"],
                x["knowledge_score"],
                x["market"],
            ),
            reverse=True,
        )

        max_limit = int(self._float(limit, 25))
        if max_limit <= 0:
            max_limit = 25

        results = results[:max_limit]

        for idx, result in enumerate(results, start=1):
            result["knowledge_search_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_145_oracle_knowledge_catalog_engine",
            ],
            "query": query,
            "filters": {
                "market": market,
                "topic": topic,
                "tier": tier,
                "status": status,
                "event_type": event_type,
                "min_score": min_score,
                "limit": max_limit,
            },
            "searched_record_count": len(records),
            "result_count": len(results),
            "knowledge_results": results,
            "top_knowledge_results": results[:10],
            "knowledge_search_summary": self._summary(results, len(records), query_terms),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "oracle_knowledge_search_context_only",
            },
        }

        self.last_search_report = report
        return report

    def _matches(
        self,
        record,
        query_terms,
        market_filter,
        topic_filter,
        tier_filter,
        status_filter,
        event_type_filter,
        min_score,
    ):
        haystack = self._haystack(record)

        if query_terms and not all(term in haystack for term in query_terms):
            return False

        if market_filter and market_filter not in str(record.get("market") or "").lower():
            return False

        if topic_filter:
            topics = [str(x).lower() for x in record.get("knowledge_topics", []) or []]
            if topic_filter not in topics and topic_filter not in haystack:
                return False

        if tier_filter and tier_filter != str(record.get("knowledge_tier") or "").lower():
            return False

        if status_filter and status_filter != str(record.get("knowledge_status") or "").lower():
            return False

        if event_type_filter:
            event_types = [
                str(x.get("event_type") or "").lower()
                for x in record.get("event_catalog", []) or []
                if isinstance(x, dict)
            ]
            if event_type_filter not in event_types:
                return False

        if min_score is not None and self._float(record.get("knowledge_score"), 0) < min_score:
            return False

        return True

    def _search_score(
        self,
        record,
        query_terms,
        market_filter,
        topic_filter,
        tier_filter,
        status_filter,
        event_type_filter,
    ):
        knowledge_score = self._float(record.get("knowledge_score"), 0)
        timeline_score = self._float(record.get("timeline_score"), 0)
        confidence = self._float(record.get("evolved_confidence"), 0)
        memory_strength = self._float(record.get("memory_strength"), 0)

        score = (
            knowledge_score * 0.48
            + timeline_score * 0.18
            + confidence * 0.14
            + memory_strength * 0.10
        )

        haystack = self._haystack(record)
        knowledge_terms = [str(x).lower() for x in record.get("knowledge_terms", []) or []]
        knowledge_topics = [str(x).lower() for x in record.get("knowledge_topics", []) or []]

        for term in query_terms:
            if term in knowledge_terms:
                score += 7
            elif term in knowledge_topics:
                score += 6
            elif term in haystack:
                score += 3

        if market_filter and market_filter == str(record.get("market") or "").lower():
            score += 6
        if topic_filter and topic_filter in knowledge_topics:
            score += 5
        if tier_filter and tier_filter == str(record.get("knowledge_tier") or "").lower():
            score += 4
        if status_filter and status_filter == str(record.get("knowledge_status") or "").lower():
            score += 4
        if event_type_filter:
            score += 4

        return round(max(0.0, min(100.0, score)), 4)

    def _result_record(self, record, search_score, query_terms):
        return {
            "market": record.get("market"),
            "knowledge_score": self._float(record.get("knowledge_score"), 0),
            "search_score": search_score,
            "knowledge_tier": record.get("knowledge_tier"),
            "knowledge_status": record.get("knowledge_status"),
            "timeline_phase": record.get("timeline_phase"),
            "timeline_tier": record.get("timeline_tier"),
            "trend_tier": record.get("trend_tier"),
            "trend_direction": record.get("trend_direction"),
            "confidence_tier": record.get("confidence_tier"),
            "confidence_trajectory": record.get("confidence_trajectory"),
            "memory_tier": record.get("memory_tier"),
            "event_count": record.get("event_count"),
            "matched_terms": self._match_terms(record, query_terms),
            "knowledge_topics": record.get("knowledge_topics", []),
            "knowledge_note": record.get("knowledge_note"),
            "event_catalog": record.get("event_catalog", []),
            "read_only": True,
            "execution_allowed": False,
        }

    def _summary(self, results, searched_count, query_terms):
        tier_counts = {}
        status_counts = {}
        market_counts = {}

        for result in results:
            tier = result.get("knowledge_tier")
            status = result.get("knowledge_status")
            market = result.get("market")

            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
            market_counts[market] = market_counts.get(market, 0) + 1

        top = results[0] if results else None

        return {
            "searched_record_count": searched_count,
            "result_count": len(results),
            "query_terms": query_terms,
            "knowledge_tier_counts": tier_counts,
            "knowledge_status_counts": status_counts,
            "market_counts": market_counts,
            "top_market": top.get("market") if top else None,
            "top_search_score": top.get("search_score") if top else None,
            "top_knowledge_tier": top.get("knowledge_tier") if top else None,
            "execution_allowed": False,
            "read_only": True,
        }

    def _match_terms(self, record, query_terms):
        if not query_terms:
            return []

        haystack = self._haystack(record)
        return [term for term in query_terms if term in haystack]

    def _haystack(self, record):
        pieces = []

        for key in [
            "market",
            "knowledge_tier",
            "knowledge_status",
            "timeline_tier",
            "timeline_phase",
            "trend_tier",
            "trend_direction",
            "executive_trend_posture",
            "confidence_tier",
            "confidence_trajectory",
            "memory_tier",
            "knowledge_note",
        ]:
            value = record.get(key)
            if value is not None:
                pieces.append(str(value).lower())

        for field in ["knowledge_topics", "knowledge_terms"]:
            for value in record.get(field, []) or []:
                pieces.append(str(value).lower())

        for event in record.get("event_catalog", []) or []:
            if not isinstance(event, dict):
                continue
            for key in ["event_type", "event_source", "event_tier", "event_label"]:
                value = event.get(key)
                if value is not None:
                    pieces.append(str(value).lower())

        return " ".join(pieces)

    def _query_terms(self, query):
        if query is None:
            return []
        if isinstance(query, list):
            raw = []
            for item in query:
                raw.extend(str(item).lower().replace(",", " ").split())
        else:
            raw = str(query).lower().replace(",", " ").split()

        return sorted(set(x.strip() for x in raw if x.strip()))

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
            "has_search_report": bool(self.last_search_report),
            "result_count": self.last_search_report.get("result_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_knowledge_search_engine = OracleKnowledgeSearchEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_knowledge_search_engine import (
    oracle_knowledge_search_engine,
)


def test_oi_146_oracle_knowledge_search_engine():
    catalog = {
        "knowledge_records": [
            {
                "market": "CRYPTO",
                "knowledge_score": 100,
                "knowledge_tier": "institutional_knowledge",
                "knowledge_status": "executive_ready_knowledge",
                "timeline_score": 100,
                "timeline_tier": "institutional_timeline",
                "timeline_phase": "executive_timeline_active",
                "trend_tier": "dominant_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "executive_priority_watch",
                "evolved_confidence": 89.175,
                "confidence_tier": "institutional_confidence",
                "confidence_trajectory": "stable",
                "memory_strength": 92.62,
                "memory_tier": "institutional_memory",
                "event_count": 4,
                "knowledge_topics": [
                    "executive_timeline_active",
                    "institutional_timeline",
                    "dominant_historical_trend",
                    "stable",
                    "executive_priority_watch",
                    "institutional_confidence",
                    "institutional_memory",
                ],
                "knowledge_terms": [
                    "crypto",
                    "case-crypto-001",
                    "confidence_evolution",
                    "executive_trend",
                    "institutional_confidence",
                    "executive_priority_watch",
                ],
                "knowledge_note": "CRYPTO knowledge catalog score is 100.0.",
                "event_catalog": [
                    {
                        "event_catalog_id": "event-001",
                        "event_type": "confidence_evolution",
                        "event_source": "confidence",
                        "event_score": 89.175,
                        "event_tier": "institutional_confidence",
                        "event_label": "stable",
                        "read_only": True,
                        "execution_allowed": False,
                    },
                    {
                        "event_catalog_id": "event-002",
                        "event_type": "executive_trend",
                        "event_source": "trend",
                        "event_score": 89.4486,
                        "event_tier": "dominant_historical_trend",
                        "event_label": "executive_priority_watch",
                        "read_only": True,
                        "execution_allowed": False,
                    },
                ],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "knowledge_score": 61.8,
                "knowledge_tier": "developing_knowledge",
                "knowledge_status": "developing_catalog",
                "timeline_score": 72,
                "timeline_tier": "strong_timeline",
                "timeline_phase": "archive_phase",
                "trend_tier": "developing_historical_trend",
                "trend_direction": "stable",
                "evolved_confidence": 72.015,
                "confidence_tier": "strong_confidence",
                "memory_strength": 56.1,
                "memory_tier": "developing_memory",
                "event_count": 2,
                "knowledge_topics": ["archive_phase", "strong_timeline", "stable"],
                "knowledge_terms": ["nasdaq", "strategic_briefing", "archive_phase"],
                "knowledge_note": "NASDAQ developing knowledge record.",
                "event_catalog": [],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = oracle_knowledge_search_engine.search_knowledge(
        knowledge_catalog=catalog,
        query="crypto executive",
        market="CRYPTO",
        topic="executive_priority_watch",
        tier="institutional_knowledge",
        event_type="executive_trend",
        min_score=90,
        limit=10,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["searched_record_count"] == 2
    assert report["result_count"] == 1
    assert report["knowledge_results"][0]["knowledge_search_rank"] == 1
    assert report["knowledge_results"][0]["market"] == "CRYPTO"
    assert report["knowledge_results"][0]["execution_allowed"] is False
    assert report["knowledge_results"][0]["read_only"] is True
    assert "crypto" in report["knowledge_results"][0]["matched_terms"]
    assert report["knowledge_search_summary"]["execution_allowed"] is False
    assert report["knowledge_search_summary"]["read_only"] is True

    diag = oracle_knowledge_search_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["result_count"] == report["result_count"]

    print("[PASS] OI-146 Oracle Knowledge Search Engine")
    print({
        "result_count": report["result_count"],
        "summary": report["knowledge_search_summary"],
        "top": report["knowledge_results"][0],
    })


if __name__ == "__main__":
    test_oi_146_oracle_knowledge_search_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_knowledge_search_engine import oracle_knowledge_search_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-146 INSTALLER")
print(" Oracle Knowledge Search Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-146 installed")
print()
print("Run:")
print("py test_oi_146_oracle_knowledge_search_engine.py")