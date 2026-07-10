from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "ops" / "runtime_path_integration_audit.py"
TEST = ROOT / "test_ops_011_runtime_path_audit_production_filter.py"

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

    IGNORED_TOP_LEVEL_DIRS = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        "runtime",
        "BACKUP_BEFORE_REPO_CLEANUP",
        "builds",
        "tests",
    }

    IGNORED_PREFIXES = (
        "build_",
        "test_",
        "run_ops_",
    )

    IGNORED_PRODUCTION_MODULES = {
        "qseries_v2/repository_management/repository_artifact_cleanup_planner_engine.py",
        "qseries_v2/repository_management/repository_gitignore_coverage_audit_engine.py",
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

    def should_ignore_file(self, path: Path) -> bool:
        rel = path.relative_to(self.repo_root)
        rel_posix = rel.as_posix()

        if any(part in self.IGNORED_TOP_LEVEL_DIRS for part in rel.parts):
            return True

        if path.name.startswith(self.IGNORED_PREFIXES):
            return True

        if rel_posix in self.IGNORED_PRODUCTION_MODULES:
            return True

        return False

    def iter_python_files(self) -> List[Path]:
        files: List[Path] = []

        for path in self.repo_root.rglob("*.py"):
            if self.should_ignore_file(path):
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
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

print("========================================")
print(" OPS-011 INSTALLER")
print(" Runtime Path Audit Production Filter")
print("========================================")
print(f"[OK] Rewrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print("")
print("[DONE] OPS-011 installed")
print("")
print("Run:")
print("py test_ops_011_runtime_path_audit_production_filter.py")