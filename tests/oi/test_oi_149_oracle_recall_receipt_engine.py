
from qseries_v2.oracle_intelligence.oracle_recall_receipt_engine import (
    oracle_recall_receipt_engine,
)


def test_oi_149_oracle_recall_receipt_engine():
    recall_report = {
        "read_only": True,
        "execution_allowed": False,
        "recall_count": 1,
        "recall_packets": [
            {
                "market": "CRYPTO",
                "recall_score": 100.0,
                "recall_tier": "institutional_recall",
                "recall_status": "executive_recall_ready",
                "knowledge_tier": "institutional_knowledge",
                "knowledge_status": "executive_ready_knowledge",
                "timeline_phase": "executive_timeline_active",
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

    validation_report = {
        "read_only": True,
        "execution_allowed": False,
        "validation_status": "validated",
        "validation_score": 100.0,
        "validated": True,
        "critical_failure_count": 0,
        "packet_validations": [
            {
                "market": "CRYPTO",
                "recall_score": 100.0,
                "packet_validation_score": 100.0,
                "packet_validation_status": "validated",
                "failed_check_count": 0,
                "critical_failure_count": 0,
                "event_recall_count": 2,
                "read_only": True,
                "execution_allowed": False,
            }
        ],
    }

    report = oracle_recall_receipt_engine.build_recall_receipt(
        recall_report,
        validation_report,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["receipt_status"] == "confirmed"
    assert report["receipt_confirmed"] is True
    assert report["source_recall_count"] == 1
    assert report["receipt_item_count"] == 1
    assert report["receipt_items"][0]["receipt_rank"] == 1
    assert report["receipt_items"][0]["market"] == "CRYPTO"
    assert report["receipt_items"][0]["receipt_status"] == "confirmed"
    assert report["receipt_items"][0]["execution_allowed"] is False
    assert report["receipt_items"][0]["read_only"] is True
    assert report["receipt_items"][0]["event_receipts"][0]["execution_allowed"] is False
    assert report["receipt_summary"]["execution_allowed"] is False
    assert report["receipt_summary"]["execution_owner"] == "Q Series"
    assert report["receipt_summary"]["receipt_confirmed"] is True

    diag = oracle_recall_receipt_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["receipt_status"] == "confirmed"

    print("[PASS] OI-149 Oracle Recall Receipt Engine")
    print({
        "receipt_id": report["receipt_id"],
        "receipt_status": report["receipt_status"],
        "receipt_confirmed": report["receipt_confirmed"],
        "summary": report["receipt_summary"],
        "top": report["receipt_items"][0],
    })


if __name__ == "__main__":
    test_oi_149_oracle_recall_receipt_engine()
