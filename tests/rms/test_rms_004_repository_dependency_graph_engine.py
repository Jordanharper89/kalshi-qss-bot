from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_dependency_graph_engine import build_repository_dependency_graph


def test_dependency_graph_scans_live_repo():
    result = build_repository_dependency_graph(ROOT)

    assert result.engine_id == "RMS-004"
    assert result.scanned_files > 0
    assert result.parsed_files > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["read_only_scan"] is True
    assert isinstance(result.nodes, list)


def test_dependency_graph_detects_internal_imports():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text("import b\n", encoding="utf-8")
        (root / "b.py").write_text("VALUE = 1\n", encoding="utf-8")

        result = build_repository_dependency_graph(root)

        node_a = [node for node in result.nodes if node.module_name == "a"][0]
        assert "b" in node_a.internal_imports


def test_dependency_graph_detects_parse_errors():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "bad.py").write_text("def broken(:\n", encoding="utf-8")

        result = build_repository_dependency_graph(root)

        assert result.parse_error_count == 1
        assert result.nodes[0].parse_error is not None


if __name__ == "__main__":
    test_dependency_graph_scans_live_repo()
    test_dependency_graph_detects_internal_imports()
    test_dependency_graph_detects_parse_errors()

    result = build_repository_dependency_graph(ROOT)
    print("[PASS] RMS-004 Repository Dependency Graph Engine")
    print(result.to_dict())
