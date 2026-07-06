
from qseries_v2.oracle_intelligence.qseries_visibility_archive_receipt_engine import (
    qseries_visibility_archive_receipt_engine,
)


def test_oi_134_qseries_visibility_archive_receipt_engine():

    archive = {
        "archive_id": "archive-001",
        "archive_status": "archived",
        "archive_confirmed": True,
        "archive_items": [
            {
                "market": "CRYPTO",
                "archive_score": 100.0,
                "archive_tier": "critical",
                "release_receipt_rank": 1,
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "archive_score": 95.4,
                "archive_tier": "high",
                "release_receipt_rank": 2,
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    integrity = {
        "integrity_status": "verified",
        "integrity_score": 100.0,
        "archive_integrity_confirmed": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    receipt = qseries_visibility_archive_receipt_engine.build_receipt(
        archive,
        integrity,
    )

    assert receipt["status"] == "ok"
    assert receipt["read_only"] is True
    assert receipt["execution_allowed"] is False
    assert receipt["execution_owner"] == "Q Series"
    assert receipt["receipt_confirmed"] is True
    assert receipt["receipt_count"] == 2
    assert receipt["receipt_items"][0]["market"] == "CRYPTO"

    diag = qseries_visibility_archive_receipt_engine.diagnostics()

    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["receipt_confirmed"] is True

    print("[PASS] OI-134 Q Series Visibility Archive Receipt Engine")
    print(
        {
            "receipt_id": receipt["receipt_id"],
            "receipt_confirmed": receipt["receipt_confirmed"],
            "summary": receipt["receipt_summary"],
            "top": receipt["receipt_items"][0],
        }
    )


if __name__ == "__main__":
    test_oi_134_qseries_visibility_archive_receipt_engine()

