from qseries_v2.oracle_intelligence.architecture_registry_engine import (
    oracle_architecture_registry_engine,
)


def sample_modules():
    return [
        {
            "module_id": "OI-155",
            "module_name": "Oracle Historical Replay Engine",
            "architecture_layer": "Historical Intelligence",
            "lifecycle_phase": "production",
            "ownership": "Oracle Intelligence",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "universal_market_model_ready": True,
            "adapter_ready": False,
            "replayable": True,
            "explainable": True,
            "dependencies": ["OI-154"],
            "tags": ["historical", "replay"],
        },
        {
            "module_id": "OI-160",
            "module_name": "Oracle Alpha Integration Test Engine",
            "architecture_layer": "Institutional Validation",
            "lifecycle_phase": "production",
            "ownership": "Oracle Intelligence",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "universal_market_model_ready": True,
            "adapter_ready": False,
            "replayable": True,
            "explainable": True,
            "dependencies": ["OI-155", "OI-156", "OI-157", "OI-158", "OI-159"],
            "tags": ["alpha", "integration"],
        },
    ]


def test_registry_builds_successfully():
    registry = oracle_architecture_registry_engine.build_registry(sample_modules())

    assert registry["read_only"] is True
    assert registry["execution_allowed"] is False
    assert registry["execution_owner"] == "Q Series"
    assert registry["registry_status"] == "architecture_registry_ready"
    assert registry["record_count"] == 2
    assert registry["violation_count"] == 0
    assert registry["replayable_count"] == 2
    assert registry["explainable_count"] == 2


def test_registry_blocks_execution_violation():
    modules = sample_modules()
    modules[0]["execution_allowed"] = True

    registry = oracle_architecture_registry_engine.build_registry(modules)

    assert registry["registry_status"] == "architecture_registry_blocked"
    assert registry["violation_count"] == 1
    assert registry["records"][0]["institutional_status"] == "blocked_execution_violation"


def test_lookup_module_found():
    registry = oracle_architecture_registry_engine.build_registry(sample_modules())
    result = oracle_architecture_registry_engine.lookup_module(registry, "OI-160")

    assert result["found"] is True
    assert result["read_only"] is True
    assert result["execution_allowed"] is False
    assert result["record"]["module_id"] == "OI-160"


def test_lookup_module_missing():
    registry = oracle_architecture_registry_engine.build_registry(sample_modules())
    result = oracle_architecture_registry_engine.lookup_module(registry, "OI-999")

    assert result["found"] is False
    assert result["record"] is None
    assert result["execution_owner"] == "Q Series"


def test_empty_registry():
    registry = oracle_architecture_registry_engine.build_registry([])

    assert registry["registry_status"] == "empty_architecture_registry"
    assert registry["record_count"] == 0
    assert registry["records"] == []
    assert registry["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_registry_builds_successfully()
    test_registry_blocks_execution_violation()
    test_lookup_module_found()
    test_lookup_module_missing()
    test_empty_registry()
    print("[PASS] OI-162 Oracle Architecture Registry Engine")
