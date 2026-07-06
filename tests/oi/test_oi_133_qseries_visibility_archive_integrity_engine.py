
from qseries_v2.oracle_intelligence.qseries_visibility_archive_integrity_engine import (
    qseries_visibility_archive_integrity_engine,
)


def test_oi_133_qseries_visibility_archive_integrity_engine():

    archive = {
        "archive_id": "archive-001",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "archive_confirmed": True,
        "archive_items": [
            {
                "market": "CRYPTO",
                "archive_score": 100.0,
                "archive_tier": "critical",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "archive_score": 95.4,
                "archive_tier": "high",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    report = (
        qseries_visibility_archive_integrity_engine.verify_archive(
            archive
        )
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["archive_integrity_confirmed"] is True
    assert report["integrity_status"] == "verified"
    assert report["failed_checks"] == 0

    diag = (
        qseries_visibility_archive_integrity_engine.diagnostics()
    )

    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["integrity_confirmed"] is True

    print(
        "[PASS] OI-133 Q Series Visibility Archive Integrity Engine"
    )

    print(
        {
            "integrity_score": report["integrity_score"],
            "integrity_status": report["integrity_status"],
            "summary": report["summary"],
        }
    )


if __name__ == "__main__":
    test_oi_133_qseries_visibility_archive_integrity_engine()

