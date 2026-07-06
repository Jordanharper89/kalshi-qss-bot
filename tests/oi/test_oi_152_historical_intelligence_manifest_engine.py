from qseries_v2.oracle_intelligence.historical_intelligence_manifest_engine import (
    oracle_historical_intelligence_manifest_engine,
)


def test_manifest_builds_read_only():
    items = [
        {
            "ledger_id": "ledger-001",
            "record_type": "recall_ledger_entry",
            "market": "CRYPTO",
            "ledger_score": 89.92,
            "recall_score": 100.0,
            "receipt_score": 94.0,
            "confidence_score": 91.0,
            "lineage_hash": "abc123",
        }
    ]

    manifest = oracle_historical_intelligence_manifest_engine.build_manifest(items)

    assert manifest["read_only"] is True
    assert manifest["execution_allowed"] is False
    assert manifest["execution_owner"] == "Q Series"
    assert manifest["entry_count"] == 1
    assert manifest["top_market"] == "CRYPTO"
    assert manifest["entries"][0]["read_only"] is True
    assert manifest["entries"][0]["execution_allowed"] is False


def test_manifest_sorts_by_score():
    items = [
        {"source_id": "low", "market": "WEATHER", "historical_score": 62},
        {"source_id": "high", "market": "CRYPTO", "historical_score": 95},
        {"source_id": "mid", "market": "STOCKS", "historical_score": 78},
    ]

    manifest = oracle_historical_intelligence_manifest_engine.build_manifest(items)

    assert manifest["entries"][0]["source_id"] == "high"
    assert manifest["entries"][0]["manifest_tier"] == "institutional_historical_manifest"
    assert manifest["entries"][1]["source_id"] == "mid"
    assert manifest["entries"][2]["source_id"] == "low"


def test_manifest_counts_markets_and_statuses():
    items = [
        {"source_id": "a", "market": "crypto", "historical_score": 95},
        {"source_id": "b", "market": "crypto", "historical_score": 81},
        {"source_id": "c", "market": "forex", "historical_score": 55},
    ]

    manifest = oracle_historical_intelligence_manifest_engine.build_manifest(items)

    assert manifest["market_counts"]["CRYPTO"] == 2
    assert manifest["market_counts"]["FOREX"] == 1
    assert manifest["status_counts"]["executive_ready_manifest"] == 1
    assert manifest["status_counts"]["validated_manifest"] == 1
    assert manifest["status_counts"]["insufficient_manifest_quality"] == 1


def test_empty_manifest():
    manifest = oracle_historical_intelligence_manifest_engine.build_manifest([])

    assert manifest["manifest_status"] == "empty_manifest"
    assert manifest["entry_count"] == 0
    assert manifest["entries"] == []
    assert manifest["summary"]["read_only"] is True


if __name__ == "__main__":
    test_manifest_builds_read_only()
    test_manifest_sorts_by_score()
    test_manifest_counts_markets_and_statuses()
    test_empty_manifest()
    print("[PASS] OI-152 Oracle Historical Intelligence Manifest Engine")
