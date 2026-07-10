from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "ops" / "runtime_path_integration_audit.py"
TEST = ROOT / "test_ops_009_runtime_path_integration_audit.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class RuntimePathFinding:
    file: str
    line: int
    pattern: str
    text: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimePathAuditReport:
    status: str
    scanned_files: int
    findings: List[RuntimePathFinding]
    migrated_modules_checked: Dict[str, bool]

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "scanned_files": self.scanned_files,
            "findings": [f.to_dict() for f in self.findings],
            "migrated_modules_checked": self.migrated_modules_checked,
        }


class RuntimePathIntegrationAudit:
    BLOCKED_PATTERNS = [
        "qseries_v2/data",
        "qseries_v2\\\\data",
        "oracle_memory.sqlite3",
        "oracle_runtime_state.sqlite3",
        "qseries_history.sqlite3",
        "oracle_data.db",
    ]

    ALLOWED_FILES = {
        "runtime_paths.py",
        "runtime_path_integration_audit.py",
    }

    MIGRATED_MODULES = [
        "qseries_v2/ops/runtime_paths.py",
        "qseries_v2/oracle_intelligence/oracle_persistent_memory_store.py",
        "qseries_v2/oracle_intelligence/oracle_runtime_state_store.py",
        "qseries_v2/ops/historical_data_store.py",
        "qseries_v2/ops/qseries_runtime.py",
    ]

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = Path(repo_root or Path.cwd()).resolve()

    def iter_python_files(self) -> List[Path]:
        ignored_parts = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            "runtime",
        }

        files: List[Path] = []
        for path in self.repo_root.rglob("*.py"):
            rel = path.relative_to(self.repo_root)
            if any(part in ignored_parts for part in rel.parts):
                continue
            files.append(path)
        return sorted(files)

    def scan(self) -> RuntimePathAuditReport:
        findings: List[RuntimePathFinding] = []
        files = self.iter_python_files()

        for path in files:
            if path.name in self.ALLOWED_FILES:
                continue

            rel = path.relative_to(self.repo_root).as_posix()

            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                lines = path.read_text(errors="ignore").splitlines()

            for idx, line in enumerate(lines, start=1):
                normalized = line.replace("\\\\", "/")

                for pattern in self.BLOCKED_PATTERNS:
                    normalized_pattern = pattern.replace("\\\\", "/")

                    if normalized_pattern in normalized:
                        if "RuntimePaths." in line:
                            continue

                        findings.append(
                            RuntimePathFinding(
                                file=rel,
                                line=idx,
                                pattern=pattern,
                                text=line.strip(),
                            )
                        )

        migrated = self.check_migrated_modules()

        status = "ok" if not findings and all(migrated.values()) else "error"

        return RuntimePathAuditReport(
            status=status,
            scanned_files=len(files),
            findings=findings,
            migrated_modules_checked=migrated,
        )

    def check_migrated_modules(self) -> Dict[str, bool]:
        results: Dict[str, bool] = {}

        for rel in self.MIGRATED_MODULES:
            path = self.repo_root / rel
            if not path.exists():
                results[rel] = False
                continue

            text = path.read_text(encoding="utf-8", errors="ignore")
            results[rel] = "RuntimePaths" in text

        return results


def run_runtime_path_integration_audit(repo_root: Path | None = None) -> RuntimePathAuditReport:
    return RuntimePathIntegrationAudit(repo_root=repo_root).scan()


__all__ = [
    "RuntimePathFinding",
    "RuntimePathAuditReport",
    "RuntimePathIntegrationAudit",
    "run_runtime_path_integration_audit",
]
'''

test_code = r'''
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
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "ops" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .runtime_path_integration_audit import "
    "RuntimePathFinding, RuntimePathAuditReport, RuntimePathIntegrationAudit, "
    "run_runtime_path_integration_audit\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" OPS-009 INSTALLER")
print(" Runtime Path Integration Audit")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-009 installed")
print("")
print("Run:")
print("py test_ops_009_runtime_path_integration_audit.py")