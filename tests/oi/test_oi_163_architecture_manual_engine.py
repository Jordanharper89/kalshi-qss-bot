from qseries_v2.oracle_intelligence.architecture_manual_engine import (
    oracle_architecture_manual_engine,
)


def sample_registry():
    return {
        "architecture_registry_id": "reg-001",
        "registry_status": "architecture_registry_ready",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "violation_count": 0,
        "supported_domains": ["CRYPTO", "STOCKS", "FOREX"],
        "permanent_principles": [
            "Oracle is strictly read-only.",
            "Q Series is the only execution engine.",
            "Universal Market Model for all data.",
        ],
        "records": [
            {
                "module_id": "OI-155",
                "module_name": "Oracle Historical Replay Engine",
                "architecture_layer": "Historical Intelligence",
                "institutional_status": "institutional_registered",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "replayable": True,
                "explainable": True,
                "universal_market_model_ready": True,
            },
            {
                "module_id": "OI-160",
                "module_name": "Oracle Alpha Integration Test Engine",
                "architecture_layer": "Institutional Validation",
                "institutional_status": "institutional_registered",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "replayable": True,
                "explainable": True,
                "universal_market_model_ready": True,
            },
        ],
    }


def test_manual_generates_successfully():
    manual = oracle_architecture_manual_engine.generate_manual(sample_registry())

    assert manual["read_only"] is True
    assert manual["execution_allowed"] is False
    assert manual["execution_owner"] == "Q Series"
    assert manual["manual_status"] == "architecture_manual_ready"
    assert manual["record_count"] == 2
    assert manual["section_count"] == 5


def test_manual_contains_safety_contract():
    manual = oracle_architecture_manual_engine.generate_manual(sample_registry())
    section = oracle_architecture_manual_engine.get_section(manual, "safety")

    assert section["found"] is True
    assert section["read_only"] is True
    assert section["execution_allowed"] is False
    assert section["section"]["content"]["oracle_executes_trades"] is False
    assert section["section"]["content"]["execution_owner"] == "Q Series"


def test_manual_contains_layer_map():
    manual = oracle_architecture_manual_engine.generate_manual(sample_registry())
    section = oracle_architecture_manual_engine.get_section(manual, "layer_map")

    assert section["found"] is True
    assert section["section"]["content"]["layer_count"] == 2


def test_blocked_registry_blocks_manual():
    registry = sample_registry()
    registry["violation_count"] = 1

    manual = oracle_architecture_manual_engine.generate_manual(registry)

    assert manual["manual_status"] == "architecture_manual_blocked"
    assert manual["violation_count"] == 1


def test_empty_manual():
    registry = sample_registry()
    registry["records"] = []

    manual = oracle_architecture_manual_engine.generate_manual(registry)

    assert manual["manual_status"] == "empty_architecture_manual"
    assert manual["record_count"] == 0
    assert manual["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_manual_generates_successfully()
    test_manual_contains_safety_contract()
    test_manual_contains_layer_map()
    test_blocked_registry_blocks_manual()
    test_empty_manual()
    print("[PASS] OI-163 Oracle Architecture Manual Engine")
