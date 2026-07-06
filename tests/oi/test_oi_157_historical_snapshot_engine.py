from qseries_v2.oracle_intelligence.historical_snapshot_engine import (
    oracle_historical_snapshot_engine,
)


def sample_replay():
    return {
        "replay_id": "replay-001",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "frame_count": 2,
        "frames": [
            {
                "replay_frame_id": "frame-001",
                "replay_rank": 1,
                "source_id": "crypto-alpha",
                "source_type": "memory_index_record",
                "market": "CRYPTO",
                "replay_score": 96.0,
                "replay_tier": "institutional_replay",
                "replay_status": "executive_replay_ready",
                "lineage_hash": "abc123",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            {
                "replay_frame_id": "frame-002",
                "replay_rank": 2,
                "source_id": "stocks-beta",
                "source_type": "memory_index_record",
                "market": "STOCKS",
                "replay_score": 78.0,
                "replay_tier": "validated_replay",
                "replay_status": "validated_replay_ready",
                "lineage_hash": "def456",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        ],
    }


def sample_validation(status="validated"):
    return {
        "validation_id": "val-001",
        "source_replay_id": "replay-001",
        "validation_status": status,
        "issue_count": 0,
        "critical_count": 0,
        "warning_count": 0,
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
    }


def test_snapshot_created_from_validated_replay():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        sample_replay(),
        sample_validation("validated"),
    )

    assert snapshot["read_only"] is True
    assert snapshot["execution_allowed"] is False
    assert snapshot["execution_owner"] == "Q Series"
    assert snapshot["snapshot_status"] == "snapshot_created"
    assert snapshot["record_count"] == 2
    assert snapshot["top_market"] == "CRYPTO"
    assert snapshot["records"][0]["source_id"] == "crypto-alpha"
    assert snapshot["records"][0]["snapshot_tier"] == "institutional_snapshot"


def test_snapshot_with_validation_warnings():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        sample_replay(),
        sample_validation("validated_with_warnings"),
    )

    assert snapshot["source_validation_status"] == "validated_with_warnings"
    assert snapshot["records"][0]["snapshot_status"] == "snapshot_ready_with_warnings"
    assert snapshot["records"][1]["snapshot_status"] == "snapshot_ready_with_warnings"


def test_failed_validation_blocks_snapshot_tier():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        sample_replay(),
        sample_validation("failed"),
    )

    assert snapshot["snapshot_status"] == "snapshot_created_invalid_validation"
    assert snapshot["records"][0]["snapshot_tier"] == "invalid_snapshot"
    assert snapshot["records"][0]["snapshot_status"] == "snapshot_blocked_by_validation"


def test_explain_snapshot_record():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        sample_replay(),
        sample_validation("validated"),
    )

    explanation = oracle_historical_snapshot_engine.explain_snapshot_record(snapshot, "crypto-alpha")

    assert explanation["found"] is True
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False
    assert explanation["record"]["source_id"] == "crypto-alpha"
    assert "Q Series owns execution" in explanation["explanation"]


def test_empty_snapshot():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        {"replay_id": "empty", "frames": []},
        sample_validation("validated"),
    )

    assert snapshot["snapshot_status"] == "empty_snapshot"
    assert snapshot["record_count"] == 0
    assert snapshot["records"] == []
    assert snapshot["summary"]["read_only"] is True


if __name__ == "__main__":
    test_snapshot_created_from_validated_replay()
    test_snapshot_with_validation_warnings()
    test_failed_validation_blocks_snapshot_tier()
    test_explain_snapshot_record()
    test_empty_snapshot()
    print("[PASS] OI-157 Oracle Historical Snapshot Engine")
