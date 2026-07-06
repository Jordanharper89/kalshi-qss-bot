
from qseries_v2.oracle_intelligence.historical_visibility_pattern_engine import (
    historical_visibility_pattern_engine,
)


def test_oi_139_historical_visibility_pattern_engine():
    catalog = {
        "catalog_records": [
            {
                "catalog_key": "arc-001",
                "archive_id": "arc-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "catalog_priority": 94,
                "catalog_tier": "institutional_priority",
                "visibility_score": 92,
                "integrity_score": 98,
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "catalog_key": "arc-002",
                "archive_id": "arc-002",
                "market": "NASDAQ",
                "archive_type": "strategic_briefing",
                "archive_timestamp": 1799999000,
                "catalog_priority": 76,
                "catalog_tier": "high_value",
                "visibility_score": 78,
                "integrity_score": 96,
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    search = {
        "results": [
            {
                "catalog_key": "arc-001",
                "archive_id": "arc-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "catalog_priority": 94,
                "catalog_tier": "institutional_priority",
                "search_score": 100,
                "read_only": True,
                "execution_allowed": False,
            }
        ]
    }

    report = historical_visibility_pattern_engine.analyze_patterns(catalog, search)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["source_record_count"] == 2
    assert report["pattern_count"] >= 4
    assert report["patterns"][0]["pattern_rank"] == 1
    assert report["patterns"][0]["execution_allowed"] is False
    assert report["patterns"][0]["read_only"] is True
    assert report["pattern_summary"]["execution_allowed"] is False
    assert report["pattern_summary"]["read_only"] is True
    assert report["market_patterns"]
    assert report["archive_type_patterns"]
    assert report["tier_patterns"]
    assert report["time_patterns"]

    diag = historical_visibility_pattern_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["pattern_count"] == report["pattern_count"]

    print("[PASS] OI-139 Historical Visibility Pattern Engine")
    print({
        "source_record_count": report["source_record_count"],
        "pattern_count": report["pattern_count"],
        "summary": report["pattern_summary"],
        "top": report["patterns"][0],
    })


if __name__ == "__main__":
    test_oi_139_historical_visibility_pattern_engine()
