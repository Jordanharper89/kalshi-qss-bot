
from pathlib import Path
import tempfile

from qseries_v2.ops.runtime_path_integration_audit import run_runtime_path_integration_audit


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def install_contract_files(root: Path):
    files = [
        root / "qseries_v2" / "ops" / "runtime_paths.py",
        root / "qseries_v2" / "oracle_intelligence" / "oracle_persistent_memory_store.py",
        root / "qseries_v2" / "oracle_intelligence" / "oracle_runtime_state_store.py",
        root / "qseries_v2" / "ops" / "historical_data_store.py",
        root / "qseries_v2" / "ops" / "qseries_runtime.py",
    ]

    for file in files:
        write(
            file,
            'from qseries_v2.ops.runtime_paths import RuntimePaths\n'
            'MESSAGE = "No hard-coded qseries_v2/data database paths are allowed here."\n'
            'DB = RuntimePaths.qseries_history_db()\n',
        )


def test_ops_022_runtime_audit_rule_refinement():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        install_contract_files(root)

        write(
            root / "qseries_v2" / "ops" / "physical_runtime_database_migration.py",
            'LEGACY_SOURCES = ["oracle_data.db", "qseries_history.sqlite3"]\n',
        )

        clean = run_runtime_path_integration_audit(repo_root=root)
        assert clean.status == "ok"
        assert clean.findings == []

        write(
            root / "qseries_v2" / "oracle_intelligence" / "bad_engine.py",
            'DB = "qseries_v2/data/qseries_history.sqlite3"\n',
        )

        dirty = run_runtime_path_integration_audit(repo_root=root)
        assert dirty.status == "error"
        assert len(dirty.findings) >= 1
        assert any("bad_engine.py" in finding.file for finding in dirty.findings)

        print("[PASS] OPS-022 Runtime Audit Rule Refinement")
        print(clean.to_dict())


if __name__ == "__main__":
    test_ops_022_runtime_audit_rule_refinement()
