
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from qseries_v2.ops.runtime_path_integration_audit import run_runtime_path_integration_audit
from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout, validate_runtime_paths


@dataclass(frozen=True)
class FinalRuntimePathGateResult:
    status: str
    generated_at: str
    runtime_root: str
    scanned_files: int
    finding_count: int
    findings: List[Dict[str, Any]]
    migrated_modules_checked: Dict[str, bool]
    runtime_validation: Dict[str, Any]
    json_report: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FinalRuntimePathIntegrationGate:
    def __init__(self, repo_root: Path | None = None) -> None:
        ensure_runtime_layout()
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.report_path = RuntimePaths.logs_dir() / "final_runtime_path_integration_gate.json"

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def run(self) -> FinalRuntimePathGateResult:
        audit = run_runtime_path_integration_audit(repo_root=self.repo_root)
        validation = validate_runtime_paths()

        findings = [finding.to_dict() for finding in audit.findings]

        status = "ok"
        if findings:
            status = "error"
        if not all(audit.migrated_modules_checked.values()):
            status = "error"
        if not validation.ok:
            status = "error"

        result = FinalRuntimePathGateResult(
            status=status,
            generated_at=self.now_iso(),
            runtime_root=str(RuntimePaths.runtime_root()),
            scanned_files=audit.scanned_files,
            finding_count=len(findings),
            findings=findings,
            migrated_modules_checked=audit.migrated_modules_checked,
            runtime_validation={
                "status": validation.status,
                "missing_directories": validation.missing_directories,
                "errors": validation.errors,
                "directories": validation.directories,
                "databases": validation.databases,
            },
            json_report=str(self.report_path),
        )

        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(
            json.dumps(result.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return result


def run_final_runtime_path_integration_gate(repo_root: Path | None = None) -> FinalRuntimePathGateResult:
    return FinalRuntimePathIntegrationGate(repo_root=repo_root).run()
