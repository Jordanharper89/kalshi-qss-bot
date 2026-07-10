from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "ops" / "runtime_path_audit_runner.py"
TEST = ROOT / "test_ops_010_runtime_path_audit_runner.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from qseries_v2.ops.runtime_path_integration_audit import run_runtime_path_integration_audit
from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout


class RuntimePathAuditRunner:
    """
    OPS-010 Runtime Path Audit Runner

    Runs the OPS-009 repository audit against the real repository and writes
    machine-readable and human-readable reports into runtime/logs.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        ensure_runtime_layout()
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.report_dir = RuntimePaths.logs_dir()
        self.report_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def run(self) -> Dict[str, Any]:
        report = run_runtime_path_integration_audit(repo_root=self.repo_root)

        payload: Dict[str, Any] = {
            "generated_at": self.now_iso(),
            "repo_root": str(self.repo_root),
            "status": report.status,
            "ok": report.ok,
            "scanned_files": report.scanned_files,
            "finding_count": len(report.findings),
            "findings": [finding.to_dict() for finding in report.findings],
            "migrated_modules_checked": report.migrated_modules_checked,
        }

        json_path = self.report_dir / "runtime_path_audit_report.json"
        txt_path = self.report_dir / "runtime_path_audit_report.txt"

        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        txt_path.write_text(self.render_text_report(payload), encoding="utf-8")

        payload["json_report"] = str(json_path)
        payload["text_report"] = str(txt_path)

        return payload

    def render_text_report(self, payload: Dict[str, Any]) -> str:
        lines = [
            "OPS-010 Runtime Path Audit Report",
            "================================",
            f"Generated At: {payload['generated_at']}",
            f"Repository: {payload['repo_root']}",
            f"Status: {payload['status']}",
            f"Scanned Files: {payload['scanned_files']}",
            f"Finding Count: {payload['finding_count']}",
            "",
            "Migrated Modules Checked:",
        ]

        for module, passed in payload["migrated_modules_checked"].items():
            lines.append(f"  [{'OK' if passed else 'FAIL'}] {module}")

        lines.append("")
        lines.append("Findings:")

        if not payload["findings"]:
            lines.append("  None")
        else:
            for finding in payload["findings"]:
                lines.append(
                    f"  [FAIL] {finding['file']}:{finding['line']} "
                    f"pattern={finding['pattern']} text={finding['text']}"
                )

        lines.append("")
        return "\n".join(lines)


def run_runtime_path_audit_runner(repo_root: Path | None = None) -> Dict[str, Any]:
    return RuntimePathAuditRunner(repo_root=repo_root).run()


__all__ = [
    "RuntimePathAuditRunner",
    "run_runtime_path_audit_runner",
]
'''

test_code = r'''
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
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "ops" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .runtime_path_audit_runner import "
    "RuntimePathAuditRunner, run_runtime_path_audit_runner\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" OPS-010 INSTALLER")
print(" Runtime Path Audit Runner")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-010 installed")
print("")
print("Run:")
print("py test_ops_010_runtime_path_audit_runner.py")