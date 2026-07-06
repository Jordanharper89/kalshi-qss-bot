from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_dependency_graph_engine import build_repository_dependency_graph
from qseries_v2.repository_management.repository_dependency_analysis_engine import analyze_repository_dependencies
from qseries_v2.repository_management.repository_migration_planner_engine import plan_repository_migration


def test_migration_planner_from_live_repo():
    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    result = plan_repository_migration(analysis)

    assert result.engine_id == "RMS-006"
    assert result.input_count > 0
    assert result.plan_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.phase_counts
    assert result.risk_counts


def test_parse_error_goes_to_fix_required():
    result = plan_repository_migration(
        {
            "records": [
                {
                    "module_name": "bad",
                    "path": "bad.py",
                    "risk_level": "high",
                    "role": "parse_error",
                    "migration_guidance": "fix_before_migration",
                }
            ]
        }
    )

    assert result.items[0].phase == "phase_6_fix_required"
    assert result.items[0].action == "fix_before_move"


def test_legacy_oracle_goes_to_legacy_review():
    result = plan_repository_migration(
        {
            "records": [
                {
                    "module_name": "oracle_alert_engine",
                    "path": "oracle_alert_engine.py",
                    "risk_level": "high",
                    "role": "legacy_oracle",
                    "migration_guidance": "review_legacy_oracle_before_move",
                }
            ]
        }
    )

    assert result.items[0].phase == "phase_4_legacy_oracle_review"
    assert result.items[0].action == "manual_review"


if __name__ == "__main__":
    test_migration_planner_from_live_repo()
    test_parse_error_goes_to_fix_required()
    test_legacy_oracle_goes_to_legacy_review()

    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    result = plan_repository_migration(analysis)

    print("[PASS] RMS-006 Repository Migration Planner Engine")
    print(result.to_dict())
