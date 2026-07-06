from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_gitignore_coverage_audit_engine import audit_repository_gitignore_coverage


def test_gitignore_coverage_live_repo():
    result = audit_repository_gitignore_coverage(ROOT)

    assert result.engine_id == "RMS-016"
    assert result.required_count > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True


def test_gitignore_coverage_detects_missing_patterns():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".gitignore").write_text(".env\nvenv/\n", encoding="utf-8")

        result = audit_repository_gitignore_coverage(root)

        assert result.missing_count > 0
        assert result.status == "warning"


def test_gitignore_coverage_detects_present_pattern():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".gitignore").write_text(".env\n*.env\nvenv/\n.venv/\n__pycache__/\n*.pyc\n.pytest_cache/\nruntime/\n*.log\n*.tmp\n*.cache\n*.csv\n*.bak*\n*_backup*\noracle_*.json\n*_log.csv\nqseries_v2/data/\n*.sqlite3\n*.db\n", encoding="utf-8")

        result = audit_repository_gitignore_coverage(root)

        assert result.missing_count == 0
        assert result.status == "ok"


if __name__ == "__main__":
    test_gitignore_coverage_live_repo()
    test_gitignore_coverage_detects_missing_patterns()
    test_gitignore_coverage_detects_present_pattern()

    result = audit_repository_gitignore_coverage(ROOT)

    print("[PASS] RMS-016 Repository Gitignore Coverage Audit Engine")
    print(result.to_dict())
