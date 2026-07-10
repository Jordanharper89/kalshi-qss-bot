from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
INTEGRATION = BASE / "integration"

MODULE_PATH = INTEGRATION / "oem_014_oracle_runtime_bootstrap_manager.py"
TEST_PATH = ROOT / "test_oem_014_oracle_runtime_bootstrap_manager.py"
INIT_PATH = INTEGRATION / "__init__.py"

MODULE_CODE = r'''"""
OEM-014 Oracle Runtime Bootstrap Manager

Clean production rewrite.

Purpose:
- Bootstrap migrated OEM Oracle engines into a runtime registration surface.
- Use OEM-011 as the canonical migrated-engine source.
- Avoid sending raw dict telemetry into the real OracleSignalBus.
- Avoid dependency on unknown runtime internals.
- Enforce Oracle read-only behavior.
- Prevent duplicate engine registration.
- Produce a stable RuntimeBootstrapReport.

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


BOOTSTRAP_ID = "oracle.engine_migration.runtime_bootstrap"
BOOTSTRAP_NAME = "Oracle Runtime Bootstrap Manager"
BOOTSTRAP_VERSION = "OEM-014.2"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BootstrapEngineHealth:
    engine_id: str
    status: str
    read_only: bool
    prediction_ready: bool
    health_status: str = "unknown"
    error: Optional[str] = None


@dataclass
class BootstrapRegistrationEntry:
    engine_id: str
    status: str
    read_only: bool
    registered: bool = False
    duplicate: bool = False
    registration_surface: Optional[str] = None
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
    registration_entries: List[Dict[str, Any]]
    engine_health: List[Dict[str, Any]]
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=_utc_now)


class BootstrapRuntimeSurface:
    """
    Minimal runtime surface for bootstrap replay/testing.

    It only stores read-only Oracle engines. It does not execute trades.
    """

    def __init__(self):
        self.engines: Dict[str, Any] = {}

    def register_engine(self, engine: Any) -> None:
        self.engines[getattr(engine, "engine_id")] = engine

    def list_engines(self) -> List[str]:
        return list(self.engines.keys())


class BootstrapSignalBus:
    """
    Bootstrap-safe signal bus.

    It records bootstrap telemetry only. It does not replace the canonical
    OracleSignalBus and does not emit prediction signals.
    """

    status = "ready"

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def record_event(self, event: Dict[str, Any]) -> None:
        self.events.append(dict(event))


class BootstrapAggregator:
    """
    Bootstrap-safe aggregator.

    It validates that registered engines can produce prediction-like objects.
    """

    status = "ready"

    def __init__(self, runtime: Any):
        self.runtime = runtime

    def collect_predictions(self, payload: Dict[str, Any]) -> List[Any]:
        predictions: List[Any] = []
        engines = getattr(self.runtime, "engines", {})
        if not isinstance(engines, dict):
            return predictions

        for engine in engines.values():
            predict = getattr(engine, "predict", None)
            if callable(predict):
                try:
                    result = predict(payload)
                    if isinstance(result, list):
                        predictions.extend(result)
                except Exception:
                    continue

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

        signal_bus = BootstrapSignalBus()
        aggregator = BootstrapAggregator(runtime)

        engines = self._discover_engines()
        registration_entries = self._register_engines(runtime, engines)

        engine_health = self._check_engine_health(runtime)

        registered_count = sum(1 for entry in registration_entries if entry.registered)
        duplicate_count = sum(1 for entry in registration_entries if entry.duplicate)
        failed_count = sum(1 for entry in registration_entries if entry.status == "failed")
        healthy_count = sum(1 for item in engine_health if item.status == "healthy")

        runtime_status = self._resolve_runtime_status(
            discovered_count=len(engines),
            registered_count=registered_count,
            duplicate_count=duplicate_count,
            failed_count=failed_count,
            healthy_count=healthy_count,
        )

        signal_bus.record_event(
            {
                "event_type": "oracle_runtime_bootstrap",
                "bootstrap_id": self.bootstrap_id,
                "runtime_status": runtime_status,
                "discovered_engines": len(engines),
                "registered_engines": registered_count,
                "duplicate_count": duplicate_count,
                "failed_registrations": failed_count,
                "healthy_engines": healthy_count,
                "read_only": True,
                "created_at": _utc_now(),
            }
        )

        return RuntimeBootstrapReport(
            bootstrap_id=self.bootstrap_id,
            status="pass" if runtime_status == "ready" else "fail",
            runtime_status=runtime_status,
            discovered_engines=len(engines),
            registered_engines=registered_count,
            duplicate_count=duplicate_count,
            failed_registrations=failed_count,
            healthy_engines=healthy_count,
            read_only=True,
            signal_bus_status=signal_bus.status,
            aggregator_status=aggregator.status,
            registration_entries=[entry.__dict__ for entry in registration_entries],
            engine_health=[item.__dict__ for item in engine_health],
            telemetry={
                "bootstrap": self.name,
                "version": self.version,
                "read_only": True,
                "runtime_surface": type(runtime).__name__,
                "signal_bus_surface": type(signal_bus).__name__,
                "aggregator_surface": type(aggregator).__name__,
                "bootstrap_event_count": len(signal_bus.events),
                "generated_at": _utc_now(),
            },
        )

    def _discover_engines(self) -> List[Any]:
        from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import (
            OracleEngineMigrationRegistryBridge,
        )

        bridge = OracleEngineMigrationRegistryBridge(runtime_paths=self.runtime_paths)
        return bridge.build_all()

    def _register_engines(self, runtime: Any, engines: List[Any]) -> List[BootstrapRegistrationEntry]:
        existing = self._existing_engine_ids(runtime)
        entries: List[BootstrapRegistrationEntry] = []

        for engine in engines:
            engine_id = str(getattr(engine, "engine_id", "unknown"))

            try:
                if engine_id == "unknown":
                    entries.append(
                        BootstrapRegistrationEntry(
                            engine_id=engine_id,
                            status="failed",
                            read_only=False,
                            error="engine missing engine_id",
                        )
                    )
                    continue

                read_only = bool(getattr(engine, "read_only", False))
                if not read_only:
                    entries.append(
                        BootstrapRegistrationEntry(
                            engine_id=engine_id,
                            status="failed",
                            read_only=False,
                            error="engine is not read_only",
                        )
                    )
                    continue

                if engine_id in existing:
                    entries.append(
                        BootstrapRegistrationEntry(
                            engine_id=engine_id,
                            status="duplicate",
                            read_only=True,
                            registered=False,
                            duplicate=True,
                            error="engine already registered",
                        )
                    )
                    continue

                surface = self._register_one(runtime, engine)
                existing.add(engine_id)

                entries.append(
                    BootstrapRegistrationEntry(
                        engine_id=engine_id,
                        status="registered",
                        read_only=True,
                        registered=True,
                        duplicate=False,
                        registration_surface=surface,
                    )
                )

            except Exception as exc:
                entries.append(
                    BootstrapRegistrationEntry(
                        engine_id=engine_id,
                        status="failed",
                        read_only=bool(getattr(engine, "read_only", False)),
                        error=str(exc),
                    )
                )

        return entries

    def _register_one(self, runtime: Any, engine: Any) -> str:
        for method_name in ("register_engine", "register", "add_engine"):
            method = getattr(runtime, method_name, None)
            if callable(method):
                method(engine)
                return f"runtime.{method_name}"

        registry = getattr(runtime, "registry", None)
        if registry is not None:
            for method_name in ("register_engine", "register", "add_engine"):
                method = getattr(registry, method_name, None)
                if callable(method):
                    method(engine)
                    return f"runtime.registry.{method_name}"

            registry_engines = getattr(registry, "engines", None)
            if isinstance(registry_engines, dict):
                registry_engines[getattr(engine, "engine_id")] = engine
                return "runtime.registry.engines"

        engines = getattr(runtime, "engines", None)
        if isinstance(engines, dict):
            engines[getattr(engine, "engine_id")] = engine
            return "runtime.engines"

        raise AttributeError("runtime does not expose a supported engine registration surface")

    def _existing_engine_ids(self, runtime: Any) -> Set[str]:
        found: Set[str] = set()

        engines = getattr(runtime, "engines", None)
        if isinstance(engines, dict):
            found.update(str(key) for key in engines.keys())

        for method_name in ("list_engines", "engine_ids", "registered_engine_ids"):
            method = getattr(runtime, method_name, None)
            if callable(method):
                try:
                    value = method()
                    found.update(self._coerce_engine_ids(value))
                except Exception:
                    pass

        registry = getattr(runtime, "registry", None)
        if registry is not None:
            registry_engines = getattr(registry, "engines", None)
            if isinstance(registry_engines, dict):
                found.update(str(key) for key in registry_engines.keys())

            for method_name in ("list_engines", "engine_ids", "registered_engine_ids"):
                method = getattr(registry, method_name, None)
                if callable(method):
                    try:
                        value = method()
                        found.update(self._coerce_engine_ids(value))
                    except Exception:
                        pass

        return found

    def _coerce_engine_ids(self, value: Any) -> Set[str]:
        if isinstance(value, dict):
            return {str(key) for key in value.keys()}
        if isinstance(value, (list, tuple, set)):
            return {str(item) for item in value}
        return set()

    def _check_engine_health(self, runtime: Any) -> List[BootstrapEngineHealth]:
        engines = getattr(runtime, "engines", {})
        if not isinstance(engines, dict):
            engines = {}

        results: List[BootstrapEngineHealth] = []

        for engine_id, engine in engines.items():
            engine_id = str(engine_id)

            try:
                read_only = bool(getattr(engine, "read_only", False))
                if not read_only:
                    results.append(
                        BootstrapEngineHealth(
                            engine_id=engine_id,
                            status="failed",
                            read_only=False,
                            prediction_ready=False,
                            error="engine is not read_only",
                        )
                    )
                    continue

                health_status = self._engine_health_status(engine)
                prediction_ready = self._prediction_ready(engine)

                results.append(
                    BootstrapEngineHealth(
                        engine_id=engine_id,
                        status="healthy" if prediction_ready else "failed",
                        read_only=True,
                        prediction_ready=prediction_ready,
                        health_status=health_status,
                        error=None if prediction_ready else "engine did not produce prediction",
                    )
                )

            except Exception as exc:
                results.append(
                    BootstrapEngineHealth(
                        engine_id=engine_id,
                        status="failed",
                        read_only=bool(getattr(engine, "read_only", False)),
                        prediction_ready=False,
                        error=str(exc),
                    )
                )

        return results

    def _engine_health_status(self, engine: Any) -> str:
        health = getattr(engine, "health", None)
        if not callable(health):
            return "unknown"

        try:
            value = health()
            if isinstance(value, dict):
                return str(value.get("status", "unknown"))
        except Exception:
            return "error"

        return "unknown"

    def _prediction_ready(self, engine: Any) -> bool:
        predict = getattr(engine, "predict", None)
        if not callable(predict):
            return False

        engine_id = str(getattr(engine, "engine_id", "unknown"))
        market_id = f"OEM014-{engine_id.upper().replace('.', '-')}-YES"

        payload = {
            "market_id": market_id,
            "resolved_market_id": market_id,
            "related_market_id": "OEM014-RELATED-MARKET",
            "query": "OEM-014 bootstrap readiness query",
            "adapter_id": "bootstrap.adapter",
            "query_id": "bootstrap.query",
            "ledger_key": "bootstrap.ledger",
            "sample_size": 25,
            "score": 0.44,
            "edge": 0.44,
            "confidence": 0.84,
            "relationship_score": 0.44,
            "influence_score": 0.44,
            "sentiment_score": 0.44,
            "discovery_score": 0.44,
            "recall_score": 0.44,
            "audit_score": 0.44,
            "resolver_score": 0.44,
        }

        try:
            predictions = predict(payload)
            return isinstance(predictions, list) and len(predictions) >= 1
        except Exception:
            return False

    def _resolve_runtime_status(
        self,
        discovered_count: int,
        registered_count: int,
        duplicate_count: int,
        failed_count: int,
        healthy_count: int,
    ) -> str:
        if failed_count > 0:
            return "degraded"

        if discovered_count <= 0:
            return "degraded"

        if registered_count == discovered_count and healthy_count == registered_count:
            return "ready"

        if duplicate_count == discovered_count and registered_count == 0:
            return "degraded"

        return "degraded"


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
    "BootstrapRegistrationEntry",
    "RuntimeBootstrapReport",
    "OracleRuntimeBootstrapManager",
    "build_bootstrap_manager",
    "bootstrap_oracle_runtime",
]
'''

TEST_CODE = r'''from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import MIGRATED_ENGINE_SPECS
from qseries_v2.integration.oem_014_oracle_runtime_bootstrap_manager import (
    BOOTSTRAP_ID,
    BootstrapRuntimeSurface,
    OracleRuntimeBootstrapManager,
    bootstrap_oracle_runtime,
    build_bootstrap_manager,
)


class DummyRuntime:
    def __init__(self):
        self.engines = {}

    def register_engine(self, engine):
        self.engines[engine.engine_id] = engine

    def list_engines(self):
        return list(self.engines.keys())


def test_oem_014_bootstrap_with_default_runtime_surface():
    report = bootstrap_oracle_runtime()

    assert report.bootstrap_id == BOOTSTRAP_ID
    assert report.status == "pass"
    assert report.runtime_status == "ready"
    assert report.discovered_engines == len(MIGRATED_ENGINE_SPECS)
    assert report.registered_engines == len(MIGRATED_ENGINE_SPECS)
    assert report.failed_registrations == 0
    assert report.healthy_engines == len(MIGRATED_ENGINE_SPECS)
    assert report.read_only is True
    assert report.signal_bus_status == "ready"
    assert report.aggregator_status == "ready"


def test_oem_014_bootstrap_with_external_runtime_surface():
    runtime = DummyRuntime()
    report = bootstrap_oracle_runtime(runtime=runtime)

    assert report.status == "pass"
    assert report.runtime_status == "ready"
    assert len(runtime.engines) == len(MIGRATED_ENGINE_SPECS)
    assert report.registered_engines == len(MIGRATED_ENGINE_SPECS)
    assert report.healthy_engines == len(MIGRATED_ENGINE_SPECS)


def test_oem_014_bootstrap_prevents_duplicate_registration():
    runtime = DummyRuntime()

    first = bootstrap_oracle_runtime(runtime=runtime)
    second = bootstrap_oracle_runtime(runtime=runtime)

    assert first.status == "pass"
    assert first.runtime_status == "ready"
    assert second.status == "fail"
    assert second.runtime_status == "degraded"
    assert second.duplicate_count == len(MIGRATED_ENGINE_SPECS)
    assert second.registered_engines == 0
    assert len(runtime.engines) == len(MIGRATED_ENGINE_SPECS)


def test_oem_014_bootstrap_runtime_surface_shape():
    runtime = BootstrapRuntimeSurface()
    manager = build_bootstrap_manager()
    report = manager.bootstrap(runtime=runtime)

    assert isinstance(runtime.engines, dict)
    assert report.telemetry["runtime_surface"] == "BootstrapRuntimeSurface"
    assert report.telemetry["read_only"] is True
    assert report.telemetry["bootstrap_event_count"] == 1


def test_oem_014_manager_shape():
    manager = OracleRuntimeBootstrapManager()

    assert manager.bootstrap_id == BOOTSTRAP_ID
    assert manager.read_only is True


if __name__ == "__main__":
    test_oem_014_bootstrap_with_default_runtime_surface()
    test_oem_014_bootstrap_with_external_runtime_surface()
    test_oem_014_bootstrap_prevents_duplicate_registration()
    test_oem_014_bootstrap_runtime_surface_shape()
    test_oem_014_manager_shape()

    report = bootstrap_oracle_runtime()

    print("[PASS] OEM-014 Oracle Runtime Bootstrap Manager")
    print(
        {
            "runtime_status": report.runtime_status,
            "registered_engines": report.registered_engines,
            "healthy_engines": report.healthy_engines,
            "duplicates": report.duplicate_count,
            "signal_bus": report.signal_bus_status,
            "aggregator": report.aggregator_status,
            "read_only": report.read_only,
        }
    )
'''

def ensure_dirs():
    INTEGRATION.mkdir(parents=True, exist_ok=True)


def update_init():
    INIT_PATH.touch(exist_ok=True)
    text = INIT_PATH.read_text(encoding="utf-8")

    line = (
        "from .oem_014_oracle_runtime_bootstrap_manager import "
        "OracleRuntimeBootstrapManager, bootstrap_oracle_runtime"
    )

    exports = [
        '"OracleRuntimeBootstrapManager"',
        '"bootstrap_oracle_runtime"',
    ]

    if line not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"

    if "__all__" not in text:
        text += "\n__all__ = []\n"

    for item in exports:
        if item not in text:
            text = text.replace("__all__ = [", f"__all__ = [\n    {item},")

    INIT_PATH.write_text(text, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OEM-014.2 INSTALLER")
    print(" Clean Oracle Runtime Bootstrap Manager Rewrite")
    print("=" * 40)

    ensure_dirs()

    MODULE_PATH.write_text(MODULE_CODE, encoding="utf-8")
    print(f"[OK] Rewrote {MODULE_PATH}")

    TEST_PATH.write_text(TEST_CODE, encoding="utf-8")
    print(f"[OK] Rewrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print("\n[DONE] OEM-014.2 installed")
    print("\nRun:")
    print("py test_oem_014_oracle_runtime_bootstrap_manager.py")


if __name__ == "__main__":
    main()