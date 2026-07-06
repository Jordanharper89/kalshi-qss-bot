from qseries_v2.oracle_intelligence.historical_intelligence_dashboard_engine import (
    oracle_historical_intelligence_dashboard_engine,
)


def test_dashboard_builds_read_only():
    manifest = {
        "manifest_id": "manifest-001",
        "manifest_status": "manifest_built",
        "entry_count": 2,
        "top_market": "CRYPTO",
        "top_manifest_tier": "institutional_historical_manifest",
        "universal_market_model_ready": True,
        "market_counts": {"CRYPTO": 1, "STOCKS": 1},
        "tier_counts": {"institutional_historical_manifest": 1, "validated_historical_manifest": 1},
        "status_counts": {"executive_ready_manifest": 1, "validated_manifest": 1},
        "entries": [
            {
                "source_id": "source-low",
                "market": "STOCKS",
                "historical_score": 80.0,
                "manifest_tier": "validated_historical_manifest",
                "manifest_status": "validated_manifest",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "source_id": "source-high",
                "market": "CRYPTO",
                "historical_score": 95.0,
                "manifest_tier": "institutional_historical_manifest",
                "manifest_status": "executive_ready_manifest",
                "read_only": True,
                "execution_allowed": False,
            },
        ],
    }

    dashboard = oracle_historical_intelligence_dashboard_engine.build_dashboard(manifest)

    assert dashboard["read_only"] is True
    assert dashboard["execution_allowed"] is False
    assert dashboard["execution_owner"] == "Q Series"
    assert dashboard["manifest_id"] == "manifest-001"
    assert dashboard["top_market"] == "CRYPTO"
    assert dashboard["tiles"]["top_entries"][0]["source_id"] == "source-high"


def test_dashboard_handles_empty_manifest():
    dashboard = oracle_historical_intelligence_dashboard_engine.build_dashboard({
        "manifest_id": "manifest-empty",
        "manifest_status": "empty_manifest",
        "entries": [],
    })

    assert dashboard["entry_count"] == 0
    assert dashboard["tiles"]["top_entries"] == []
    assert dashboard["executive_summary"]["read_only"] is True
    assert dashboard["executive_summary"]["execution_allowed"] is False


def test_dashboard_market_distribution():
    manifest = {
        "manifest_id": "manifest-002",
        "market_counts": {"FOREX": 3, "CRYPTO": 1},
        "tier_counts": {},
        "status_counts": {},
        "entries": [
            {"source_id": "a", "market": "FOREX", "historical_score": 77},
            {"source_id": "b", "market": "CRYPTO", "historical_score": 88},
        ],
    }

    dashboard = oracle_historical_intelligence_dashboard_engine.build_dashboard(manifest)

    assert dashboard["top_market"] == "FOREX"
    assert dashboard["tiles"]["market_distribution"]["FOREX"] == 3


if __name__ == "__main__":
    test_dashboard_builds_read_only()
    test_dashboard_handles_empty_manifest()
    test_dashboard_market_distribution()
    print("[PASS] OI-153 Oracle Historical Intelligence Dashboard Engine")
