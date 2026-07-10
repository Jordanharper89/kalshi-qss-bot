from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import (
    BRIDGE_ID,
    MIGRATED_ENGINE_SPECS,
    OracleEngineMigrationRegistryBridge,
    build_bridge,
    register_migrated_oracle_engines,
)


class DummyRuntime:
    def __init__(self):
        self.engines = {}

    def register_engine(self, engine):
        self.engines[engine.engine_id] = engine


def test_oem_011_bridge_lists_specs():
    bridge = build_bridge()
    specs = bridge.list_specs()

    assert len(specs) == len(MIGRATED_ENGINE_SPECS)
    assert all("engine_id" in spec for spec in specs)
    assert all("module" in spec for spec in specs)
    assert all("class_name" in spec for spec in specs)


def test_oem_011_bridge_builds_all_engines():
    bridge = build_bridge()
    engines = bridge.build_all()

    assert len(engines) == len(MIGRATED_ENGINE_SPECS)

    engine_ids = {engine.engine_id for engine in engines}
    expected_ids = {spec["engine_id"] for spec in MIGRATED_ENGINE_SPECS}

    assert engine_ids == expected_ids
    assert all(getattr(engine, "read_only", False) is True for engine in engines)


def test_oem_011_bridge_registers_all_engines():
    runtime = DummyRuntime()
    result = register_migrated_oracle_engines(runtime)

    assert result.bridge_id == BRIDGE_ID
    assert result.status == "pass"
    assert result.total_specs == len(MIGRATED_ENGINE_SPECS)
    assert result.registered_count == len(MIGRATED_ENGINE_SPECS)
    assert result.failed_count == 0
    assert len(runtime.engines) == len(MIGRATED_ENGINE_SPECS)


def test_oem_011_registered_engines_emit_predictions():
    runtime = DummyRuntime()
    register_migrated_oracle_engines(runtime)

    for engine_id, engine in runtime.engines.items():
        predictions = engine.predict(
            {
                "market_id": f"OEM011-{engine_id.upper().replace('.', '-')}",
                "score": 0.42,
                "edge": 0.42,
                "confidence": 0.82,
            }
        )
        assert isinstance(predictions, list)
        assert len(predictions) >= 1


if __name__ == "__main__":
    test_oem_011_bridge_lists_specs()
    test_oem_011_bridge_builds_all_engines()
    test_oem_011_bridge_registers_all_engines()
    test_oem_011_registered_engines_emit_predictions()

    runtime = DummyRuntime()
    result = register_migrated_oracle_engines(runtime)

    print("[PASS] OEM-011 Oracle Engine Migration Registry Bridge")
    print(
        {
            "bridge_id": result.bridge_id,
            "status": result.status,
            "total_specs": result.total_specs,
            "registered_count": result.registered_count,
            "failed_count": result.failed_count,
            "runtime_engines": len(runtime.engines),
        }
    )
