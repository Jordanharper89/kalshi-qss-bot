from qseries_v2.oracle_intelligence.historical_intelligence_summary_engine import (
    oracle_historical_intelligence_summary_engine,
)


def sample_receipt():
    return {
        "receipt_id": "receipt-001",
        "receipt_status": "snapshot_receipt_confirmed",
        "source_snapshot_id": "snap-001",
        "source_validation_status": "validated",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "receipt_record_id": "rec-001",
                "source_snapshot_record_id": "snap-rec-001",
                "source_id": "crypto-alpha",
                "market": "CRYPTO",
                "receipt_score": 96.0,
                "receipt_tier": "institutional_snapshot_receipt",
                "receipt_status": "confirmed_institutional_receipt",
                "snapshot_status": "executive_snapshot_ready",
                "snapshot_tier": "institutional_snapshot",
                "lineage_hash": "abc123",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            {
                "receipt_record_id": "rec-002",
                "source_snapshot_record_id": "snap-rec-002",
                "source_id": "stocks-beta",
                "market": "STOCKS",
                "receipt_score": 78.0,
                "receipt_tier": "validated_snapshot_receipt",
                "receipt_status": "confirmed_receipt",
                "snapshot_status": "snapshot_ready",
                "snapshot_tier": "validated_snapshot",
                "lineage_hash": "def456",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        ],
    }


def test_summary_created_from_receipt():
    summary = oracle_historical_intelligence_summary_engine.summarize(sample_receipt())

    assert summary["read_only"] is True
    assert summary["execution_allowed"] is False
    assert summary["execution_owner"] == "Q Series"
    assert summary["point_count"] == 2
    assert summary["top_market"] == "CRYPTO"
    assert summary["points"][0]["source_id"] == "crypto-alpha"
    assert summary["points"][0]["summary_tier"] == "institutional_historical_summary"
    assert summary["average_summary_score"] == 87.0


def test_summary_with_blocked_receipt():
    receipt = sample_receipt()
    receipt["records"][0]["receipt_status"] = "receipt_blocked_by_snapshot"
    receipt["records"][0]["receipt_tier"] = "invalid_snapshot_receipt"

    summary = oracle_historical_intelligence_summary_engine.summarize(receipt)

    assert summary["historical_summary_status"] == "historical_summary_created_with_blocks"
    assert summary["blocked_count"] == 1
    assert summary["points"][0]["summary_tier"] == "blocked_historical_summary"
    assert summary["points"][0]["summary_status"] == "summary_blocked_by_receipt"


def test_explain_summary_point():
    summary = oracle_historical_intelligence_summary_engine.summarize(sample_receipt())

    explanation = oracle_historical_intelligence_summary_engine.explain_summary_point(
        summary,
        "crypto-alpha",
    )

    assert explanation["found"] is True
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False
    assert explanation["point"]["source_id"] == "crypto-alpha"
    assert "Q Series owns execution" in explanation["explanation"]


def test_empty_summary():
    summary = oracle_historical_intelligence_summary_engine.summarize({
        "receipt_id": "empty",
        "receipt_status": "empty_snapshot_receipt",
        "records": [],
    })

    assert summary["historical_summary_status"] == "empty_historical_summary"
    assert summary["point_count"] == 0
    assert summary["points"] == []
    assert summary["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_summary_created_from_receipt()
    test_summary_with_blocked_receipt()
    test_explain_summary_point()
    test_empty_summary()
    print("[PASS] OI-159 Oracle Historical Intelligence Summary Engine")
