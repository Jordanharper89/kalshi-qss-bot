
from pathlib import Path
import tempfile

from qseries_v2.ops.runtime_path_integration_audit import (
    RuntimePathIntegrationAudit,
    run_runtime_path_integration_audit,
)


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def install_migrated_contract_files(root: Path):
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


def test_ops_011_runtime_path_audit_production_filter():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        install_migrated_contract_files(root)

        ignored_files = [
            root / "BACKUP_BEFORE_REPO_CLEANUP" / "qseries_v2" / "ops" / "old.py",
            root / "builds" / "ops" / "build_old.py",
            root / "tests" / "ops" / "test_old.py",
            root / "build_ops_fake.py",
            root / "test_ops_fake.py",
            root / "run_ops_fake.py",
            root / "qseries_v2" / "repository_management" / "repository_artifact_cleanup_planner_engine.py",
            root / "qseries_v2" / "repository_management" / "repository_gitignore_coverage_audit_engine.py",
        ]

        for file in ignored_files:
            write(file, 'DB = "qseries_v2/data/qseries_history.sqlite3"\n')

        write(
            root / "qseries_v2" / "oracle_intelligence" / "live_bad_engine.py",
            'DB = Path("qseries_v2/data/qseries_history.sqlite3")\n',
        )

        report = run_runtime_path_integration_audit(repo_root=root)

        assert report.status == "error"
        assert len(report.findings) == 3
        assert all("live_bad_engine.py" in finding.file for finding in report.findings)
        assert not any("BACKUP_BEFORE_REPO_CLEANUP" in finding.file for finding in report.findings)
        assert not any("builds/" in finding.file for finding in report.findings)
        assert not any("tests/" in finding.file for finding in report.findings)
        assert not any("repository_management" in finding.file for finding in report.findings)

        good = root / "qseries_v2" / "oracle_intelligence" / "live_bad_engine.py"
        good.write_text(
            "from qseries_v2.ops.runtime_paths import RuntimePaths\n"
            "DB = RuntimePaths.qseries_history_db()\n",
            encoding="utf-8",
        )

        clean_report = RuntimePathIntegrationAudit(repo_root=root).scan()

        assert clean_report.status == "ok"
        assert clean_report.ok is True
        assert clean_report.findings == []

        print("[PASS] OPS-011 Runtime Path Audit Production Filter")
        print(clean_report.to_dict())


if __name__ == "__main__":
    test_ops_011_runtime_path_audit_production_filter()
