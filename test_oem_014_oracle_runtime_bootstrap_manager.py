from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import MIGRATED_ENGINE_SPECS
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
