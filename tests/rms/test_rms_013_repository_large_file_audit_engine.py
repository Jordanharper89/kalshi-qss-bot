from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_large_file_audit_engine import audit_repository_large_files


def test_large_file_audit_live_repo():
    result = audit_repository_large_files(ROOT)

    assert result.engine_id == "RMS-013"
    assert result.scanned_files > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True


def test_large_file_audit_detects_warning_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "large.bin"
        target.write_bytes(b"x" * 4096)

        result = audit_repository_large_files(root, warning_mb=0.001, critical_mb=10.0)

        assert result.large_file_count == 1
        assert result.warning_count == 1
        assert result.critical_count == 0
        assert result.records[0].severity == "warning"


def test_large_file_audit_detects_critical_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "critical.bin"
        target.write_bytes(b"x" * 4096)

        result = audit_repository_large_files(root, warning_mb=0.001, critical_mb=0.001)

        assert result.large_file_count == 1
        assert result.critical_count == 1
        assert result.records[0].severity == "critical"
        assert result.status == "critical"


if __name__ == "__main__":
    test_large_file_audit_live_repo()
    test_large_file_audit_detects_warning_file()
    test_large_file_audit_detects_critical_file()

    result = audit_repository_large_files(ROOT)

    print("[PASS] RMS-013 Repository Large File Audit Engine")
    print(result.to_dict())
