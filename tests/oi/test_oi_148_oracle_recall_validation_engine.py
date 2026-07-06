
from qseries_v2.oracle_intelligence.oracle_recall_validation_engine import (
    oracle_recall_validation_engine,
)


def test_oi_148_oracle_recall_validation_engine():
    recall_report = {
        "read_only": True,
        "execution_allowed": False,
        "recall_count": 1,
        "qseries_handoff": {
            "execution_owner": "Q Series",
            "oracle_permission": "read_only",
            "execution_allowed": False,
        },
        "recall_packets": [
            {
                "market": "CRYPTO",
                "recall_score": 100.0,
                "recall_tier": "institutional_recall",
                "recall_status": "executive_recall_ready",
                "knowledge_score": 100.0,
                "search_score": 100.0,
                "knowledge_tier": "institutional_knowledge",
                "knowledge_status": "executive_ready_knowledge",
                "timeline_phase": "executive_timeline_active",
                "timeline_tier": "institutional_timeline",
                "trend_tier": "dominant_historical_trend",
                "trend_direction": "stable",
                "confidence_tier": "institutional_confidence",
                "memory_tier": "institutional_memory",
                "event_recall": [
                    {
                        "event_recall_id": "recall-event-002",
                        "event_type": "executive_trend",
                        "event_source": "trend",
                        "event_score": 89.4486,
                        "event_tier": "dominant_historical_trend",
                        "event_label": "executive_priority_watch",
                        "timeline_position": 2,
                        "recall_weight": 82.614,
                        "read_only": True,
                        "execution_allowed": False,
                        "event_recall_rank": 1,
                    },
                    {
                        "event_recall_id": "recall-event-001",
                        "event_type": "confidence_evolution",
                        "event_source": "confidence",
                        "event_score": 89.175,
                        "event_tier": "institutional_confidence",
                        "event_label": "stable",
                        "timeline_position": 1,
                        "recall_weight": 80.4225,
                        "read_only": True,
                        "execution_allowed": False,
                        "event_recall_rank": 2,
                    },
                ],
                "read_only": True,
                "execution_allowed": False,
            }
        ],
    }

    report = oracle_recall_validation_engine.validate_recall(recall_report)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["validation_status"] == "validated"
    assert report["validated"] is True
    assert report["safe_for_historical_use"] is True
    assert report["validation_score"] == 100.0
    assert report["source_recall_count"] == 1
    assert report["packet_validation_count"] == 1
    assert report["packet_validations"][0]["packet_validation_status"] == "validated"
    assert report["packet_validations"][0]["execution_allowed"] is False
    assert report["packet_validations"][0]["read_only"] is True
    assert report["critical_failure_count"] == 0
    assert report["warning_count"] == 0
    assert report["validation_summary"]["execution_allowed"] is False
    assert report["validation_summary"]["execution_owner"] == "Q Series"

    diag = oracle_recall_validation_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["validation_status"] == "validated"

    print("[PASS] OI-148 Oracle Recall Validation Engine")
    print({
        "validation_status": report["validation_status"],
        "validation_score": report["validation_score"],
        "validated": report["validated"],
        "summary": report["validation_summary"],
    })


if __name__ == "__main__":
    test_oi_148_oracle_recall_validation_engine()
