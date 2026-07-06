
from qseries_v2.oracle_intelligence.oracle_recall_ledger_engine import (
    oracle_recall_ledger_engine,
)


def test_oi_150_oracle_recall_ledger_engine():
    receipt_report = {
        "read_only": True,
        "execution_allowed": False,
        "receipt_id": "receipt-abc123",
        "receipt_status": "confirmed",
        "receipt_confirmed": True,
        "receipt_item_count": 1,
        "receipt_items": [
            {
                "market": "CRYPTO",
                "receipt_score": 94.0,
                "receipt_tier": "institutional_receipt",
                "receipt_status": "confirmed",
                "recall_score": 100.0,
                "recall_tier": "institutional_recall",
                "packet_validation_status": "validated",
                "knowledge_tier": "institutional_knowledge",
                "knowledge_status": "executive_ready_knowledge",
                "timeline_phase": "executive_timeline_active",
                "confidence_tier": "institutional_confidence",
                "memory_tier": "institutional_memory",
                "event_receipts": [
                    {
                        "event_receipt_id": "evt-rec-001",
                        "event_type": "executive_trend",
                        "event_source": "trend",
                        "event_receipt_score": 87.0,
                        "event_receipt_status": "confirmed",
                        "read_only": True,
                        "execution_allowed": False,
                    },
                    {
                        "event_receipt_id": "evt-rec-002",
                        "event_type": "confidence_evolution",
                        "event_source": "confidence",
                        "event_receipt_score": 84.0,
                        "event_receipt_status": "confirmed",
                        "read_only": True,
                        "execution_allowed": False,
                    },
                ],
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            }
        ],
    }

    report = oracle_recall_ledger_engine.record_recall_ledger(receipt_report)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["ledger_status"] == "recorded_confirmed"
    assert report["ledger_confirmed"] is True
    assert report["source_receipt_id"] == "receipt-abc123"
    assert report["ledger_entry_count"] == 1
    assert report["ledger_entries"][0]["ledger_rank"] == 1
    assert report["ledger_entries"][0]["market"] == "CRYPTO"
    assert report["ledger_entries"][0]["ledger_entry_status"] == "recorded_confirmed"
    assert report["ledger_entries"][0]["execution_allowed"] is False
    assert report["ledger_entries"][0]["read_only"] is True
    assert report["ledger_entries"][0]["event_receipt_refs"][0]["execution_allowed"] is False
    assert report["ledger_summary"]["execution_allowed"] is False
    assert report["ledger_summary"]["execution_owner"] == "Q Series"
    assert report["ledger_summary"]["ledger_confirmed"] is True

    diag = oracle_recall_ledger_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["ledger_status"] == "recorded_confirmed"

    print("[PASS] OI-150 Oracle Recall Ledger Engine")
    print({
        "ledger_id": report["ledger_id"],
        "ledger_status": report["ledger_status"],
        "ledger_confirmed": report["ledger_confirmed"],
        "summary": report["ledger_summary"],
        "top": report["ledger_entries"][0],
    })


if __name__ == "__main__":
    test_oi_150_oracle_recall_ledger_engine()
