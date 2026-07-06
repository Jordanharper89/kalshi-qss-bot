from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_cleanup_execution_report_engine import generate_repository_cleanup_execution_report


def test_cleanup_execution_report_from_live_repo():
    result = generate_repository_cleanup_execution_report(ROOT)

    assert result.engine_id == "RMS-020"
    assert result.step_count > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True
    assert "RMS-019" in result.telemetry["validated_chain"]


def test_cleanup_execution_report_is_serializable():
    result = generate_repository_cleanup_execution_report(ROOT)
    data = result.to_dict()

    assert data["engine_id"] == "RMS-020"
    assert "steps" in data
    assert "telemetry" in data


if __name__ == "__main__":
    test_cleanup_execution_report_from_live_repo()
    test_cleanup_execution_report_is_serializable()

    result = generate_repository_cleanup_execution_report(ROOT)

    print("[PASS] RMS-020 Repository Cleanup Execution Report Engine")
    print(result.to_dict())
