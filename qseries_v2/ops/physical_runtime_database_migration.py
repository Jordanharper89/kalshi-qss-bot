
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
