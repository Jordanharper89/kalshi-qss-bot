
from qseries_v2.oracle_intelligence.oracle_transfer_ledger_engine import oracle_transfer_ledger_engine


def test_oi_121_oracle_transfer_ledger_engine():
    transfer_record = {
        "transfer_status": "ready_for_q_series_visibility",
        "transfer_ready": True,
        "audit_status": "passed",
        "audit_score": 100.0,
        "intake_status": "ready",
        "q_series_safe_to_view": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "transfer_items": [
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

    ledger = oracle_transfer_ledger_engine.build_ledger_entry(transfer_record)

    assert ledger["status"] == "ok"
    assert ledger["read_only"] is True
    assert ledger["execution_allowed"] is False
    assert ledger["execution_owner"] == "Q Series"
    assert ledger["ledger_status"] == "recorded_ready_transfer"
    assert ledger["transfer_count"] == 2
    assert len(ledger["ledger_entry_id"]) == 24
    assert ledger["ledger_items"][0]["market"] == "CRYPTO"
    assert ledger["ledger_summary"]["execution_allowed"] is False

    diag = oracle_transfer_ledger_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-121 Oracle Transfer Ledger Engine")
    print({
        "ledger_status": ledger["ledger_status"],
        "ledger_entry_id": ledger["ledger_entry_id"],
        "summary": ledger["ledger_summary"],
        "top": ledger["ledger_items"][0],
    })


if __name__ == "__main__":
    test_oi_121_oracle_transfer_ledger_engine()
