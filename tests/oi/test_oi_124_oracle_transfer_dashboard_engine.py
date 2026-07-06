
from qseries_v2.oracle_intelligence.oracle_transfer_dashboard_engine import oracle_transfer_dashboard_engine


def test_oi_124_oracle_transfer_dashboard_engine():
    receipt = {
        "receipt_status": "confirmed",
        "receipt_confirmed": True,
        "ledger_integrity_confirmed": True,
        "transfer_ready": True,
        "transfer_status": "ready_for_q_series_visibility",
        "ledger_entry_id": "abc123def456ghi789jkl012",
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "receipt_items": [
            {
                "market": "CRYPTO",
                "receipt_rank": 1,
                "receipt_score": 100.0,
                "receipt_tier": "critical",
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
                "receipt_rank": 2,
                "receipt_score": 100.0,
                "receipt_tier": "critical",
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

    dashboard = oracle_transfer_dashboard_engine.build_dashboard(receipt)

    assert dashboard["status"] == "ok"
    assert dashboard["read_only"] is True
    assert dashboard["execution_allowed"] is False
    assert dashboard["execution_owner"] == "Q Series"
    assert dashboard["dashboard_status"] == "confirmed_visible"
    assert dashboard["card_count"] == 2
    assert dashboard["dashboard_cards"][0]["dashboard_rank"] == 1
    assert dashboard["dashboard_cards"][0]["market"] == "CRYPTO"
    assert dashboard["dashboard_summary"]["execution_allowed"] is False

    diag = oracle_transfer_dashboard_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["dashboard_status"] == "confirmed_visible"

    print("[PASS] OI-124 Oracle Transfer Dashboard Engine")
    print({
        "dashboard_status": dashboard["dashboard_status"],
        "card_count": dashboard["card_count"],
        "summary": dashboard["dashboard_summary"],
        "top": dashboard["dashboard_cards"][0],
    })


if __name__ == "__main__":
    test_oi_124_oracle_transfer_dashboard_engine()
