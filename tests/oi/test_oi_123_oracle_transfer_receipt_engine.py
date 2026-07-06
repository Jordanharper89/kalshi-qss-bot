
from qseries_v2.oracle_intelligence.oracle_transfer_receipt_engine import oracle_transfer_receipt_engine


def test_oi_123_oracle_transfer_receipt_engine():
    ledger = {
        "ledger_entry_id": "abc123def456ghi789jkl012",
        "ledger_status": "recorded_ready_transfer",
        "transfer_status": "ready_for_q_series_visibility",
        "transfer_ready": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "ledger_items": [
            {
                "market": "CRYPTO",
                "transfer_rank": 1,
                "transfer_score": 100.0,
                "transfer_tier": "critical",
                "intake_tier": "critical",
                "handoff_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "transfer_rank": 2,
                "transfer_score": 90.0,
                "transfer_tier": "critical",
                "intake_tier": "high",
                "handoff_tier": "high",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    integrity = {
        "ledger_entry_id": "abc123def456ghi789jkl012",
        "integrity_status": "verified",
        "integrity_score": 100.0,
        "ledger_integrity_confirmed": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    receipt = oracle_transfer_receipt_engine.build_receipt(ledger, integrity)

    assert receipt["status"] == "ok"
    assert receipt["read_only"] is True
    assert receipt["execution_allowed"] is False
    assert receipt["execution_owner"] == "Q Series"
    assert receipt["receipt_status"] == "confirmed"
    assert receipt["receipt_confirmed"] is True
    assert receipt["ledger_integrity_confirmed"] is True
    assert receipt["receipt_count"] == 2
    assert receipt["receipt_items"][0]["receipt_rank"] == 1
    assert receipt["receipt_items"][0]["market"] == "CRYPTO"
    assert receipt["receipt_summary"]["execution_allowed"] is False

    diag = oracle_transfer_receipt_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["receipt_confirmed"] is True

    print("[PASS] OI-123 Oracle Transfer Receipt Engine")
    print({
        "receipt_status": receipt["receipt_status"],
        "receipt_confirmed": receipt["receipt_confirmed"],
        "summary": receipt["receipt_summary"],
        "top": receipt["receipt_items"][0],
    })


if __name__ == "__main__":
    test_oi_123_oracle_transfer_receipt_engine()
