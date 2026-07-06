from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_runtime_artifact_audit_engine import audit_repository_runtime_artifacts


def test_runtime_artifact_audit_live_repo():
    result = audit_repository_runtime_artifacts(ROOT)

    assert result.engine_id == "RMS-015"
    assert result.scanned_files > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True


def test_runtime_artifact_audit_detects_database():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "oracle_data.db").write_bytes(b"db")

        result = audit_repository_runtime_artifacts(root)

        assert result.artifact_count == 1
        assert result.records[0].artifact_type == "database"
        assert result.status == "warning"


def test_runtime_artifact_audit_detects_state_json():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "oracle_state.json").write_text("{}", encoding="utf-8")

        result = audit_repository_runtime_artifacts(root)

        assert result.artifact_count == 1
        assert result.records[0].artifact_type == "runtime_json"


if __name__ == "__main__":
    test_runtime_artifact_audit_live_repo()
    test_runtime_artifact_audit_detects_database()
    test_runtime_artifact_audit_detects_state_json()

    result = audit_repository_runtime_artifacts(ROOT)

    print("[PASS] RMS-015 Repository Runtime Artifact Audit Engine")
    print(result.to_dict())
