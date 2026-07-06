from qseries_v2.oracle_intelligence.universal_market_adapter_contract_engine import (
    oracle_universal_market_adapter_contract_engine,
)


def good_adapter():
    return {
        "adapter_id": "adp.crypto",
        "adapter_name": "Crypto Adapter",
        "domain": "CRYPTO",
        "adapter_type": "crypto_adapter",
        "schema_version": "universal_market_model_schema_v1",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "provided_capabilities": [
            "normalize_to_umm",
            "preserve_lineage",
            "provide_timestamp",
            "provide_source",
            "provide_confidence",
            "read_only_ingestion",
            "replayable_output",
            "explainable_output",
            "telemetry_enabled",
        ],
    }


def test_ready_contract_registry():
    registry = oracle_universal_market_adapter_contract_engine.build_contract_registry([good_adapter()])

    assert registry["read_only"] is True
    assert registry["execution_allowed"] is False
    assert registry["execution_owner"] == "Q Series"
    assert registry["registry_status"] == "adapter_contract_registry_ready"
    assert registry["contract_count"] == 1
    assert registry["ready_count"] == 1
    assert registry["issue_count"] == 0


def test_missing_capability_warns():
    adapter = good_adapter()
    adapter["provided_capabilities"] = adapter["provided_capabilities"][:-1]

    registry = oracle_universal_market_adapter_contract_engine.build_contract_registry([adapter])

    assert registry["registry_status"] == "adapter_contract_registry_ready_with_warnings"
    assert registry["warning_count"] == 1
    assert any(issue["code"] == "missing_capability" for issue in registry["issues"])


def test_execution_violation_blocks():
    adapter = good_adapter()
    adapter["execution_allowed"] = True

    registry = oracle_universal_market_adapter_contract_engine.build_contract_registry([adapter])

    assert registry["registry_status"] == "adapter_contract_registry_blocked"
    assert registry["critical_count"] >= 1
    assert registry["contracts"][0]["contract_status"] == "blocked_execution_violation"


def test_unsupported_domain_warns():
    adapter = good_adapter()
    adapter["domain"] = "UNKNOWN_DOMAIN"

    registry = oracle_universal_market_adapter_contract_engine.build_contract_registry([adapter])

    assert registry["registry_status"] == "adapter_contract_registry_ready_with_warnings"
    assert any(issue["code"] == "unsupported_domain" for issue in registry["issues"])


def test_empty_registry():
    registry = oracle_universal_market_adapter_contract_engine.build_contract_registry([])

    assert registry["registry_status"] == "empty_adapter_contract_registry"
    assert registry["contract_count"] == 0
    assert registry["contracts"] == []
    assert registry["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_ready_contract_registry()
    test_missing_capability_warns()
    test_execution_violation_blocks()
    test_unsupported_domain_warns()
    test_empty_registry()
    print("[PASS] OI-166 Oracle Universal Market Adapter Contract Engine")
