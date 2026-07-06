from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_dependency_graph_engine import build_repository_dependency_graph
from qseries_v2.repository_management.repository_dependency_analysis_engine import analyze_repository_dependencies
from qseries_v2.repository_management.repository_migration_planner_engine import plan_repository_migration
from qseries_v2.repository_management.repository_safe_move_validator_engine import validate_repository_safe_moves


def test_safe_move_validator_from_live_repo():
    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    plan = plan_repository_migration(analysis)
    result = validate_repository_safe_moves(plan)

    assert result.engine_id == "RMS-007"
    assert result.input_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.validations


def test_high_risk_is_blocked():
    result = validate_repository_safe_moves(
        {
            "items": [
                {
                    "module_name": "oracle_alert_engine",
                    "path": "oracle_alert_engine.py",
                    "phase": "phase_4_legacy_oracle_review",
                    "risk_level": "high",
                    "action": "manual_review",
                    "destination": "qseries_v2/oracle_intelligence/ or archive/legacy_oracle/",
                }
            ]
        }
    )

    assert result.validations[0].approved_for_move is False
    assert "high_risk_requires_manual_review" in result.validations[0].blockers
    assert "ambiguous_destination" in result.validations[0].blockers


def test_low_risk_final_destination_can_be_approved():
    result = validate_repository_safe_moves(
        {
            "items": [
                {
                    "module_name": "weather_engine",
                    "path": "weather_engine.py",
                    "phase": "phase_2_low_risk_leaf",
                    "risk_level": "low",
                    "action": "review_then_move",
                    "destination": "services/weather/",
                }
            ]
        }
    )

    assert result.validations[0].approved_for_move is True
    assert result.validations[0].blocker_count == 0


if __name__ == "__main__":
    test_safe_move_validator_from_live_repo()
    test_high_risk_is_blocked()
    test_low_risk_final_destination_can_be_approved()

    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    plan = plan_repository_migration(analysis)
    result = validate_repository_safe_moves(plan)

    print("[PASS] RMS-007 Repository Safe Move Validator Engine")
    print(result.to_dict())
