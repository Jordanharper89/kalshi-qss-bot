
"""
OPS-008 Q Series Runtime Runtime Path Migration

Migrates Q Series runtime operations to the canonical OPS-004 RuntimePaths
contract.

This module owns runtime lifecycle state, service registry state, scheduler
state, watchdog state, and runtime file locations.

No hard-coded qseries_v2/data paths are allowed here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout, validate_runtime_paths


@dataclass(frozen=True)
class RuntimeServiceStatus:
    name: str
    status: str
    metadata: Dict[str, Any]
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeWatchdogStatus:
    status: str
    checks: int
    last_check_at: str
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeStatus:
    status: str
    runtime_root: str
    services: Dict[str, Dict[str, Any]]
    scheduler_jobs: int
    watchdog: Dict[str, Any]
    paths: Dict[str, str]
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class QSeriesRuntime:
    """
    Canonical runtime manager for Q Series.

    Runtime directories and database paths must resolve through RuntimePaths.
    """

    def __init__(self) -> None:
        layout = ensure_runtime_layout()
        if not layout.ok:
            raise RuntimeError(f"Runtime layout validation failed: {layout.to_dict() if hasattr(layout, 'to_dict') else layout}")

        self.runtime_root = RuntimePaths.runtime_root()
        self.data_dir = RuntimePaths.data_dir()
        self.logs_dir = RuntimePaths.logs_dir()
        self.cache_dir = RuntimePaths.cache_dir()
        self.state_dir = RuntimePaths.state_dir()
        self.raw_dir = RuntimePaths.raw_dir()
        self.test_data_dir = RuntimePaths.test_data_dir()

        self._running = False
        self._services: Dict[str, RuntimeServiceStatus] = {}
        self._scheduler_jobs: Dict[str, Dict[str, Any]] = {}
        self._watchdog_checks = 0
        self._watchdog_notes: List[str] = []
        self._started_at: Optional[str] = None
        self._updated_at = self.now_iso()

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def start(self) -> RuntimeStatus:
        self._running = True
        self._started_at = self.now_iso()
        self._updated_at = self._started_at
        self.write_state("runtime_status.json", {"status": "running", "started_at": self._started_at})
        return self.status()

    def stop(self) -> RuntimeStatus:
        self._running = False
        self._updated_at = self.now_iso()
        self.write_state("runtime_status.json", {"status": "stopped", "updated_at": self._updated_at})
        return self.status()

    def register_service(
        self,
        name: str,
        status: str = "registered",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeServiceStatus:
        if not name or not isinstance(name, str):
            raise ValueError("service name must be a non-empty string")
        if not status or not isinstance(status, str):
            raise ValueError("service status must be a non-empty string")

        record = RuntimeServiceStatus(
            name=name,
            status=status,
            metadata=metadata or {},
            updated_at=self.now_iso(),
        )
        self._services[name] = record
        self._updated_at = record.updated_at
        return record

    def update_service(
        self,
        name: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeServiceStatus:
        existing = self._services.get(name)
        merged = dict(existing.metadata) if existing else {}
        if metadata:
            merged.update(metadata)
        return self.register_service(name=name, status=status, metadata=merged)

    def service_status(self, name: str) -> Optional[RuntimeServiceStatus]:
        return self._services.get(name)

    def services(self) -> Dict[str, Dict[str, Any]]:
        return {name: service.to_dict() for name, service in self._services.items()}

    def add_scheduler_job(
        self,
        job_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not job_id or not isinstance(job_id, str):
            raise ValueError("job_id must be a non-empty string")

        job = {
            "job_id": job_id,
            "metadata": metadata or {},
            "registered_at": self.now_iso(),
        }
        self._scheduler_jobs[job_id] = job
        self._updated_at = job["registered_at"]
        return job

    def remove_scheduler_job(self, job_id: str) -> bool:
        existed = job_id in self._scheduler_jobs
        if existed:
            del self._scheduler_jobs[job_id]
            self._updated_at = self.now_iso()
        return existed

    def scheduler_jobs(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._scheduler_jobs)

    def watchdog_check(self, note: Optional[str] = None) -> RuntimeWatchdogStatus:
        self._watchdog_checks += 1
        if note:
            self._watchdog_notes.append(note)

        checked_at = self.now_iso()
        self._updated_at = checked_at

        status = RuntimeWatchdogStatus(
            status="ok" if self._running else "stopped",
            checks=self._watchdog_checks,
            last_check_at=checked_at,
            notes=list(self._watchdog_notes),
        )

        self.write_state("watchdog_status.json", status.to_dict())
        return status

    def watchdog_status(self) -> RuntimeWatchdogStatus:
        return RuntimeWatchdogStatus(
            status="ok" if self._running else "stopped",
            checks=self._watchdog_checks,
            last_check_at=self._updated_at,
            notes=list(self._watchdog_notes),
        )

    def runtime_paths_report(self) -> Dict[str, str]:
        return {
            "runtime_root": str(RuntimePaths.runtime_root()),
            "data_dir": str(RuntimePaths.data_dir()),
            "raw_dir": str(RuntimePaths.raw_dir()),
            "logs_dir": str(RuntimePaths.logs_dir()),
            "cache_dir": str(RuntimePaths.cache_dir()),
            "state_dir": str(RuntimePaths.state_dir()),
            "test_data_dir": str(RuntimePaths.test_data_dir()),
            "oracle_data_db": str(RuntimePaths.oracle_data_db()),
            "oracle_memory_db": str(RuntimePaths.oracle_memory_db()),
            "oracle_runtime_state_db": str(RuntimePaths.oracle_runtime_state_db()),
            "qseries_history_db": str(RuntimePaths.qseries_history_db()),
        }

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            status="running" if self._running else "stopped",
            runtime_root=str(RuntimePaths.runtime_root()),
            services=self.services(),
            scheduler_jobs=len(self._scheduler_jobs),
            watchdog=self.watchdog_status().to_dict(),
            paths=self.runtime_paths_report(),
            updated_at=self._updated_at,
        )

    def health(self) -> Dict[str, Any]:
        validation = validate_runtime_paths()
        return {
            "status": "ok" if validation.ok else "error",
            "runtime_status": "running" if self._running else "stopped",
            "runtime_root": str(RuntimePaths.runtime_root()),
            "scheduler_jobs": len(self._scheduler_jobs),
            "services": len(self._services),
            "watchdog_checks": self._watchdog_checks,
            "uses_runtime_paths": True,
            "validation": {
                "status": validation.status,
                "missing_directories": validation.missing_directories,
                "errors": validation.errors,
            },
        }

    def state_path(self, filename: str) -> Path:
        return self._safe_child(RuntimePaths.state_dir(), filename)

    def log_path(self, filename: str) -> Path:
        return self._safe_child(RuntimePaths.logs_dir(), filename)

    def cache_path(self, filename: str) -> Path:
        return self._safe_child(RuntimePaths.cache_dir(), filename)

    def raw_path(self, filename: str) -> Path:
        return self._safe_child(RuntimePaths.raw_dir(), filename)

    def data_path(self, filename: str) -> Path:
        return self._safe_child(RuntimePaths.data_dir(), filename)

    def test_data_path(self, filename: str) -> Path:
        return self._safe_child(RuntimePaths.test_data_dir(), filename)

    def _safe_child(self, base: Path, filename: str) -> Path:
        if not filename or not isinstance(filename, str):
            raise ValueError("filename must be a non-empty string")

        candidate = (base / filename).resolve()
        base_resolved = base.resolve()

        if base_resolved not in candidate.parents and candidate != base_resolved:
            raise ValueError("path escapes runtime directory")

        candidate.parent.mkdir(parents=True, exist_ok=True)
        return candidate

    def write_state(self, filename: str, payload: Dict[str, Any]) -> Path:
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")

        path = self.state_path(filename)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def read_state(self, filename: str) -> Optional[Dict[str, Any]]:
        path = self.state_path(filename)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write_log(self, filename: str, message: str) -> Path:
        if not isinstance(message, str):
            raise ValueError("message must be a string")

        path = self.log_path(filename)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n")
        return path


def create_qseries_runtime() -> QSeriesRuntime:
    return QSeriesRuntime()


qseries_runtime = create_qseries_runtime


__all__ = [
    "RuntimeServiceStatus",
    "RuntimeWatchdogStatus",
    "RuntimeStatus",
    "QSeriesRuntime",
    "create_qseries_runtime",
    "qseries_runtime",
]
