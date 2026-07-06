from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_integration_gate_engine import run_repository_integration_gate


def test_repository_integration_gate_from_live_repo():
    result = run_repository_integration_gate(ROOT)

    assert result.engine_id == "RMS-009"
    assert result.check_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.pass_count >= 1


def test_repository_integration_gate_detects_missing_repo():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_repository_integration_gate(tmp)

        assert result.passed is False
        assert result.fail_count > 0
        assert result.status == "failed"


def test_repository_integration_gate_result_is_serializable():
    result = run_repository_integration_gate(ROOT)
    data = result.to_dict()

    assert data["engine_id"] == "RMS-009"
    assert "checks" in data
    assert "telemetry" in data


if __name__ == "__main__":
    test_repository_integration_gate_from_live_repo()
    test_repository_integration_gate_detects_missing_repo()
    test_repository_integration_gate_result_is_serializable()

    result = run_repository_integration_gate(ROOT)
    print("[PASS] RMS-009 Repository Integration Gate Engine")
    print(result.to_dict())
