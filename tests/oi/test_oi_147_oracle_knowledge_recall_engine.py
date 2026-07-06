
from qseries_v2.oracle_intelligence.oracle_knowledge_recall_engine import (
    oracle_knowledge_recall_engine,
)


def test_oi_147_oracle_knowledge_recall_engine():
    search_report = {
        "knowledge_results": [
            {
                "market": "CRYPTO",
                "knowledge_score": 100.0,
                "search_score": 100.0,
                "knowledge_tier": "institutional_knowledge",
                "knowledge_status": "executive_ready_knowledge",
                "timeline_phase": "executive_timeline_active",
                "timeline_tier": "institutional_timeline",
                "trend_tier": "dominant_historical_trend",
                "trend_direction": "stable",
                "confidence_tier": "institutional_confidence",
                "confidence_trajectory": "stable",
                "memory_tier": "institutional_memory",
                "event_count": 4,
                "matched_terms": ["crypto", "executive"],
                "knowledge_topics": [
                    "executive_timeline_active",
                    "institutional_timeline",
                    "dominant_historical_trend",
                    "stable",
                    "executive_priority_watch",
                    "institutional_confidence",
                    "institutional_memory",
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
                        "timeline_position": 1,
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
                        "timeline_position": 2,
                        "read_only": True,
                        "execution_allowed": False,
                    },
                ],
                "read_only": True,
                "execution_allowed": False,
            }
        ]
    }

    report = oracle_knowledge_recall_engine.build_recall(
        knowledge_search_report=search_report,
        recall_market="CRYPTO",
        recall_topic="executive_priority_watch",
        min_recall_score=80,
        limit=5,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["source_result_count"] == 1
    assert report["recall_count"] == 1
    assert report["recall_packets"][0]["recall_rank"] == 1
    assert report["recall_packets"][0]["market"] == "CRYPTO"
    assert report["recall_packets"][0]["recall_status"] == "executive_recall_ready"
    assert report["recall_packets"][0]["execution_allowed"] is False
    assert report["recall_packets"][0]["read_only"] is True
    assert report["recall_packets"][0]["event_recall"][0]["execution_allowed"] is False
    assert report["recall_summary"]["execution_allowed"] is False
    assert report["recall_summary"]["read_only"] is True
    assert report["executive_recall_brief"]["execution_allowed"] is False
    assert report["executive_recall_brief"]["execution_owner"] == "Q Series"

    diag = oracle_knowledge_recall_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["recall_count"] == report["recall_count"]

    print("[PASS] OI-147 Oracle Knowledge Recall Engine")
    print({
        "recall_count": report["recall_count"],
        "summary": report["recall_summary"],
        "brief": report["executive_recall_brief"],
        "top": report["recall_packets"][0],
    })


if __name__ == "__main__":
    test_oi_147_oracle_knowledge_recall_engine()
