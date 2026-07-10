from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import MIGRATED_ENGINE_SPECS
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
