
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
