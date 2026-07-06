from qseries_v2.oracle_intelligence.institutional_memory_index_engine import (
    oracle_institutional_memory_index_engine,
)


def test_index_builds_from_manifest_entries():
    manifest = {
        "manifest_id": "manifest-001",
        "entries": [
            {
                "source_id": "source-low",
                "source_type": "historical_case",
                "market": "STOCKS",
                "historical_score": 79.0,
                "manifest_tier": "validated_historical_manifest",
                "manifest_status": "validated_manifest",
            },
            {
                "source_id": "source-high",
                "source_type": "recall_ledger_entry",
                "market": "CRYPTO",
                "historical_score": 96.0,
                "manifest_tier": "institutional_historical_manifest",
                "manifest_status": "executive_ready_manifest",
            },
        ],
    }

    index = oracle_institutional_memory_index_engine.build_index(manifest)

    assert index["read_only"] is True
    assert index["execution_allowed"] is False
    assert index["execution_owner"] == "Q Series"
    assert index["source_manifest_id"] == "manifest-001"
    assert index["record_count"] == 2
    assert index["top_market"] == "CRYPTO"
    assert index["records"][0]["source_id"] == "source-high"
    assert index["records"][0]["memory_tier"] == "institutional_memory_index"


def test_index_builds_from_dashboard_top_entries():
    dashboard = {
        "dashboard_id": "hist-dash-001",
        "tiles": {
            "top_entries": [
                {
                    "source_id": "dash-source",
                    "source_type": "dashboard_manifest_entry",
                    "market": "FOREX",
                    "historical_score": 82.0,
                    "manifest_tier": "validated_historical_manifest",
                }
            ]
        },
    }

    index = oracle_institutional_memory_index_engine.build_index(dashboard)

    assert index["source_dashboard_id"] == "hist-dash-001"
    assert index["record_count"] == 1
    assert index["records"][0]["market"] == "FOREX"
    assert index["records"][0]["memory_status"] == "search_ready"


def test_search_index_returns_matching_records():
    manifest = {
        "manifest_id": "manifest-002",
        "entries": [
            {
                "source_id": "crypto-alpha",
                "source_type": "recall_ledger_entry",
                "market": "CRYPTO",
                "historical_score": 94.0,
                "manifest_tier": "institutional_historical_manifest",
            },
            {
                "source_id": "weather-beta",
                "source_type": "historical_case",
                "market": "WEATHER",
                "historical_score": 77.0,
                "manifest_tier": "validated_historical_manifest",
            },
        ],
    }

    index = oracle_institutional_memory_index_engine.build_index(manifest)
    results = oracle_institutional_memory_index_engine.search_index(index, "crypto institutional")

    assert results["read_only"] is True
    assert results["execution_allowed"] is False
    assert results["match_count"] == 1
    assert results["matches"][0]["source_id"] == "crypto-alpha"


def test_empty_index():
    index = oracle_institutional_memory_index_engine.build_index({"manifest_id": "empty", "entries": []})

    assert index["index_status"] == "empty_memory_index"
    assert index["record_count"] == 0
    assert index["records"] == []
    assert index["summary"]["read_only"] is True


if __name__ == "__main__":
    test_index_builds_from_manifest_entries()
    test_index_builds_from_dashboard_top_entries()
    test_search_index_returns_matching_records()
    test_empty_index()
    print("[PASS] OI-154 Oracle Institutional Memory Index Engine")
