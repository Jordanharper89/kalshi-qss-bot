from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_duplicate_file_audit_engine import audit_repository_duplicate_files


def test_duplicate_file_audit_live_repo():
    result = audit_repository_duplicate_files(ROOT)

    assert result.engine_id == "RMS-014"
    assert result.scanned_files > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True


def test_duplicate_file_audit_detects_duplicates():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("same", encoding="utf-8")
        (root / "b.txt").write_text("same", encoding="utf-8")
        (root / "c.txt").write_text("different", encoding="utf-8")

        result = audit_repository_duplicate_files(root)

        assert result.duplicate_group_count == 1
        assert result.duplicate_file_count == 2
        assert len(result.groups[0].paths) == 2


def test_duplicate_file_audit_ignores_empty_by_default():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("", encoding="utf-8")
        (root / "b.txt").write_text("", encoding="utf-8")

        result = audit_repository_duplicate_files(root)

        assert result.duplicate_group_count == 0
        assert result.scanned_files == 0


if __name__ == "__main__":
    test_duplicate_file_audit_live_repo()
    test_duplicate_file_audit_detects_duplicates()
    test_duplicate_file_audit_ignores_empty_by_default()

    result = audit_repository_duplicate_files(ROOT)

    print("[PASS] RMS-014 Repository Duplicate File Audit Engine")
    print(result.to_dict())
