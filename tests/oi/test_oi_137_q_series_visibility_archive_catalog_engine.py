
from qseries_v2.oracle_intelligence.q_series_visibility_archive_catalog_engine import (
    q_series_visibility_archive_catalog_engine,
)


def test_oi_137_q_series_visibility_archive_catalog_engine():
    archive_index = {
        "index_entries": [
            {
                "archive_id": "arc-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "visibility_score": 92,
                "integrity_score": 98,
                "index_status": "indexed",
            },
            {
                "archive_id": "arc-002",
                "market": "NASDAQ",
                "archive_type": "strategic_briefing",
                "archive_timestamp": 1799999000,
                "visibility_score": 78,
                "integrity_score": 96,
                "index_status": "indexed",
            },
        ]
    }

    receipts = {
        "receipts": [
            {
                "archive_id": "arc-001",
                "receipt_id": "rec-001",
                "receipt_score": 99,
                "status": "receipt_verified",
            },
            {
                "archive_id": "arc-002",
                "receipt_id": "rec-002",
                "receipt_score": 95,
                "status": "receipt_verified",
            },
        ]
    }

    visibility = {
        "visibility_events": [
            {
                "archive_id": "arc-001",
                "visibility_status": "visible",
                "confidence": 94,
            },
            {
                "archive_id": "arc-002",
                "visibility_status": "visible",
                "confidence": 82,
            },
        ]
    }

    release = {
        "release_records": [
            {
                "archive_id": "arc-001",
                "release_status": "released",
                "release_score": 97,
            },
            {
                "archive_id": "arc-002",
                "release_status": "released",
                "release_score": 80,
            },
        ]
    }

    report = q_series_visibility_archive_catalog_engine.build_catalog(
        archive_index,
        receipts,
        visibility,
        release,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["catalog_count"] == 2
    assert report["catalog_records"][0]["catalog_rank"] == 1
    assert report["catalog_records"][0]["catalog_priority"] >= report["catalog_records"][-1]["catalog_priority"]
    assert report["catalog_records"][0]["execution_allowed"] is False
    assert report["catalog_records"][0]["read_only"] is True
    assert "crypto" in report["catalog_records"][0]["search_terms"]
    assert report["catalog_summary"]["execution_allowed"] is False
    assert report["catalog_summary"]["read_only"] is True

    diag = q_series_visibility_archive_catalog_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["catalog_count"] == report["catalog_count"]

    print("[PASS] OI-137 Q Series Visibility Archive Catalog Engine")
    print({
        "catalog_count": report["catalog_count"],
        "summary": report["catalog_summary"],
        "top": report["catalog_records"][0],
    })


if __name__ == "__main__":
    test_oi_137_q_series_visibility_archive_catalog_engine()
