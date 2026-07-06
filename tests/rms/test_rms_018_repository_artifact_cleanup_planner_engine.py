from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_tracked_artifact_audit_engine import audit_repository_tracked_artifacts
from qseries_v2.repository_management.repository_artifact_cleanup_planner_engine import plan_repository_artifact_cleanup


def test_artifact_cleanup_planner_from_live_repo():
    audit = audit_repository_tracked_artifacts(ROOT)
    result = plan_repository_artifact_cleanup(audit)

    assert result.engine_id == "RMS-018"
    assert result.input_count >= 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True


def test_artifact_cleanup_planner_database_runtime_phase():
    result = plan_repository_artifact_cleanup(
        {
            "records": [
                {
                    "path": "oracle/data/oracle_data.db",
                    "artifact_type": "tracked_database",
                    "severity": "warning",
                }
            ]
        }
    )

    assert result.plan_count == 1
    assert result.items[0].phase == "phase_1_runtime_databases"
    assert result.items[0].action == "move_to_runtime_then_untrack"


def test_artifact_cleanup_planner_test_database_phase():
    result = plan_repository_artifact_cleanup(
        {
            "records": [
                {
                    "path": "qseries_v2/data/test_oracle_memory.sqlite3",
                    "artifact_type": "tracked_database",
                    "severity": "warning",
                }
            ]
        }
    )

    assert result.items[0].phase == "phase_2_test_databases"
    assert result.items[0].action == "remove_from_git_tracking"


if __name__ == "__main__":
    test_artifact_cleanup_planner_from_live_repo()
    test_artifact_cleanup_planner_database_runtime_phase()
    test_artifact_cleanup_planner_test_database_phase()

    audit = audit_repository_tracked_artifacts(ROOT)
    result = plan_repository_artifact_cleanup(audit)

    print("[PASS] RMS-018 Repository Artifact Cleanup Planner Engine")
    print(result.to_dict())
