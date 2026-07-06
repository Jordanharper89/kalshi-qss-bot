
from qseries_v2.oracle_intelligence.qseries_visibility_release_ledger_engine import qseries_visibility_release_ledger_engine


def test_oi_129_qseries_visibility_release_ledger_engine():
    release = {
        "release_status": "released",
        "release_confirmed": True,
        "surface_status": "visible",
        "validation_status": "validated",
        "validation_score": 100.0,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "release_items": [
            {
                "market": "CRYPTO",
                "release_rank": 1,
                "release_score": 100.0,
                "release_tier": "critical",
                "surface_tier": "critical",
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "release_rank": 2,
                "release_score": 100.0,
                "release_tier": "critical",
                "surface_tier": "critical",
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    ledger = qseries_visibility_release_ledger_engine.build_release_ledger(release)

    assert ledger["status"] == "ok"
    assert ledger["read_only"] is True
    assert ledger["execution_allowed"] is False
    assert ledger["execution_owner"] == "Q Series"
    assert ledger["release_ledger_status"] == "recorded_released_visibility"
    assert ledger["release_confirmed"] is True
    assert ledger["release_count"] == 2
    assert len(ledger["release_ledger_id"]) == 24
    assert ledger["release_ledger_items"][0]["market"] == "CRYPTO"
    assert ledger["release_ledger_summary"]["execution_allowed"] is False

    diag = qseries_visibility_release_ledger_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-129 Q Series Visibility Release Ledger Engine")
    print({
        "release_ledger_status": ledger["release_ledger_status"],
        "release_ledger_id": ledger["release_ledger_id"],
        "summary": ledger["release_ledger_summary"],
        "top": ledger["release_ledger_items"][0],
    })


if __name__ == "__main__":
    test_oi_129_qseries_visibility_release_ledger_engine()
