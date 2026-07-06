from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_tracked_artifact_audit_engine import audit_repository_tracked_artifacts
from qseries_v2.repository_management.repository_artifact_cleanup_planner_engine import plan_repository_artifact_cleanup
from qseries_v2.repository_management.repository_artifact_cleanup_safety_gate_engine import run_repository_artifact_cleanup_safety_gate


def test_artifact_cleanup_safety_gate_from_live_repo():
    audit = audit_repository_tracked_artifacts(ROOT)
    plan = plan_repository_artifact_cleanup(audit)
    result = run_repository_artifact_cleanup_safety_gate(plan)

    assert result.engine_id == "RMS-019"
    assert result.input_count >= 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True


def test_artifact_cleanup_safety_gate_blocks_delete_command():
    result = run_repository_artifact_cleanup_safety_gate(
        {
            "items": [
                {
                    "path": "oracle/data/oracle_data.db",
                    "artifact_type": "tracked_database",
                    "phase": "phase_1_runtime_databases",
                    "action": "move_to_runtime_then_untrack",
                    "destination": "runtime/data/",
                    "risk_level": "medium",
                    "command_hint": "del oracle/data/oracle_data.db",
                }
            ]
        }
    )

    assert result.passed is False
    assert any(check.status == "fail" for check in result.checks)


def test_artifact_cleanup_safety_gate_accepts_cached_untrack():
    result = run_repository_artifact_cleanup_safety_gate(
        {
            "items": [
                {
                    "path": "qseries_v2/data/test_oracle_memory.sqlite3",
                    "artifact_type": "tracked_database",
                    "phase": "phase_2_test_databases",
                    "action": "remove_from_git_tracking",
                    "destination": "runtime/test-data/",
                    "risk_level": "medium",
                    "command_hint": 'git rm --cached "qseries_v2/data/test_oracle_memory.sqlite3"',
                }
            ]
        }
    )

    assert result.passed is True
    assert result.fail_count == 0


if __name__ == "__main__":
    test_artifact_cleanup_safety_gate_from_live_repo()
    test_artifact_cleanup_safety_gate_blocks_delete_command()
    test_artifact_cleanup_safety_gate_accepts_cached_untrack()

    audit = audit_repository_tracked_artifacts(ROOT)
    plan = plan_repository_artifact_cleanup(audit)
    result = run_repository_artifact_cleanup_safety_gate(plan)

    print("[PASS] RMS-019 Repository Artifact Cleanup Safety Gate Engine")
    print(result.to_dict())
