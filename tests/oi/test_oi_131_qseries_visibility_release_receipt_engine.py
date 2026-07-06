
from qseries_v2.oracle_intelligence.qseries_visibility_release_receipt_engine import qseries_visibility_release_receipt_engine


def test_oi_131_qseries_visibility_release_receipt_engine():
    release_ledger = {
        "release_ledger_id": "abc123def456ghi789jkl012",
        "release_ledger_status": "recorded_released_visibility",
        "release_status": "released",
        "release_confirmed": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "release_ledger_items": [
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

    integrity = {
        "release_ledger_id": "abc123def456ghi789jkl012",
        "integrity_status": "verified",
        "integrity_score": 100.0,
        "release_ledger_integrity_confirmed": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    receipt = qseries_visibility_release_receipt_engine.build_release_receipt(release_ledger, integrity)

    assert receipt["status"] == "ok"
    assert receipt["read_only"] is True
    assert receipt["execution_allowed"] is False
    assert receipt["execution_owner"] == "Q Series"
    assert receipt["release_receipt_status"] == "confirmed"
    assert receipt["release_receipt_confirmed"] is True
    assert receipt["release_ledger_integrity_confirmed"] is True
    assert receipt["receipt_count"] == 2
    assert receipt["release_receipt_items"][0]["release_receipt_rank"] == 1
    assert receipt["release_receipt_items"][0]["market"] == "CRYPTO"
    assert receipt["release_receipt_summary"]["execution_allowed"] is False

    diag = qseries_visibility_release_receipt_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["release_receipt_confirmed"] is True

    print("[PASS] OI-131 Q Series Visibility Release Receipt Engine")
    print({
        "release_receipt_status": receipt["release_receipt_status"],
        "release_receipt_confirmed": receipt["release_receipt_confirmed"],
        "summary": receipt["release_receipt_summary"],
        "top": receipt["release_receipt_items"][0],
    })


if __name__ == "__main__":
    test_oi_131_qseries_visibility_release_receipt_engine()
