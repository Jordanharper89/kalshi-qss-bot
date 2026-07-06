
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
