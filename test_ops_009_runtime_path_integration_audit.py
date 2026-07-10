
from pathlib import Path
import tempfile

from qseries_v2.ops.runtime_path_integration_audit import (
    RuntimePathIntegrationAudit,
    run_runtime_path_integration_audit,
)


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ops_009_runtime_path_integration_audit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        write(root / "qseries_v2" / "ops" / "runtime_paths.py", "class RuntimePaths: pass\n")
        write(root / "qseries_v2" / "ops" / "runtime_path_integration_audit.py", "# allowed\n")

        migrated_files = [
            root / "qseries_v2" / "oracle_intelligence" / "oracle_persistent_memory_store.py",
            root / "qseries_v2" / "oracle_intelligence" / "oracle_runtime_state_store.py",
            root / "qseries_v2" / "ops" / "historical_data_store.py",
            root / "qseries_v2" / "ops" / "qseries_runtime.py",
        ]

        for file in migrated_files:
            write(file, "from qseries_v2.ops.runtime_paths import RuntimePaths\n")

        write(
            root / "qseries_v2" / "oracle_intelligence" / "bad_engine.py",
            'DB = Path("qseries_v2/data/qseries_history.sqlite3")\n',
        )

        report = run_runtime_path_integration_audit(repo_root=root)

        assert report.status == "error"
        assert report.ok is False
        assert len(report.findings) >= 1
        assert any("bad_engine.py" in finding.file for finding in report.findings)

        bad_file = root / "qseries_v2" / "oracle_intelligence" / "bad_engine.py"
        bad_file.write_text(
            "from qseries_v2.ops.runtime_paths import RuntimePaths\nDB = RuntimePaths.qseries_history_db()\n",
            encoding="utf-8",
        )

        clean_report = RuntimePathIntegrationAudit(repo_root=root).scan()

        assert clean_report.status == "ok"
        assert clean_report.ok is True
        assert clean_report.findings == []
        assert all(clean_report.migrated_modules_checked.values())

        print("[PASS] OPS-009 Runtime Path Integration Audit")
        print(clean_report.to_dict())


if __name__ == "__main__":
    test_ops_009_runtime_path_integration_audit()
