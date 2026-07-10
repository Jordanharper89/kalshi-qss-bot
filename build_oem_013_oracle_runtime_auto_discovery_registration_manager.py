from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
INTEGRATION = BASE / "integration"

MODULE_PATH = INTEGRATION / "oem_013_oracle_runtime_auto_discovery_registration_manager.py"
TEST_PATH = ROOT / "test_oem_013_oracle_runtime_auto_discovery_registration_manager.py"
INIT_PATH = INTEGRATION / "__init__.py"

MODULE_CODE = r'''"""
OEM-013 Oracle Runtime Auto-Discovery Registration Manager

Auto-discovers migrated OEM Oracle engines and registers them with the
canonical Oracle Runtime registration surface.

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


MANAGER_ID = "oracle.engine_migration.runtime_auto_registration"
MANAGER_NAME = "Oracle Runtime Auto-Discovery Registration Manager"
MANAGER_VERSION = "OEM-013"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RuntimeRegistrationEntry:
    engine_id: str
    status: str
    read_only: bool
    registered: bool = False
    duplicate: bool = False
    registration_surface: Optional[str] = None
    error: Optional[str] = None
    registered_at: Optional[str] = None


@dataclass
class RuntimeRegistrationReport:
    manager_id: str
    status: str
    discovered_count: int
    registered_count: int
    duplicate_count: int
    failed_count: int
    entries: List[Dict[str, Any]]
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=_utc_now)


class OracleRuntimeAutoDiscoveryRegistrationManager:
    manager_id = MANAGER_ID
    name = MANAGER_NAME
    version = MANAGER_VERSION
    read_only = True

    def __init__(self, runtime_paths: Optional[Any] = None):
        self.runtime_paths = runtime_paths

    def discover_engines(self) -> List[Any]:
        from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import (
            OracleEngineMigrationRegistryBridge,
        )

        bridge = OracleEngineMigrationRegistryBridge(runtime_paths=self.runtime_paths)
        return bridge.build_all()

    def register_discovered(self, runtime: Any) -> RuntimeRegistrationReport:
        engines = self.discover_engines()
        existing = self._existing_engine_ids(runtime)
        entries: List[RuntimeRegistrationEntry] = []

        for engine in engines:
            entries.append(self._register_one(runtime, engine, existing))

        registered_count = sum(1 for entry in entries if entry.registered)
        duplicate_count = sum(1 for entry in entries if entry.duplicate)
        failed_count = sum(1 for entry in entries if entry.status == "failed")
        status = "pass" if failed_count == 0 else "fail"

        return RuntimeRegistrationReport(
            manager_id=self.manager_id,
            status=status,
            discovered_count=len(engines),
            registered_count=registered_count,
            duplicate_count=duplicate_count,
            failed_count=failed_count,
            entries=[entry.__dict__ for entry in entries],
            telemetry={
                "manager": self.name,
                "version": self.version,
                "read_only": True,
                "runtime_registration": "auto_discovery",
                "generated_at": _utc_now(),
            },
        )

    def _register_one(self, runtime: Any, engine: Any, existing: Set[str]) -> RuntimeRegistrationEntry:
        try:
            engine_id = getattr(engine, "engine_id", None)
            if not engine_id:
                return RuntimeRegistrationEntry(
                    engine_id="unknown",
                    status="failed",
                    read_only=False,
                    error="engine missing engine_id",
                )

            read_only = bool(getattr(engine, "read_only", False))
            if not read_only:
                return RuntimeRegistrationEntry(
                    engine_id=engine_id,
                    status="failed",
                    read_only=False,
                    error="engine is not read_only",
                )

            if engine_id in existing:
                return RuntimeRegistrationEntry(
                    engine_id=engine_id,
                    status="duplicate",
                    read_only=True,
                    registered=False,
                    duplicate=True,
                    error="engine already registered",
                )

            surface = self._register_engine(runtime, engine)
            existing.add(engine_id)

            return RuntimeRegistrationEntry(
                engine_id=engine_id,
                status="registered",
                read_only=True,
                registered=True,
                duplicate=False,
                registration_surface=surface,
                registered_at=_utc_now(),
            )

        except Exception as exc:
            return RuntimeRegistrationEntry(
                engine_id=str(getattr(engine, "engine_id", "unknown")),
                status="failed",
                read_only=bool(getattr(engine, "read_only", False)),
                error=str(exc),
            )

    def _existing_engine_ids(self, runtime: Any) -> Set[str]:
        found: Set[str] = set()

        engines = getattr(runtime, "engines", None)
        if isinstance(engines, dict):
            found.update(str(key) for key in engines.keys())

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
                        if isinstance(value, dict):
                            found.update(str(key) for key in value.keys())
                        elif isinstance(value, list):
                            found.update(str(item) for item in value)
                        elif isinstance(value, set):
                            found.update(str(item) for item in value)
                    except Exception:
                        pass

        for method_name in ("list_engines", "engine_ids", "registered_engine_ids"):
            method = getattr(runtime, method_name, None)
            if callable(method):
                try:
                    value = method()
                    if isinstance(value, dict):
                        found.update(str(key) for key in value.keys())
                    elif isinstance(value, list):
                        found.update(str(item) for item in value)
                    elif isinstance(value, set):
                        found.update(str(item) for item in value)
                except Exception:
                    pass

        return found

    def _register_engine(self, runtime: Any, engine: Any) -> str:
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

        raise AttributeError("runtime does not expose a supported registration surface")


def build_manager(runtime_paths: Optional[Any] = None) -> OracleRuntimeAutoDiscoveryRegistrationManager:
    return OracleRuntimeAutoDiscoveryRegistrationManager(runtime_paths=runtime_paths)


def auto_register_migrated_oracle_engines(
    runtime: Any,
    runtime_paths: Optional[Any] = None,
) -> RuntimeRegistrationReport:
    return build_manager(runtime_paths=runtime_paths).register_discovered(runtime)


__all__ = [
    "MANAGER_ID",
    "MANAGER_NAME",
    "MANAGER_VERSION",
    "RuntimeRegistrationEntry",
    "RuntimeRegistrationReport",
    "OracleRuntimeAutoDiscoveryRegistrationManager",
    "build_manager",
    "auto_register_migrated_oracle_engines",
]
'''

TEST_CODE = r'''from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import MIGRATED_ENGINE_SPECS
from qseries_v2.integration.oem_013_oracle_runtime_auto_discovery_registration_manager import (
    MANAGER_ID,
    OracleRuntimeAutoDiscoveryRegistrationManager,
    auto_register_migrated_oracle_engines,
    build_manager,
)


class DummyRuntime:
    def __init__(self):
        self.engines = {}

    def register_engine(self, engine):
        self.engines[engine.engine_id] = engine

    def list_engines(self):
        return list(self.engines.keys())


def test_oem_013_manager_discovers_engines():
    manager = build_manager()
    engines = manager.discover_engines()

    assert len(engines) == len(MIGRATED_ENGINE_SPECS)
    assert all(getattr(engine, "read_only", False) is True for engine in engines)


def test_oem_013_manager_registers_discovered_engines():
    runtime = DummyRuntime()
    report = auto_register_migrated_oracle_engines(runtime)

    assert report.manager_id == MANAGER_ID
    assert report.status == "pass"
    assert report.discovered_count == len(MIGRATED_ENGINE_SPECS)
    assert report.registered_count == len(MIGRATED_ENGINE_SPECS)
    assert report.failed_count == 0
    assert len(runtime.engines) == len(MIGRATED_ENGINE_SPECS)


def test_oem_013_manager_blocks_duplicates():
    runtime = DummyRuntime()

    first = auto_register_migrated_oracle_engines(runtime)
    second = auto_register_migrated_oracle_engines(runtime)

    assert first.status == "pass"
    assert second.status == "pass"
    assert second.registered_count == 0
    assert second.duplicate_count == len(MIGRATED_ENGINE_SPECS)
    assert len(runtime.engines) == len(MIGRATED_ENGINE_SPECS)


def test_oem_013_registered_engines_emit_predictions():
    runtime = DummyRuntime()
    auto_register_migrated_oracle_engines(runtime)

    for engine_id, engine in runtime.engines.items():
        predictions = engine.predict(
            {
                "market_id": f"OEM013-{engine_id.upper().replace('.', '-')}",
                "score": 0.45,
                "edge": 0.45,
                "confidence": 0.84,
            }
        )

        assert isinstance(predictions, list)
        assert len(predictions) >= 1


def test_oem_013_manager_shape():
    manager = OracleRuntimeAutoDiscoveryRegistrationManager()

    assert manager.manager_id == MANAGER_ID
    assert manager.read_only is True


if __name__ == "__main__":
    test_oem_013_manager_discovers_engines()
    test_oem_013_manager_registers_discovered_engines()
    test_oem_013_manager_blocks_duplicates()
    test_oem_013_registered_engines_emit_predictions()
    test_oem_013_manager_shape()

    runtime = DummyRuntime()
    report = auto_register_migrated_oracle_engines(runtime)

    print("[PASS] OEM-013 Oracle Runtime Auto-Discovery Registration Manager")
    print(
        {
            "manager_id": report.manager_id,
            "status": report.status,
            "discovered_count": report.discovered_count,
            "registered_count": report.registered_count,
            "duplicate_count": report.duplicate_count,
            "failed_count": report.failed_count,
            "runtime_engines": len(runtime.engines),
        }
    )
'''

def ensure_dirs():
    INTEGRATION.mkdir(parents=True, exist_ok=True)


def update_init():
    INIT_PATH.touch(exist_ok=True)
    text = INIT_PATH.read_text(encoding="utf-8")

    line = (
        "from .oem_013_oracle_runtime_auto_discovery_registration_manager import "
        "OracleRuntimeAutoDiscoveryRegistrationManager, auto_register_migrated_oracle_engines"
    )

    exports = [
        '"OracleRuntimeAutoDiscoveryRegistrationManager"',
        '"auto_register_migrated_oracle_engines"',
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
    print(" OEM-013 INSTALLER")
    print(" Oracle Runtime Auto-Discovery Registration Manager")
    print("=" * 40)

    ensure_dirs()

    MODULE_PATH.write_text(MODULE_CODE, encoding="utf-8")
    print(f"[OK] Wrote {MODULE_PATH}")

    TEST_PATH.write_text(TEST_CODE, encoding="utf-8")
    print(f"[OK] Wrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print("\n[DONE] OEM-013 installed")
    print("\nRun:")
    print("py test_oem_013_oracle_runtime_auto_discovery_registration_manager.py")


if __name__ == "__main__":
    main()