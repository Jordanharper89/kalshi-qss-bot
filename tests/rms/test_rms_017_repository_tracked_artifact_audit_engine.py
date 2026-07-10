from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_tracked_artifact_audit_engine import audit_repository_tracked_artifacts


def _audit_single_file(rel_path: str):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")

        return audit_repository_tracked_artifacts(root)


def test_tracked_artifact_audit_live_repo():
    result = audit_repository_tracked_artifacts(ROOT)

    assert result.engine_id == "RMS-017"
    assert result.tracked_file_count > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True


def test_tracked_artifact_audit_detects_env_as_critical():
    result = _audit_single_file(".env")

    assert result.artifact_count == 1
    assert result.critical_count == 1
    assert result.records[0].artifact_type == "tracked_environment"
    assert result.records[0].severity == "critical"


def test_tracked_artifact_audit_detects_db_as_critical():
    result = _audit_single_file("oracle_data.db")

    assert result.artifact_count == 1
    assert result.critical_count == 1
    assert result.records[0].artifact_type == "tracked_database"
    assert result.records[0].severity == "critical"


def test_tracked_artifact_audit_detects_sqlite3_as_critical():
    result = _audit_single_file("runtime_state.sqlite3")

    assert result.artifact_count == 1
    assert result.critical_count == 1
    assert result.records[0].artifact_type == "tracked_database"
    assert result.records[0].severity == "critical"


def test_tracked_artifact_audit_detects_qseries_data_as_critical():
    result = _audit_single_file("qseries_v2/data/generated_payload.txt")

    assert result.artifact_count == 1
    assert result.critical_count == 1
    assert result.records[0].artifact_type == "tracked_qseries_data_artifact"
    assert result.records[0].severity == "critical"


def test_tracked_artifact_audit_detects_oracle_data_as_critical():
    result = _audit_single_file("oracle/data/generated_payload.txt")

    assert result.artifact_count == 1
    assert result.critical_count == 1
    assert result.records[0].artifact_type == "tracked_oracle_data_artifact"
    assert result.records[0].severity == "critical"


def test_tracked_artifact_audit_preserves_raw_json_warning():
    result = _audit_single_file("samples/raw/market_orderbook_sample.json")

    assert result.artifact_count == 1
    assert result.warning_count == 1
    assert result.critical_count == 0
    assert result.records[0].artifact_type == "tracked_raw_sample"
    assert result.records[0].severity == "warning"


def test_tracked_artifact_audit_clean_fixture_has_zero_critical_findings():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("clean fixture", encoding="utf-8")

        result = audit_repository_tracked_artifacts(root)

        assert result.artifact_count == 0
        assert result.critical_count == 0
        assert result.status == "ok"


def test_tracked_artifact_audit_detects_runtime_json_fallback():
    result = _audit_single_file("oracle_state.json")

    assert result.artifact_count == 1
    assert result.records[0].artifact_type == "tracked_runtime_json"


if __name__ == "__main__":
    test_tracked_artifact_audit_live_repo()
    test_tracked_artifact_audit_detects_env_as_critical()
    test_tracked_artifact_audit_detects_db_as_critical()
    test_tracked_artifact_audit_detects_sqlite3_as_critical()
    test_tracked_artifact_audit_detects_qseries_data_as_critical()
    test_tracked_artifact_audit_detects_oracle_data_as_critical()
    test_tracked_artifact_audit_preserves_raw_json_warning()
    test_tracked_artifact_audit_clean_fixture_has_zero_critical_findings()
    test_tracked_artifact_audit_detects_runtime_json_fallback()

    result = audit_repository_tracked_artifacts(ROOT)

    print("[PASS] RMS-017 Repository Tracked Artifact Audit Engine")
    print(result.to_dict())
