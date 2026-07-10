from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
INTEGRATION = BASE / "integration"

MODULE_PATH = INTEGRATION / "oem_014_oracle_runtime_bootstrap_manager.py"

MODULE_CODE = r'''"""
OEM-014 Oracle Runtime Bootstrap Manager

Bootstraps migrated OEM Oracle engines into a runtime-like registration surface
using the already-installed OEM migration registry and auto-discovery manager.

Built on:
- OEM-011 Oracle Engine Migration Registry Bridge
- OEM-013 Oracle Runtime Auto-Discovery Registration Manager

OEM-014.1 fix:
- Do not emit raw dict events into the real OracleSignalBus.
- The real OracleSignalBus expects CanonicalPrediction-like objects.
- Bootstrap telemetry remains in RuntimeBootstrapReport.
- Dict event emission is limited to BootstrapSignalBus fallback only.

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


BOOTSTRAP_ID = "oracle.engine_migration.runtime_bootstrap"
BOOTSTRAP_NAME = "Oracle Runtime Bootstrap Manager"
BOOTSTRAP_VERSION = "OEM-014.1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BootstrapEngineHealth:
    engine_id: str
    status: str
    read_only: bool
    health_status: Optional[str] = None
    prediction_ready: bool = False
    error: Optional[str] = None


@dataclass
class RuntimeBootstrapReport:
    bootstrap_id: str
    status: str
    runtime_status: str
    discovered_engines: int
    registered_engines: int
    duplicate_count: int
    failed_registrations: int
    healthy_engines: int
    read_only: bool
    signal_bus_status: str
    aggregator_status: str
    engine_health: List[Dict[str, Any]]
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=_utc_now)


class BootstrapRuntimeSurface:
    def __init__(self):
        self.engines: Dict[str, Any] = {}

    def register_engine(self, engine: Any) -> None:
        self.engines[getattr(engine, "engine_id")] = engine

    def list_engines(self) -> List[str]:
        return list(self.engines.keys())


class BootstrapSignalBus:
    def __init__(self):
        self.status = "ready"
        self.events: List[Dict[str, Any]] = []

    def emit(self, event: Dict[str, Any]) -> None:
        self.events.append(dict(event))


class BootstrapAggregator:
    def __init__(self, runtime: Any):
        self.runtime = runtime
        self.status = "ready"

    def collect_predictions(self, payload: Dict[str, Any]) -> List[Any]:
        predictions: List[Any] = []
        for engine in getattr(self.runtime, "engines", {}).values():
            predict = getattr(engine, "predict", None)
            if callable(predict):
                result = predict(payload)
                if isinstance(result, list):
                    predictions.extend(result)
        return predictions


class OracleRuntimeBootstrapManager:
    bootstrap_id = BOOTSTRAP_ID
    name = BOOTSTRAP_NAME
    version = BOOTSTRAP_VERSION
    read_only = True

    def __init__(self, runtime_paths: Optional[Any] = None):
        self.runtime_paths = runtime_paths

    def bootstrap(self, runtime: Optional[Any] = None) -> RuntimeBootstrapReport:
        runtime = runtime or BootstrapRuntimeSurface()
        signal_bus = self._build_signal_bus()
        registration_report = self._register_engines(runtime)
        aggregator = self._build_aggregator(runtime)

        engine_health = self._check_registered_engine_health(runtime)
        healthy_count = sum(1 for item in engine_health if item.status == "healthy")

        runtime_status = "ready" if (
            registration_report.failed_count == 0
            and healthy_count == registration_report.registered_count
            and self._get_status(signal_bus) == "ready"
            and self._get_status(aggregator) == "ready"
        ) else "degraded"

        self._safe_emit_bootstrap_event(
            signal_bus,
            {
                "event_type": "oracle_runtime_bootstrap",
                "bootstrap_id": self.bootstrap_id,
                "runtime_status": runtime_status,
                "registered_engines": registration_report.registered_count,
                "healthy_engines": healthy_count,
                "read_only": True,
                "created_at": _utc_now(),
            },
        )

        status = "pass" if runtime_status == "ready" else "fail"

        return RuntimeBootstrapReport(
            bootstrap_id=self.bootstrap_id,
            status=status,
            runtime_status=runtime_status,
            discovered_engines=registration_report.discovered_count,
            registered_engines=registration_report.registered_count,
            duplicate_count=registration_report.duplicate_count,
            failed_registrations=registration_report.failed_count,
            healthy_engines=healthy_count,
            read_only=True,
            signal_bus_status=self._get_status(signal_bus),
            aggregator_status=self._get_status(aggregator),
            engine_health=[item.__dict__ for item in engine_health],
            telemetry={
                "bootstrap": self.name,
                "version": self.version,
                "read_only": True,
                "runtime_surface": type(runtime).__name__,
                "signal_bus_surface": type(signal_bus).__name__,
                "aggregator_surface": type(aggregator).__name__,
                "bootstrap_event_recorded": isinstance(signal_bus, BootstrapSignalBus),
                "generated_at": _utc_now(),
            },
        )

    def _safe_emit_bootstrap_event(self, signal_bus: Any, event: Dict[str, Any]) -> None:
        if isinstance(signal_bus, BootstrapSignalBus):
            signal_bus.emit(event)

    def _register_engines(self, runtime: Any) -> Any:
        from qseries_v2.integration.oem_013_oracle_runtime_auto_discovery_registration_manager import (
            auto_register_migrated_oracle_engines,
        )

        return auto_register_migrated_oracle_engines(runtime, runtime_paths=self.runtime_paths)

    def _build_signal_bus(self) -> Any:
        try:
            from qseries_v2.integration.oracle_signal_bus import OracleSignalBus

            try:
                return OracleSignalBus(runtime_paths=self.runtime_paths)
            except TypeError:
                return OracleSignalBus()
        except Exception:
            return BootstrapSignalBus()

    def _build_aggregator(self, runtime: Any) -> Any:
        try:
            from qseries_v2.integration.multi_engine_oracle_aggregator import MultiEngineOracleAggregator

            try:
                return MultiEngineOracleAggregator(runtime=runtime, runtime_paths=self.runtime_paths)
            except TypeError:
                try:
                    return MultiEngineOracleAggregator(runtime)
                except TypeError:
                    return MultiEngineOracleAggregator()
        except Exception:
            return BootstrapAggregator(runtime)

    def _check_registered_engine_health(self, runtime: Any) -> List[BootstrapEngineHealth]:
        engines = getattr(runtime, "engines", {})
        if not isinstance(engines, dict):
            engines = {}

        results: List[BootstrapEngineHealth] = []

        for engine_id, engine in engines.items():
            try:
                read_only = bool(getattr(engine, "read_only", False))
                if not read_only:
                    results.append(
                        BootstrapEngineHealth(
                            engine_id=str(engine_id),
                            status="failed",
                            read_only=False,
                            error="engine is not read_only",
                        )
                    )
                    continue

                health_status = "unknown"
                health = getattr(engine, "health", None)
                if callable(health):
                    health_result = health()
                    if isinstance(health_result, dict):
                        health_status = health_result.get("status", "unknown")

                prediction_ready = self._engine_prediction_ready(engine)

                results.append(
                    BootstrapEngineHealth(
                        engine_id=str(engine_id),
                        status="healthy" if prediction_ready else "failed",
                        read_only=True,
                        health_status=health_status,
                        prediction_ready=prediction_ready,
                        error=None if prediction_ready else "engine did not produce prediction",
                    )
                )

            except Exception as exc:
                results.append(
                    BootstrapEngineHealth(
                        engine_id=str(engine_id),
                        status="failed",
                        read_only=bool(getattr(engine, "read_only", False)),
                        error=str(exc),
                    )
                )

        return results

    def _engine_prediction_ready(self, engine: Any) -> bool:
        predict = getattr(engine, "predict", None)
        if not callable(predict):
            return False

        engine_id = getattr(engine, "engine_id", "unknown")
        market_id = f"OEM014-{str(engine_id).upper().replace('.', '-')}"

        payload = {
            "market_id": market_id,
            "score": 0.41,
            "edge": 0.41,
            "confidence": 0.84,
            "relationship_score": 0.41,
            "influence_score": 0.41,
            "sentiment_score": 0.41,
            "discovery_score": 0.41,
            "recall_score": 0.41,
            "audit_score": 0.41,
            "resolver_score": 0.41,
            "resolved_market_id": market_id,
            "query": "OEM-014 bootstrap readiness query",
        }

        result = predict(payload)
        return isinstance(result, list) and len(result) >= 1

    def _get_status(self, component: Any) -> str:
        status = getattr(component, "status", None)
        if isinstance(status, str):
            return status

        health = getattr(component, "health", None)
        if callable(health):
            try:
                value = health()
                if isinstance(value, dict):
                    return str(value.get("status", "unknown"))
            except Exception:
                return "unknown"

        return "ready"


def build_bootstrap_manager(runtime_paths: Optional[Any] = None) -> OracleRuntimeBootstrapManager:
    return OracleRuntimeBootstrapManager(runtime_paths=runtime_paths)


def bootstrap_oracle_runtime(
    runtime: Optional[Any] = None,
    runtime_paths: Optional[Any] = None,
) -> RuntimeBootstrapReport:
    return build_bootstrap_manager(runtime_paths=runtime_paths).bootstrap(runtime=runtime)


__all__ = [
    "BOOTSTRAP_ID",
    "BOOTSTRAP_NAME",
    "BOOTSTRAP_VERSION",
    "BootstrapRuntimeSurface",
    "BootstrapSignalBus",
    "BootstrapAggregator",
    "BootstrapEngineHealth",
    "RuntimeBootstrapReport",
    "OracleRuntimeBootstrapManager",
    "build_bootstrap_manager",
    "bootstrap_oracle_runtime",
]
'''

def main():
    print("=" * 40)
    print(" OEM-014.1 INSTALLER")
    print(" Oracle Runtime Bootstrap Signal Bus Fix")
    print("=" * 40)

    MODULE_PATH.write_text(MODULE_CODE, encoding="utf-8")
    print(f"[OK] Rewrote {MODULE_PATH}")

    print("\n[DONE] OEM-014.1 installed")
    print("\nRun:")
    print("py test_oem_014_oracle_runtime_bootstrap_manager.py")


if __name__ == "__main__":
    main()