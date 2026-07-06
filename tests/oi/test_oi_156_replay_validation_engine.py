from qseries_v2.oracle_intelligence.replay_validation_engine import (
    oracle_replay_validation_engine,
)


def valid_replay():
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


def test_valid_replay_passes():
    report = oracle_replay_validation_engine.validate_replay(valid_replay())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["validation_status"] == "validated"
    assert report["issue_count"] == 0
    assert report["frame_count"] == 2


def test_execution_violation_fails():
    replay = valid_replay()
    replay["frames"][0]["execution_allowed"] = True

    report = oracle_replay_validation_engine.validate_replay(replay)

    assert report["validation_status"] == "failed"
    assert report["critical_count"] >= 1
    assert any(issue["code"] == "execution_violation" for issue in report["issues"])


def test_missing_lineage_fails():
    replay = valid_replay()
    replay["frames"][0]["lineage_hash"] = ""

    report = oracle_replay_validation_engine.validate_replay(replay)

    assert report["validation_status"] == "failed"
    assert any(issue["code"] == "missing_required_field" for issue in report["issues"])
    assert any(issue["code"] == "missing_lineage" for issue in report["issues"])


def test_rank_warning():
    replay = valid_replay()
    replay["frames"][1]["replay_rank"] = 5

    report = oracle_replay_validation_engine.validate_replay(replay)

    assert report["validation_status"] == "validated_with_warnings"
    assert report["warning_count"] == 1
    assert any(issue["code"] == "rank_mismatch" for issue in report["issues"])


def test_duplicate_frame_id_fails():
    replay = valid_replay()
    replay["frames"][1]["replay_frame_id"] = "frame-001"

    report = oracle_replay_validation_engine.validate_replay(replay)

    assert report["validation_status"] == "failed"
    assert any(issue["code"] == "duplicate_frame_id" for issue in report["issues"])


if __name__ == "__main__":
    test_valid_replay_passes()
    test_execution_violation_fails()
    test_missing_lineage_fails()
    test_rank_warning()
    test_duplicate_frame_id_fails()
    print("[PASS] OI-156 Oracle Replay Validation Engine")
