"""
OPS-002 — Background Scheduler

Purpose:
- Run recurring background jobs for Q Series.
- Supports start/stop/restart.
- Tracks job health, errors, run counts, and timing.
- Designed for market cache refresh, Oracle scan loops, heartbeat checks, and future collectors.

No trading logic.
No execution logic.
"""

import time
import threading
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional


class SchedulerJobState(str, Enum):
    REGISTERED = "REGISTERED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class BackgroundSchedulerError(Exception):
    pass


@dataclass
class ScheduledJob:
    name: str
    interval_seconds: float
    job_callable: Callable[[], Any]
    run_immediately: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    state: SchedulerJobState = SchedulerJobState.REGISTERED
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    last_result: Any = None
    last_started_at: Optional[float] = None
    last_finished_at: Optional[float] = None
    last_duration_seconds: Optional[float] = None
    next_run_at: Optional[float] = None


class QSeriesBackgroundScheduler:
    def __init__(self, event_bus: Any = None, tick_seconds: float = 0.25):
        self.event_bus = event_bus
        self.tick_seconds = float(tick_seconds)
        self._lock = threading.RLock()
        self._jobs: Dict[str, ScheduledJob] = {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.started_at: Optional[float] = None
        self.stopped_at: Optional[float] = None

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

    def register_job(
        self,
        name: str,
        interval_seconds: float,
        job_callable: Callable[[], Any],
        run_immediately: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not name or not name.strip():
            raise BackgroundSchedulerError("Job name is required.")

        if interval_seconds <= 0:
            raise BackgroundSchedulerError("interval_seconds must be greater than zero.")

        if not callable(job_callable):
            raise BackgroundSchedulerError(f"Job '{name}' requires a callable.")

        clean_name = name.strip()

        with self._lock:
            if clean_name in self._jobs:
                raise BackgroundSchedulerError(f"Job already registered: {clean_name}")

            now = time.time()
            job = ScheduledJob(
                name=clean_name,
                interval_seconds=float(interval_seconds),
                job_callable=job_callable,
                run_immediately=bool(run_immediately),
                metadata=metadata or {},
                next_run_at=now if run_immediately else now + float(interval_seconds),
            )

            self._jobs[clean_name] = job

        self._emit(
            "ops.scheduler.job.registered",
            {
                "job": clean_name,
                "interval_seconds": float(interval_seconds),
                "run_immediately": bool(run_immediately),
                "timestamp": time.time(),
                "metadata": metadata or {},
            },
        )

        return {
            "status": "ok",
            "job": clean_name,
            "interval_seconds": float(interval_seconds),
            "state": job.state.value,
        }

    def unregister_job(self, name: str) -> Dict[str, Any]:
        with self._lock:
            if name not in self._jobs:
                raise BackgroundSchedulerError(f"Unknown job: {name}")
            del self._jobs[name]

        self._emit("ops.scheduler.job.unregistered", {"job": name, "timestamp": time.time()})

        return {"status": "ok", "job": name}

    def start(self) -> Dict[str, Any]:
        if self._thread and self._thread.is_alive():
            return {"status": "already_running"}

        self._stop_event.clear()
        self.started_at = time.time()
        self.stopped_at = None

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        self._emit("ops.scheduler.started", {"timestamp": self.started_at})

        return {"status": "started", "timestamp": self.started_at}

    def stop(self) -> Dict[str, Any]:
        self._stop_event.set()
        self.stopped_at = time.time()

        self._emit("ops.scheduler.stopping", {"timestamp": self.stopped_at})

        return {"status": "stopping", "timestamp": self.stopped_at}

    def pause_job(self, name: str) -> Dict[str, Any]:
        with self._lock:
            job = self._get_job_locked(name)
            job.state = SchedulerJobState.PAUSED

        self._emit("ops.scheduler.job.paused", {"job": name, "timestamp": time.time()})
        return {"status": "ok", "job": name, "state": SchedulerJobState.PAUSED.value}

    def resume_job(self, name: str) -> Dict[str, Any]:
        with self._lock:
            job = self._get_job_locked(name)
            job.state = SchedulerJobState.REGISTERED
            job.next_run_at = time.time() + job.interval_seconds

        self._emit("ops.scheduler.job.resumed", {"job": name, "timestamp": time.time()})
        return {"status": "ok", "job": name, "state": SchedulerJobState.REGISTERED.value}

    def run_job_now(self, name: str) -> Dict[str, Any]:
        with self._lock:
            job = self._get_job_locked(name)

        return self._execute_job(job)

    def _loop(self):
        while not self._stop_event.is_set():
            now = time.time()
            due_jobs = []

            with self._lock:
                for job in self._jobs.values():
                    if job.state == SchedulerJobState.PAUSED:
                        continue

                    if job.next_run_at is not None and now >= job.next_run_at:
                        due_jobs.append(job)

            for job in due_jobs:
                self._execute_job(job)

            self._stop_event.wait(self.tick_seconds)

        with self._lock:
            for job in self._jobs.values():
                if job.state == SchedulerJobState.RUNNING:
                    job.state = SchedulerJobState.STOPPED

        self._emit("ops.scheduler.stopped", {"timestamp": time.time()})

    def _execute_job(self, job: ScheduledJob) -> Dict[str, Any]:
        with self._lock:
            if job.state == SchedulerJobState.PAUSED:
                return {"status": "paused", "job": job.name}

            job.state = SchedulerJobState.RUNNING
            job.last_started_at = time.time()
            job.last_error = None

        self._emit("ops.scheduler.job.started", {"job": job.name, "timestamp": job.last_started_at})

        try:
            result = job.job_callable()
            finished = time.time()

            with self._lock:
                job.last_finished_at = finished
                job.last_duration_seconds = finished - (job.last_started_at or finished)
                job.last_result = result
                job.run_count += 1
                job.state = SchedulerJobState.REGISTERED
                job.next_run_at = finished + job.interval_seconds

            self._emit(
                "ops.scheduler.job.finished",
                {
                    "job": job.name,
                    "timestamp": finished,
                    "duration_seconds": job.last_duration_seconds,
                    "run_count": job.run_count,
                },
            )

            return {
                "status": "ok",
                "job": job.name,
                "result": result,
                "duration_seconds": job.last_duration_seconds,
            }

        except Exception as exc:
            finished = time.time()
            error = f"{exc}\n{traceback.format_exc()}"

            with self._lock:
                job.last_finished_at = finished
                job.last_duration_seconds = finished - (job.last_started_at or finished)
                job.last_error = error
                job.error_count += 1
                job.state = SchedulerJobState.ERROR
                job.next_run_at = finished + job.interval_seconds

            self._emit(
                "ops.scheduler.job.error",
                {
                    "job": job.name,
                    "timestamp": finished,
                    "error": str(exc),
                    "error_count": job.error_count,
                },
            )

            return {
                "status": "error",
                "job": job.name,
                "error": str(exc),
            }

    def _get_job_locked(self, name: str) -> ScheduledJob:
        if name not in self._jobs:
            raise BackgroundSchedulerError(f"Unknown job: {name}")
        return self._jobs[name]

    def job_status(self, name: str) -> Dict[str, Any]:
        with self._lock:
            job = self._get_job_locked(name)
            return {
                "name": job.name,
                "state": job.state.value,
                "interval_seconds": job.interval_seconds,
                "run_immediately": job.run_immediately,
                "run_count": job.run_count,
                "error_count": job.error_count,
                "last_error": job.last_error,
                "last_result": job.last_result,
                "last_started_at": job.last_started_at,
                "last_finished_at": job.last_finished_at,
                "last_duration_seconds": job.last_duration_seconds,
                "next_run_at": job.next_run_at,
                "metadata": dict(job.metadata),
            }

    def diagnostics(self) -> Dict[str, Any]:
        with self._lock:
            jobs = {name: self.job_status(name) for name in self._jobs.keys()}
            error_count = sum(1 for job in jobs.values() if job["error_count"] > 0)
            running_jobs = sum(1 for job in jobs.values() if job["state"] == SchedulerJobState.RUNNING.value)

            return {
                "module": "ops_002_background_scheduler",
                "status": "ok" if error_count == 0 else "warning",
                "scheduler_running": bool(self._thread and self._thread.is_alive()),
                "job_count": len(jobs),
                "running_jobs": running_jobs,
                "error_jobs": error_count,
                "started_at": self.started_at,
                "stopped_at": self.stopped_at,
                "tick_seconds": self.tick_seconds,
                "jobs": jobs,
            }


def build_background_scheduler(event_bus: Any = None, tick_seconds: float = 0.25) -> QSeriesBackgroundScheduler:
    return QSeriesBackgroundScheduler(event_bus=event_bus, tick_seconds=tick_seconds)


if __name__ == "__main__":
    scheduler = build_background_scheduler()
    print(scheduler.diagnostics())
