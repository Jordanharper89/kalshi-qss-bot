from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_dependency_graph_engine import build_repository_dependency_graph
from qseries_v2.repository_management.repository_dependency_analysis_engine import analyze_repository_dependencies
from qseries_v2.repository_management.repository_migration_planner_engine import plan_repository_migration
from qseries_v2.repository_management.repository_safe_move_validator_engine import validate_repository_safe_moves
from qseries_v2.repository_management.repository_refactoring_planner_engine import plan_repository_refactor


def test_refactoring_planner_from_live_repo():
    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    migration = plan_repository_migration(analysis)
    validation = validate_repository_safe_moves(migration)
    result = plan_repository_refactor(validation)

    assert result.engine_id == "RMS-008"
    assert result.input_count > 0
    assert result.step_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.steps[0].action == "git_checkpoint"


def test_approved_validation_creates_move_step():
    result = plan_repository_refactor(
        {
            "validations": [
                {
                    "path": "weather_engine.py",
                    "module_name": "weather_engine",
                    "phase": "phase_2_low_risk_leaf",
                    "action": "review_then_move",
                    "destination": "services/weather/",
                    "risk_level": "low",
                    "approved_for_move": True,
                    "blockers": [],
                }
            ]
        }
    )

    assert result.approved_move_count == 1
    assert any(step.action == "move_after_checkpoint" for step in result.steps)


def test_blocked_validation_creates_manual_review_step():
    result = plan_repository_refactor(
        {
            "validations": [
                {
                    "path": "oracle_alert_engine.py",
                    "module_name": "oracle_alert_engine",
                    "phase": "phase_4_legacy_oracle_review",
                    "action": "manual_review",
                    "destination": "qseries_v2/oracle_intelligence/ or archive/legacy_oracle/",
                    "risk_level": "high",
                    "approved_for_move": False,
                    "blockers": ["high_risk_requires_manual_review"],
                }
            ]
        }
    )

    assert result.manual_review_count == 1
    assert any(step.requires_manual_review for step in result.steps)


if __name__ == "__main__":
    test_refactoring_planner_from_live_repo()
    test_approved_validation_creates_move_step()
    test_blocked_validation_creates_manual_review_step()

    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    migration = plan_repository_migration(analysis)
    validation = validate_repository_safe_moves(migration)
    result = plan_repository_refactor(validation)

    print("[PASS] RMS-008 Repository Refactoring Planner Engine")
    print(result.to_dict())
