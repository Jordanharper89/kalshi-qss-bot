from qseries_v2.oracle_intelligence.snapshot_receipt_engine import (
    oracle_snapshot_receipt_engine,
)


def sample_snapshot(status="snapshot_created"):
    return {
        "snapshot_id": "snap-001",
        "snapshot_status": status,
        "source_validation_status": "validated",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "record_count": 2,
        "records": [
            {
                "snapshot_record_id": "snap-rec-001",
                "source_frame_id": "frame-001",
                "source_id": "crypto-alpha",
                "market": "CRYPTO",
                "snapshot_score": 96.0,
                "snapshot_tier": "institutional_snapshot",
                "snapshot_status": "executive_snapshot_ready",
                "replay_rank": 1,
                "lineage_hash": "abc123",
                "validation_status": "validated",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            {
                "snapshot_record_id": "snap-rec-002",
                "source_frame_id": "frame-002",
                "source_id": "stocks-beta",
                "market": "STOCKS",
                "snapshot_score": 78.0,
                "snapshot_tier": "validated_snapshot",
                "snapshot_status": "snapshot_ready",
                "replay_rank": 2,
                "lineage_hash": "def456",
                "validation_status": "validated",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        ],
    }


def test_receipt_created_from_snapshot():
    receipt = oracle_snapshot_receipt_engine.create_receipt(sample_snapshot())

    assert receipt["read_only"] is True
    assert receipt["execution_allowed"] is False
    assert receipt["execution_owner"] == "Q Series"
    assert receipt["receipt_status"] == "snapshot_receipt_confirmed"
    assert receipt["record_count"] == 2
    assert receipt["top_market"] == "CRYPTO"
    assert receipt["records"][0]["source_id"] == "crypto-alpha"
    assert receipt["records"][0]["receipt_tier"] == "institutional_snapshot_receipt"


def test_receipt_blocks_invalid_snapshot_records():
    snapshot = sample_snapshot()
    snapshot["records"][0]["snapshot_status"] = "snapshot_blocked_by_validation"
    snapshot["records"][0]["snapshot_tier"] = "invalid_snapshot"

    receipt = oracle_snapshot_receipt_engine.create_receipt(snapshot)

    assert receipt["receipt_status"] == "snapshot_receipt_created_with_blocks"
    assert receipt["blocked_count"] == 1
    assert receipt["records"][0]["receipt_tier"] == "invalid_snapshot_receipt"
    assert receipt["records"][0]["receipt_status"] == "receipt_blocked_by_snapshot"


def test_explain_receipt_record():
    receipt = oracle_snapshot_receipt_engine.create_receipt(sample_snapshot())

    explanation = oracle_snapshot_receipt_engine.explain_receipt_record(receipt, "crypto-alpha")

    assert explanation["found"] is True
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False
    assert explanation["record"]["source_id"] == "crypto-alpha"
    assert "Q Series owns execution" in explanation["explanation"]


def test_empty_receipt():
    receipt = oracle_snapshot_receipt_engine.create_receipt({
        "snapshot_id": "empty",
        "snapshot_status": "empty_snapshot",
        "records": [],
    })

    assert receipt["receipt_status"] == "empty_snapshot_receipt"
    assert receipt["record_count"] == 0
    assert receipt["records"] == []
    assert receipt["summary"]["read_only"] is True


if __name__ == "__main__":
    test_receipt_created_from_snapshot()
    test_receipt_blocks_invalid_snapshot_records()
    test_explain_receipt_record()
    test_empty_receipt()
    print("[PASS] OI-158 Oracle Snapshot Receipt Engine")
