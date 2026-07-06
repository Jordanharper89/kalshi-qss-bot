
from qseries_v2.oracle_intelligence.archive_search_engine import archive_search_engine


def test_oi_138_archive_search_engine():
    catalog = {
        "catalog_records": [
            {
                "catalog_key": "arc-001",
                "archive_id": "arc-001",
                "receipt_id": "rec-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "catalog_priority": 94,
                "catalog_tier": "institutional_priority",
                "visibility_score": 92,
                "integrity_score": 98,
                "catalog_label": "CRYPTO digest_snapshot catalog record",
                "catalog_summary": "CRYPTO archive record for read-only historical search.",
                "search_terms": ["crypto", "digest_snapshot", "arc-001", "volatility"],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "catalog_key": "arc-002",
                "archive_id": "arc-002",
                "receipt_id": "rec-002",
                "market": "NASDAQ",
                "archive_type": "strategic_briefing",
                "archive_timestamp": 1799999000,
                "catalog_priority": 76,
                "catalog_tier": "high_value",
                "visibility_score": 78,
                "integrity_score": 96,
                "catalog_label": "NASDAQ strategic_briefing catalog record",
                "catalog_summary": "NASDAQ archive record for read-only historical search.",
                "search_terms": ["nasdaq", "strategic_briefing", "arc-002", "macro"],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = archive_search_engine.search_archive(
        catalog_report=catalog,
        query="crypto volatility",
        market="CRYPTO",
        min_priority=80,
        limit=10,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["searched_record_count"] == 2
    assert report["result_count"] == 1
    assert report["results"][0]["search_rank"] == 1
    assert report["results"][0]["market"] == "CRYPTO"
    assert report["results"][0]["catalog_key"] == "arc-001"
    assert report["results"][0]["execution_allowed"] is False
    assert report["results"][0]["read_only"] is True
    assert "crypto" in report["results"][0]["match_terms"]
    assert "volatility" in report["results"][0]["match_terms"]
    assert report["search_summary"]["execution_allowed"] is False
    assert report["search_summary"]["read_only"] is True

    diag = archive_search_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["result_count"] == report["result_count"]

    print("[PASS] OI-138 Archive Search Engine")
    print({
        "result_count": report["result_count"],
        "summary": report["search_summary"],
        "top": report["results"][0],
    })


if __name__ == "__main__":
    test_oi_138_archive_search_engine()
