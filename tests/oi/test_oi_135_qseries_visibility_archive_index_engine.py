
from qseries_v2.oracle_intelligence.qseries_visibility_archive_index_engine import (
    qseries_visibility_archive_index_engine,
)


def test_oi_135_qseries_visibility_archive_index_engine():
    receipt = {
        "archive_id": "archive-001",
        "receipt_id": "receipt-001",
        "archive_receipt_status": "confirmed",
        "archive_receipt_confirmed": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "archive_receipt_items": [
            {
                "market": "CRYPTO",
                "archive_receipt_rank": 1,
                "archive_receipt_score": 100.0,
                "archive_receipt_tier": "critical",
                "archive_score": 100.0,
                "archive_tier": "critical",
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
                "archive_receipt_rank": 2,
                "archive_receipt_score": 95.4,
                "archive_receipt_tier": "high",
                "archive_score": 95.4,
                "archive_tier": "high",
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

    report = qseries_visibility_archive_index_engine.build_index(receipt)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["index_status"] == "indexed"
    assert report["index_confirmed"] is True
    assert report["index_count"] == 2
    assert len(report["index_id"]) == 24
    assert report["index_items"][0]["market"] == "CRYPTO"
    assert report["index_items"][0]["index_rank"] == 1
    assert "critical" in report["tier_index"]
    assert "CRYPTO" in report["market_index"]
    assert report["index_summary"]["execution_allowed"] is False

    diag = qseries_visibility_archive_index_engine.diagnostics()

    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["index_confirmed"] is True

    print("[PASS] OI-135 Q Series Visibility Archive Index Engine")
    print({
        "index_status": report["index_status"],
        "index_id": report["index_id"],
        "summary": report["index_summary"],
        "top": report["index_items"][0],
    })


if __name__ == "__main__":
    test_oi_135_qseries_visibility_archive_index_engine()
