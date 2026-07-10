
from __future__ import annotations

import ast
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
        "physical_runtime_database_migration.py",
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

    SAFE_TEXT_PHRASES = [
        "No hard-coded",
        "hard-coded",
        "database paths are allowed",
        "paths are allowed",
        "RuntimePaths migration",
        "runtime path migration",
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
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(errors="ignore")

            findings.extend(self.scan_python_ast(rel, text))

        migrated = self.check_migrated_modules()
        status = "ok" if not findings and all(migrated.values()) else "error"

        return RuntimePathAuditReport(
            status=status,
            scanned_files=len(files),
            findings=findings,
            migrated_modules_checked=migrated,
        )

    def scan_python_ast(self, rel: str, text: str) -> List[RuntimePathFinding]:
        findings: List[RuntimePathFinding] = []

        try:
            tree = ast.parse(text)
        except SyntaxError:
            return self.scan_text_fallback(rel, text)

        lines = text.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue

            if not isinstance(node.value, str):
                continue

            value = node.value
            normalized_value = value.replace("\\\\", "/")

            if self.is_safe_string(value):
                continue

            if self.is_runtimepaths_context(lines, node.lineno):
                continue

            for pattern in self.BLOCKED_PATTERNS:
                normalized_pattern = pattern.replace("\\\\", "/")

                if normalized_pattern in normalized_value:
                    findings.append(
                        RuntimePathFinding(
                            file=rel,
                            line=node.lineno,
                            pattern=pattern,
                            text=lines[node.lineno - 1].strip() if node.lineno - 1 < len(lines) else value,
                        )
                    )

        return findings

    def scan_text_fallback(self, rel: str, text: str) -> List[RuntimePathFinding]:
        findings: List[RuntimePathFinding] = []

        for idx, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                continue

            if self.is_safe_string(stripped):
                continue

            if "RuntimePaths." in stripped:
                continue

            normalized = stripped.replace("\\\\", "/")

            for pattern in self.BLOCKED_PATTERNS:
                normalized_pattern = pattern.replace("\\\\", "/")
                if normalized_pattern in normalized:
                    findings.append(
                        RuntimePathFinding(
                            file=rel,
                            line=idx,
                            pattern=pattern,
                            text=stripped,
                        )
                    )

        return findings

    def is_safe_string(self, value: str) -> bool:
        lower = value.lower()

        for phrase in self.SAFE_TEXT_PHRASES:
            if phrase.lower() in lower:
                return True

        return False

    def is_runtimepaths_context(self, lines: List[str], lineno: int) -> bool:
        start = max(0, lineno - 3)
        end = min(len(lines), lineno + 2)
        context = "\n".join(lines[start:end])
        return "RuntimePaths." in context or "RuntimePaths" in context

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
