
from qseries_v2.oracle_intelligence.oracle_market_memory_engine import oracle_market_memory_engine


def test_oi_140_oracle_market_memory_engine():
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

    patterns = {
        "patterns": [
            {
                "pattern_key": "CRYPTO",
                "pattern_type": "market_visibility",
                "record_count": 1,
                "pattern_score": 89.7,
                "pattern_tier": "dominant_pattern",
                "markets": ["CRYPTO"],
                "archive_types": ["digest_snapshot"],
                "catalog_tiers": ["institutional_priority"],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "pattern_key": "NASDAQ",
                "pattern_type": "market_visibility",
                "record_count": 1,
                "pattern_score": 55.2,
                "pattern_tier": "developing_pattern",
                "markets": ["NASDAQ"],
                "archive_types": ["strategic_briefing"],
                "catalog_tiers": ["high_value"],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = oracle_market_memory_engine.build_market_memory(patterns, catalog, search)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["market_memory_count"] == 2
    assert report["market_memory_profiles"][0]["memory_rank"] == 1
    assert report["market_memory_profiles"][0]["market"] == "CRYPTO"
    assert report["market_memory_profiles"][0]["execution_allowed"] is False
    assert report["market_memory_profiles"][0]["read_only"] is True
    assert report["market_memory_profiles"][0]["historical_signature"]["execution_allowed"] is False
    assert report["memory_summary"]["execution_allowed"] is False
    assert report["memory_summary"]["read_only"] is True

    diag = oracle_market_memory_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["market_memory_count"] == report["market_memory_count"]

    print("[PASS] OI-140 Oracle Market Memory Engine")
    print({
        "market_memory_count": report["market_memory_count"],
        "summary": report["memory_summary"],
        "top": report["market_memory_profiles"][0],
    })


if __name__ == "__main__":
    test_oi_140_oracle_market_memory_engine()
