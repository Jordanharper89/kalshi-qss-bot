from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_dependency_graph_engine import build_repository_dependency_graph
from qseries_v2.repository_management.repository_dependency_analysis_engine import analyze_repository_dependencies


def test_dependency_analysis_from_live_repo():
    graph = build_repository_dependency_graph(ROOT)
    result = analyze_repository_dependencies(graph)

    assert result.engine_id == "RMS-005"
    assert result.input_nodes > 0
    assert result.analyzed_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.records


def test_dependency_hub_is_high_risk():
    result = analyze_repository_dependencies(
        {
            "nodes": [
                {
                    "module_name": "hub",
                    "path": "hub.py",
                    "internal_imports": [f"m{i}" for i in range(10)],
                    "external_imports": [],
                    "parse_error": None,
                }
            ],
            "orphan_modules": [],
            "circular_reference_count": 0,
        }
    )

    assert result.records[0].role == "dependency_hub"
    assert result.records[0].risk_level == "high"


def test_parse_error_is_high_risk():
    result = analyze_repository_dependencies(
        {
            "nodes": [
                {
                    "module_name": "bad",
                    "path": "bad.py",
                    "internal_imports": [],
                    "external_imports": [],
                    "parse_error": "SyntaxError",
                }
            ],
            "orphan_modules": ["bad"],
            "circular_reference_count": 0,
        }
    )

    assert result.records[0].role == "parse_error"
    assert result.records[0].migration_guidance == "fix_before_migration"


if __name__ == "__main__":
    test_dependency_analysis_from_live_repo()
    test_dependency_hub_is_high_risk()
    test_parse_error_is_high_risk()

    graph = build_repository_dependency_graph(ROOT)
    result = analyze_repository_dependencies(graph)

    print("[PASS] RMS-005 Repository Dependency Analysis Engine")
    print(result.to_dict())
