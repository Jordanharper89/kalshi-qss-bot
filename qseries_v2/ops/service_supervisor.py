"""
OPS-001 — Service Supervisor

Purpose:
- Manage long-running Q Series background services.
- Start, stop, restart, and inspect registered services.
- Protect the system from duplicate starts.
- Track health, uptime, crashes, and last errors.
- Foundation for 24/7 Oracle operations.

No trading logic.
No execution logic.
"""

import time
import threading
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional


class ServiceState(str, Enum):
    REGISTERED = "REGISTERED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class ServiceSupervisorError(Exception):
    pass


@dataclass
class ManagedService:
    name: str
    start_callable: Callable[[], Any]
    stop_callable: Optional[Callable[[], Any]] = None
    health_callable: Optional[Callable[[], Dict[str, Any]]] = None
    restart_on_failure: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    state: ServiceState = ServiceState.REGISTERED
    started_at: Optional[float] = None
    stopped_at: Optional[float] = None
    last_error: Optional[str] = None
    start_count: int = 0
    stop_count: int = 0
    restart_count: int = 0
    last_start_result: Any = None
    last_stop_result: Any = None


class QSeriesServiceSupervisor:
    def __init__(self, event_bus: Any = None):
        self.event_bus = event_bus
        self._lock = threading.RLock()
        self._services: Dict[str, ManagedService] = {}

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        if self.event_bus is None:
            return

        try:
            if hasattr(self.event_bus, "publish"):
                self.event_bus.publish(event_type, payload)
            elif hasattr(self.event_bus, "emit"):
                self.event_bus.emit(event_type, payload)
        except Exception:
            pass

    def register_service(
        self,
        name: str,
        start_callable: Callable[[], Any],
        stop_callable: Optional[Callable[[], Any]] = None,
        health_callable: Optional[Callable[[], Dict[str, Any]]] = None,
        restart_on_failure: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not name or not name.strip():
            raise ServiceSupervisorError("Service name is required.")

        if not callable(start_callable):
            raise ServiceSupervisorError(f"Service '{name}' requires a callable start function.")

        clean_name = name.strip()

        with self._lock:
            if clean_name in self._services:
                raise ServiceSupervisorError(f"Service already registered: {clean_name}")

            service = ManagedService(
                name=clean_name,
                start_callable=start_callable,
                stop_callable=stop_callable,
                health_callable=health_callable,
                restart_on_failure=restart_on_failure,
                metadata=metadata or {},
            )

            self._services[clean_name] = service

        self._emit(
            "ops.service.registered",
            {
                "service": clean_name,
                "timestamp": time.time(),
                "metadata": metadata or {},
            },
        )

        return {
            "status": "ok",
            "service": clean_name,
            "state": ServiceState.REGISTERED.value,
        }

    def start_service(self, name: str) -> Dict[str, Any]:
        with self._lock:
            service = self._get_service_locked(name)

            if service.state == ServiceState.RUNNING:
                return {
                    "status": "already_running",
                    "service": service.name,
                    "state": service.state.value,
                }

            service.state = ServiceState.STARTING
            service.last_error = None

        self._emit("ops.service.starting", {"service": name, "timestamp": time.time()})

        try:
            result = service.start_callable()

            with self._lock:
                service.state = ServiceState.RUNNING
                service.started_at = time.time()
                service.stopped_at = None
                service.start_count += 1
                service.last_start_result = result

            self._emit(
                "ops.service.started",
                {
                    "service": name,
                    "timestamp": time.time(),
                    "result": result,
                },
            )

            return {
                "status": "ok",
                "service": service.name,
                "state": ServiceState.RUNNING.value,
                "result": result,
            }

        except Exception as exc:
            error = f"{exc}\n{traceback.format_exc()}"

            with self._lock:
                service.state = ServiceState.ERROR
                service.last_error = error

            self._emit(
                "ops.service.error",
                {
                    "service": name,
                    "phase": "start",
                    "error": str(exc),
                    "timestamp": time.time(),
                },
            )

            return {
                "status": "error",
                "service": service.name,
                "state": ServiceState.ERROR.value,
                "error": str(exc),
            }

    def stop_service(self, name: str) -> Dict[str, Any]:
        with self._lock:
            service = self._get_service_locked(name)

            if service.state in (ServiceState.STOPPED, ServiceState.REGISTERED):
                return {
                    "status": "already_stopped",
                    "service": service.name,
                    "state": service.state.value,
                }

            service.state = ServiceState.STOPPING

        self._emit("ops.service.stopping", {"service": name, "timestamp": time.time()})

        try:
            result = None
            if service.stop_callable is not None:
                result = service.stop_callable()

            with self._lock:
                service.state = ServiceState.STOPPED
                service.stopped_at = time.time()
                service.stop_count += 1
                service.last_stop_result = result

            self._emit(
                "ops.service.stopped",
                {
                    "service": name,
                    "timestamp": time.time(),
                    "result": result,
                },
            )

            return {
                "status": "ok",
                "service": service.name,
                "state": ServiceState.STOPPED.value,
                "result": result,
            }

        except Exception as exc:
            error = f"{exc}\n{traceback.format_exc()}"

            with self._lock:
                service.state = ServiceState.ERROR
                service.last_error = error

            self._emit(
                "ops.service.error",
                {
                    "service": name,
                    "phase": "stop",
                    "error": str(exc),
                    "timestamp": time.time(),
                },
            )

            return {
                "status": "error",
                "service": service.name,
                "state": ServiceState.ERROR.value,
                "error": str(exc),
            }

    def restart_service(self, name: str) -> Dict[str, Any]:
        stop_result = self.stop_service(name)
        start_result = self.start_service(name)

        with self._lock:
            service = self._get_service_locked(name)
            service.restart_count += 1

        return {
            "status": "ok" if start_result.get("status") in ("ok", "already_running") else "error",
            "service": name,
            "stop": stop_result,
            "start": start_result,
        }

    def start_all(self) -> Dict[str, Any]:
        results = {}

        for name in self.list_service_names():
            results[name] = self.start_service(name)

        return {
            "status": "ok",
            "results": results,
        }

    def stop_all(self) -> Dict[str, Any]:
        results = {}

        for name in self.list_service_names():
            results[name] = self.stop_service(name)

        return {
            "status": "ok",
            "results": results,
        }

    def list_service_names(self):
        with self._lock:
            return list(self._services.keys())

    def _get_service_locked(self, name: str) -> ManagedService:
        if name not in self._services:
            raise ServiceSupervisorError(f"Unknown service: {name}")
        return self._services[name]

    def service_status(self, name: str) -> Dict[str, Any]:
        with self._lock:
            service = self._get_service_locked(name)

            uptime = None
            if service.started_at and service.state == ServiceState.RUNNING:
                uptime = time.time() - service.started_at

            health = None
            if service.health_callable is not None:
                try:
                    health = service.health_callable()
                except Exception as exc:
                    health = {
                        "status": "error",
                        "error": str(exc),
                    }

            return {
                "name": service.name,
                "state": service.state.value,
                "started_at": service.started_at,
                "stopped_at": service.stopped_at,
                "uptime_seconds": uptime,
                "start_count": service.start_count,
                "stop_count": service.stop_count,
                "restart_count": service.restart_count,
                "restart_on_failure": service.restart_on_failure,
                "last_error": service.last_error,
                "health": health,
                "metadata": dict(service.metadata),
            }

    def diagnostics(self) -> Dict[str, Any]:
        with self._lock:
            statuses = {
                name: self.service_status(name)
                for name in self._services.keys()
            }

            running = sum(1 for s in statuses.values() if s["state"] == ServiceState.RUNNING.value)
            errors = sum(1 for s in statuses.values() if s["state"] == ServiceState.ERROR.value)

            return {
                "module": "ops_001_service_supervisor",
                "status": "ok" if errors == 0 else "warning",
                "service_count": len(statuses),
                "running_count": running,
                "error_count": errors,
                "services": statuses,
            }


def build_service_supervisor(event_bus: Any = None) -> QSeriesServiceSupervisor:
    return QSeriesServiceSupervisor(event_bus=event_bus)


if __name__ == "__main__":
    supervisor = build_service_supervisor()
    print(supervisor.diagnostics())
