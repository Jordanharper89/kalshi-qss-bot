
from qseries_v2.oracle_intelligence.qseries_visibility_archive_engine import qseries_visibility_archive_engine


def test_oi_132_qseries_visibility_archive_engine():
    receipt = {
        "release_receipt_status": "confirmed",
        "release_receipt_confirmed": True,
        "release_ledger_id": "abc123def456ghi789jkl012",
        "integrity_status": "verified",
        "integrity_score": 100.0,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "release_receipt_items": [
            {
                "market": "CRYPTO",
                "release_receipt_rank": 1,
                "receipt_score": 100.0,
                "receipt_tier": "critical",
                "release_score": 100.0,
                "release_tier": "critical",
                "surface_tier": "critical",
                "dashboard_tier": "critical",
                "transfer_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "release_receipt_rank": 2,
                "receipt_score": 100.0,
                "receipt_tier": "critical",
                "release_score": 100.0,
                "release_tier": "critical",
                "surface_tier": "critical",
                "dashboard_tier": "critical",
                "transfer_tier": "critical",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    archive = qseries_visibility_archive_engine.build_archive(receipt)

    assert archive["status"] == "ok"
    assert archive["read_only"] is True
    assert archive["execution_allowed"] is False
    assert archive["execution_owner"] == "Q Series"
    assert archive["archive_status"] == "archived"
    assert archive["archive_confirmed"] is True
    assert len(archive["archive_id"]) == 24
    assert archive["archive_count"] == 2
    assert archive["archive_items"][0]["market"] == "CRYPTO"
    assert archive["archive_summary"]["execution_allowed"] is False

    diag = qseries_visibility_archive_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["archive_confirmed"] is True

    print("[PASS] OI-132 Q Series Visibility Archive Engine")
    print({
        "archive_status": archive["archive_status"],
        "archive_id": archive["archive_id"],
        "summary": archive["archive_summary"],
        "top": archive["archive_items"][0],
    })


if __name__ == "__main__":
    test_oi_132_qseries_visibility_archive_engine()
