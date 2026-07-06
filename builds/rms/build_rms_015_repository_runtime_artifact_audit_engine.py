from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_runtime_artifact_audit_engine.py"
TEST = TEST_DIR / "test_rms_015_repository_runtime_artifact_audit_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-015"
ENGINE_NAME = "Repository Runtime Artifact Audit Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RuntimeArtifactRecord:
    path: str
    artifact_type: str
    size_bytes: int
    severity: str
    recommendation: str


@dataclass(frozen=True)
class RuntimeArtifactAuditResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    scanned_files: int
    artifact_count: int
    warning_count: int
    records: List[RuntimeArtifactRecord]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "scanned_files": self.scanned_files,
            "artifact_count": self.artifact_count,
            "warning_count": self.warning_count,
            "records": [asdict(r) for r in self.records],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryRuntimeArtifactAuditEngine:
    def audit(self, root: str | Path = ".") -> RuntimeArtifactAuditResult:
        root_path = Path(root).resolve()
        excluded = {".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
        records: List[RuntimeArtifactRecord] = []
        scanned = 0

        for path in sorted(root_path.rglob("*"), key=lambda p: str(p).lower()):
            if not path.is_file():
                continue

            rel = path.relative_to(root_path)
            if any(part in excluded for part in rel.parts):
                continue

            scanned += 1
            artifact_type = self._artifact_type(path)
            if not artifact_type:
                continue

            severity = "warning" if artifact_type in {"database", "runtime_json", "raw_sample"} else "info"
            recommendation = self._recommendation(artifact_type)

            records.append(
                RuntimeArtifactRecord(
                    path=str(rel),
                    artifact_type=artifact_type,
                    size_bytes=path.stat().st_size,
                    severity=severity,
                    recommendation=recommendation,
                )
            )

        warning_count = sum(1 for r in records if r.severity == "warning")
        status = "warning" if warning_count else "ok"

        return RuntimeArtifactAuditResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            scanned_files=scanned,
            artifact_count=len(records),
            warning_count=warning_count,
            records=records,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "audit_only": True,
            },
            explanation=(
                f"Scanned {scanned} file(s). Found {len(records)} runtime artifact candidate(s), "
                f"{warning_count} warning(s). No files were modified."
            ),
        )

    def _artifact_type(self, path: Path) -> str:
        name = path.name.lower()
        full = str(path).lower()

        if name.endswith((".sqlite3", ".db")):
            return "database"
        if name.endswith(".json") and (
            "state" in name
            or "memory" in name
            or "cache" in name
            or "watchlist" in name
            or "sample" in name
            or "history" in name
        ):
            return "runtime_json"
        if "\\raw\\" in full or "/raw/" in full:
            return "raw_sample"
        if name.endswith(".log"):
            return "log"
        if name.endswith(".tmp"):
            return "temp"
        return ""

    def _recommendation(self, artifact_type: str) -> str:
        if artifact_type == "database":
            return "Move generated database files to runtime/data and ignore future database artifacts."
        if artifact_type == "runtime_json":
            return "Move runtime JSON state/sample files to runtime/ and keep them out of Git."
        if artifact_type == "raw_sample":
            return "Review raw market/orderbook samples and archive only intentional fixtures."
        if artifact_type == "log":
            return "Keep logs ignored; do not commit generated log files."
        if artifact_type == "temp":
            return "Delete temporary files after verification."
        return "Review artifact before committing."


def audit_repository_runtime_artifacts(root: str | Path = ".") -> RuntimeArtifactAuditResult:
    return RepositoryRuntimeArtifactAuditEngine().audit(root)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RuntimeArtifactRecord",
    "RuntimeArtifactAuditResult",
    "RepositoryRuntimeArtifactAuditEngine",
    "audit_repository_runtime_artifacts",
]
'''

TEST_CODE = r'''
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_runtime_artifact_audit_engine import audit_repository_runtime_artifacts


def test_runtime_artifact_audit_live_repo():
    result = audit_repository_runtime_artifacts(ROOT)

    assert result.engine_id == "RMS-015"
    assert result.scanned_files > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True


def test_runtime_artifact_audit_detects_database():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "oracle_data.db").write_bytes(b"db")

        result = audit_repository_runtime_artifacts(root)

        assert result.artifact_count == 1
        assert result.records[0].artifact_type == "database"
        assert result.status == "warning"


def test_runtime_artifact_audit_detects_state_json():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "oracle_state.json").write_text("{}", encoding="utf-8")

        result = audit_repository_runtime_artifacts(root)

        assert result.artifact_count == 1
        assert result.records[0].artifact_type == "runtime_json"


if __name__ == "__main__":
    test_runtime_artifact_audit_live_repo()
    test_runtime_artifact_audit_detects_database()
    test_runtime_artifact_audit_detects_state_json()

    result = audit_repository_runtime_artifacts(ROOT)

    print("[PASS] RMS-015 Repository Runtime Artifact Audit Engine")
    print(result.to_dict())
'''


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .repository_runtime_artifact_audit_engine import RepositoryRuntimeArtifactAuditEngine, audit_repository_runtime_artifacts\n"
    if line not in existing:
        existing += line
    INIT.write_text(existing, encoding="utf-8")


def main():
    PKG.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    update_init()

    print("========================================")
    print(" RMS-015 INSTALLER")
    print(" Repository Runtime Artifact Audit Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-015 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_015_repository_runtime_artifact_audit_engine.py")


if __name__ == "__main__":
    main()