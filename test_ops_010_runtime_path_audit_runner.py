
import json
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.ops.runtime_path_audit_runner import RuntimePathAuditRunner, run_runtime_path_audit_runner


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ops_010_runtime_path_audit_runner():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = Path(tmp_obj.name)

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(tmp / "runtime")

    try:
        repo = tmp / "repo"

        write(repo / "qseries_v2" / "ops" / "runtime_paths.py", "class RuntimePaths: pass\n")
        write(repo / "qseries_v2" / "ops" / "runtime_path_integration_audit.py", "# audit\n")

        migrated_files = [
            repo / "qseries_v2" / "oracle_intelligence" / "oracle_persistent_memory_store.py",
            repo / "qseries_v2" / "oracle_intelligence" / "oracle_runtime_state_store.py",
            repo / "qseries_v2" / "ops" / "historical_data_store.py",
            repo / "qseries_v2" / "ops" / "qseries_runtime.py",
        ]

        for file in migrated_files:
            write(file, "from qseries_v2.ops.runtime_paths import RuntimePaths\n")

        write(
            repo / "qseries_v2" / "oracle_intelligence" / "remaining_engine.py",
            'DB_PATH = "qseries_v2/data/qseries_history.sqlite3"\n',
        )

        result = run_runtime_path_audit_runner(repo_root=repo)

        assert result["status"] == "error"
        assert result["ok"] is False
        assert result["finding_count"] >= 1
        assert Path(result["json_report"]).exists()
        assert Path(result["text_report"]).exists()

        loaded = json.loads(Path(result["json_report"]).read_text(encoding="utf-8"))
        assert loaded["status"] == "error"
        assert loaded["finding_count"] >= 1

        text = Path(result["text_report"]).read_text(encoding="utf-8")
        assert "OPS-010 Runtime Path Audit Report" in text
        assert "remaining_engine.py" in text

        print("[PASS] OPS-010 Runtime Path Audit Runner")
        print({
            "status": result["status"],
            "finding_count": result["finding_count"],
            "json_report": result["json_report"],
            "text_report": result["text_report"],
        })

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_010_runtime_path_audit_runner()
