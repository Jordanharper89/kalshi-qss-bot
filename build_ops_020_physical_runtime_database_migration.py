from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "ops" / "physical_runtime_database_migration.py"
TEST = ROOT / "test_ops_020_physical_runtime_database_migration.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout
from qseries_v2.ops.final_runtime_path_integration_gate import run_final_runtime_path_integration_gate


@dataclass(frozen=True)
class DatabaseMigrationAction:
    source: str
    destination: str
    status: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PhysicalRuntimeDatabaseMigrationResult:
    status: str
    generated_at: str
    dry_run: bool
    runtime_data_dir: str
    actions: List[DatabaseMigrationAction]
    blocked_reasons: List[str]

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "generated_at": self.generated_at,
            "dry_run": self.dry_run,
            "runtime_data_dir": self.runtime_data_dir,
            "actions": [action.to_dict() for action in self.actions],
            "blocked_reasons": self.blocked_reasons,
        }


class PhysicalRuntimeDatabaseMigration:
    """
    OPS-020 Physical Runtime Database Migration.

    This migration only moves database artifacts after the runtime-path gate
    passes. Default mode is dry-run for safety.
    """

    DEFAULT_CANDIDATES = [
        Path("oracle") / "data" / "oracle_data.db",
        Path("qseries_v2") / "data" / "oracle_memory.sqlite3",
        Path("qseries_v2") / "data" / "oracle_runtime_state.sqlite3",
        Path("qseries_v2") / "data" / "qseries_history.sqlite3",
    ]

    def __init__(self, repo_root: Path | None = None) -> None:
        ensure_runtime_layout()
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.runtime_data_dir = RuntimePaths.data_dir()
        self.runtime_data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def discover_candidates(self) -> List[Path]:
        candidates: List[Path] = []

        for rel in self.DEFAULT_CANDIDATES:
            path = self.repo_root / rel
            if path.exists() and path.is_file():
                candidates.append(path)

        for base in [
            self.repo_root,
            self.repo_root / "qseries_v2" / "data",
            self.repo_root / "oracle" / "data",
        ]:
            if not base.exists():
                continue

            for path in base.glob("test_*.sqlite3"):
                if path.is_file():
                    candidates.append(path)

            for path in base.glob("test_*.db"):
                if path.is_file():
                    candidates.append(path)

        unique: List[Path] = []
        seen = set()

        for path in candidates:
            resolved = path.resolve()
            if resolved not in seen:
                unique.append(path)
                seen.add(resolved)

        return unique

    def destination_for(self, source: Path) -> Path:
        return self.runtime_data_dir / source.name

    def run(self, dry_run: bool = True, require_gate: bool = True) -> PhysicalRuntimeDatabaseMigrationResult:
        blocked_reasons: List[str] = []

        if require_gate:
            gate = run_final_runtime_path_integration_gate(repo_root=self.repo_root)
            if not gate.ok:
                blocked_reasons.append(
                    f"final runtime path gate failed: findings={gate.finding_count}, status={gate.status}"
                )

        actions: List[DatabaseMigrationAction] = []

        candidates = self.discover_candidates()

        if blocked_reasons:
            for source in candidates:
                actions.append(
                    DatabaseMigrationAction(
                        source=str(source),
                        destination=str(self.destination_for(source)),
                        status="blocked",
                        reason="migration blocked by safety gate",
                    )
                )

            return PhysicalRuntimeDatabaseMigrationResult(
                status="blocked",
                generated_at=self.now_iso(),
                dry_run=dry_run,
                runtime_data_dir=str(self.runtime_data_dir),
                actions=actions,
                blocked_reasons=blocked_reasons,
            )

        for source in candidates:
            destination = self.destination_for(source)

            if source.resolve() == destination.resolve():
                actions.append(
                    DatabaseMigrationAction(
                        source=str(source),
                        destination=str(destination),
                        status="skipped",
                        reason="already in runtime data directory",
                    )
                )
                continue

            if destination.exists():
                actions.append(
                    DatabaseMigrationAction(
                        source=str(source),
                        destination=str(destination),
                        status="skipped",
                        reason="destination already exists",
                    )
                )
                continue

            if dry_run:
                actions.append(
                    DatabaseMigrationAction(
                        source=str(source),
                        destination=str(destination),
                        status="planned",
                        reason="dry run only",
                    )
                )
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))

            actions.append(
                DatabaseMigrationAction(
                    source=str(source),
                    destination=str(destination),
                    status="moved",
                    reason="moved into runtime/data",
                )
            )

        status = "ok"
        if any(action.status == "moved" for action in actions):
            status = "ok"
        elif any(action.status == "planned" for action in actions):
            status = "planned"
        elif not actions:
            status = "ok"

        return PhysicalRuntimeDatabaseMigrationResult(
            status=status,
            generated_at=self.now_iso(),
            dry_run=dry_run,
            runtime_data_dir=str(self.runtime_data_dir),
            actions=actions,
            blocked_reasons=[],
        )


def run_physical_runtime_database_migration(
    repo_root: Path | None = None,
    dry_run: bool = True,
    require_gate: bool = True,
) -> PhysicalRuntimeDatabaseMigrationResult:
    return PhysicalRuntimeDatabaseMigration(repo_root=repo_root).run(
        dry_run=dry_run,
        require_gate=require_gate,
    )


__all__ = [
    "DatabaseMigrationAction",
    "PhysicalRuntimeDatabaseMigrationResult",
    "PhysicalRuntimeDatabaseMigration",
    "run_physical_runtime_database_migration",
]
'''

test_code = r'''
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.ops.physical_runtime_database_migration import (
    PhysicalRuntimeDatabaseMigration,
    run_physical_runtime_database_migration,
)


def write(path: Path, data: bytes = b"db"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def install_clean_repo(root: Path):
    files = [
        root / "qseries_v2" / "ops" / "runtime_paths.py",
        root / "qseries_v2" / "oracle_intelligence" / "oracle_persistent_memory_store.py",
        root / "qseries_v2" / "oracle_intelligence" / "oracle_runtime_state_store.py",
        root / "qseries_v2" / "ops" / "historical_data_store.py",
        root / "qseries_v2" / "ops" / "qseries_runtime.py",
    ]

    for file in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("from qseries_v2.ops.runtime_paths import RuntimePaths\n", encoding="utf-8")


def test_ops_020_physical_runtime_database_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = Path(tmp_obj.name)

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(tmp / "runtime")

    try:
        repo = tmp / "repo"
        install_clean_repo(repo)

        write(repo / "oracle" / "data" / "oracle_data.db")
        write(repo / "qseries_v2" / "data" / "oracle_memory.sqlite3")
        write(repo / "qseries_v2" / "data" / "oracle_runtime_state.sqlite3")
        write(repo / "qseries_v2" / "data" / "qseries_history.sqlite3")
        write(repo / "qseries_v2" / "data" / "test_oracle_memory.sqlite3")

        dry = run_physical_runtime_database_migration(
            repo_root=repo,
            dry_run=True,
            require_gate=True,
        )

        assert dry.status == "planned"
        assert dry.dry_run is True
        assert len(dry.actions) == 5
        assert all(action.status == "planned" for action in dry.actions)

        assert (repo / "oracle" / "data" / "oracle_data.db").exists()
        assert not (RuntimePaths.data_dir() / "oracle_data.db").exists()

        live = PhysicalRuntimeDatabaseMigration(repo_root=repo).run(
            dry_run=False,
            require_gate=True,
        )

        assert live.status == "ok"
        assert any(action.status == "moved" for action in live.actions)

        assert not (repo / "oracle" / "data" / "oracle_data.db").exists()
        assert (RuntimePaths.data_dir() / "oracle_data.db").exists()
        assert (RuntimePaths.data_dir() / "oracle_memory.sqlite3").exists()
        assert (RuntimePaths.data_dir() / "oracle_runtime_state.sqlite3").exists()
        assert (RuntimePaths.data_dir() / "qseries_history.sqlite3").exists()
        assert (RuntimePaths.data_dir() / "test_oracle_memory.sqlite3").exists()

        bad_repo = tmp / "bad_repo"
        install_clean_repo(bad_repo)
        write(bad_repo / "qseries_v2" / "data" / "qseries_history.sqlite3")
        bad_file = bad_repo / "qseries_v2" / "oracle_intelligence" / "bad_engine.py"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text('DB = "qseries_v2/data/qseries_history.sqlite3"\n', encoding="utf-8")

        blocked = run_physical_runtime_database_migration(
            repo_root=bad_repo,
            dry_run=False,
            require_gate=True,
        )

        assert blocked.status == "blocked"
        assert blocked.blocked_reasons
        assert all(action.status == "blocked" for action in blocked.actions)
        assert (bad_repo / "qseries_v2" / "data" / "qseries_history.sqlite3").exists()

        print("[PASS] OPS-020 Physical Runtime Database Migration")
        print({
            "dry_status": dry.status,
            "live_status": live.status,
            "blocked_status": blocked.status,
            "runtime_data_dir": str(RuntimePaths.data_dir()),
        })

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_020_physical_runtime_database_migration()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "ops" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .physical_runtime_database_migration import "
    "DatabaseMigrationAction, PhysicalRuntimeDatabaseMigrationResult, "
    "PhysicalRuntimeDatabaseMigration, run_physical_runtime_database_migration\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" OPS-020 INSTALLER")
print(" Physical Runtime Database Migration")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-020 installed")
print("")
print("Run:")
print("py test_ops_020_physical_runtime_database_migration.py")