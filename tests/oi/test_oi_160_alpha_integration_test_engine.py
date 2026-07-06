from qseries_v2.oracle_intelligence.alpha_integration_test_engine import (
    oracle_alpha_integration_test_engine,
)


def sample_packets():
    return {
        "replay": {
            "replay_id": "replay-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "frame_count": 1,
            "frames": [{"replay_frame_id": "frame-001"}],
        },
        "validation": {
            "validation_id": "val-001",
            "source_replay_id": "replay-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
        },
        "snapshot": {
            "snapshot_id": "snap-001",
            "source_replay_id": "replay-001",
            "source_validation_id": "val-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "record_count": 1,
            "records": [{"snapshot_record_id": "snap-rec-001"}],
        },
        "receipt": {
            "receipt_id": "receipt-001",
            "source_snapshot_id": "snap-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "record_count": 1,
            "records": [{"receipt_record_id": "receipt-rec-001"}],
        },
        "summary": {
            "historical_summary_id": "summary-001",
            "source_receipt_id": "receipt-001",
            "source_snapshot_id": "snap-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "point_count": 1,
            "points": [{"summary_point_id": "summary-point-001"}],
        },
    }


def test_alpha_integration_ready():
    report = oracle_alpha_integration_test_engine.run_alpha_test(sample_packets())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["alpha_status"] == "alpha_integration_ready"
    assert report["issue_count"] == 0
    assert report["packet_count"] == 5


def test_missing_packet_fails():
    packets = sample_packets()
    del packets["summary"]

    report = oracle_alpha_integration_test_engine.run_alpha_test(packets)

    assert report["alpha_status"] == "alpha_integration_failed"
    assert report["critical_count"] == 1
    assert any(issue["code"] == "missing_required_packet" for issue in report["issues"])


def test_execution_violation_fails():
    packets = sample_packets()
    packets["replay"]["execution_allowed"] = True

    report = oracle_alpha_integration_test_engine.run_alpha_test(packets)

    assert report["alpha_status"] == "alpha_integration_failed"
    assert any(issue["code"] == "execution_contract_failed" for issue in report["issues"])


def test_link_mismatch_fails():
    packets = sample_packets()
    packets["snapshot"]["source_validation_id"] = "wrong-val"

    report = oracle_alpha_integration_test_engine.run_alpha_test(packets)

    assert report["alpha_status"] == "alpha_integration_failed"
    assert any(issue["code"] == "snapshot_validation_link_mismatch" for issue in report["issues"])


def test_count_warning():
    packets = sample_packets()
    packets["summary"]["point_count"] = 2

    report = oracle_alpha_integration_test_engine.run_alpha_test(packets)

    assert report["alpha_status"] == "alpha_integration_ready_with_warnings"
    assert report["warning_count"] == 1
    assert any(issue["code"] == "summary_point_count_mismatch" for issue in report["issues"])


if __name__ == "__main__":
    test_alpha_integration_ready()
    test_missing_packet_fails()
    test_execution_violation_fails()
    test_link_mismatch_fails()
    test_count_warning()
    print("[PASS] OI-160 Oracle Alpha Integration Test Engine")
