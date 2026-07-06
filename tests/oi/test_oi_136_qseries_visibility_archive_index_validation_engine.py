
from qseries_v2.oracle_intelligence.qseries_visibility_archive_index_validation_engine import (
    qseries_visibility_archive_index_validation_engine,
)


def test_oi_136_qseries_visibility_archive_index_validation_engine():
    archive_index = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "index_id": "index-001",
        "index_status": "indexed",
        "index_confirmed": True,
        "oracle_index_boundaries": [
            "Q Series visibility archive index is read-only.",
            "Oracle does not execute.",
            "Q Series owns execution evaluation and decisions.",
        ],
        "index_items": [
            {
                "market": "CRYPTO",
                "index_rank": 1,
                "index_score": 100.0,
                "index_tier": "critical",
                "archive_score": 100.0,
                "archive_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "index_rank": 2,
                "index_score": 95.4,
                "index_tier": "high",
                "archive_score": 95.4,
                "archive_tier": "high",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
        "tier_index": {
            "critical": [
                {
                    "market": "CRYPTO",
                    "index_rank": 1,
                    "index_score": 100.0,
                }
            ],
            "high": [
                {
                    "market": "NASDAQ",
                    "index_rank": 2,
                    "index_score": 95.4,
                }
            ],
        },
        "market_index": {
            "CRYPTO": {
                "index_rank": 1,
                "index_score": 100.0,
                "index_tier": "critical",
                "q_series_visibility": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            "NASDAQ": {
                "index_rank": 2,
                "index_score": 95.4,
                "index_tier": "high",
                "q_series_visibility": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        },
    }

    report = (
        qseries_visibility_archive_index_validation_engine.validate_index(
            archive_index
        )
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["validation_status"] == "validated"
    assert report["archive_index_validated"] is True
    assert report["failed_checks"] == 0
    assert report["validation_score"] == 100.0

    diag = qseries_visibility_archive_index_validation_engine.diagnostics()

    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["archive_index_validated"] is True

    print("[PASS] OI-136 Q Series Visibility Archive Index Validation Engine")
    print({
        "validation_score": report["validation_score"],
        "validation_status": report["validation_status"],
        "validated": report["archive_index_validated"],
        "summary": report["validation_summary"],
    })


if __name__ == "__main__":
    test_oi_136_qseries_visibility_archive_index_validation_engine()
