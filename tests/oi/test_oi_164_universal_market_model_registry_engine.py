from qseries_v2.oracle_intelligence.universal_market_model_registry_engine import (
    oracle_universal_market_model_registry_engine,
)


def test_default_registry_builds_ready():
    registry = oracle_universal_market_model_registry_engine.build_registry()

    assert registry["read_only"] is True
    assert registry["execution_allowed"] is False
    assert registry["execution_owner"] == "Q Series"
    assert registry["single_oracle_instance"] is True
    assert registry["adapter_based_expansion"] is True
    assert registry["registry_status"] == "umm_registry_ready"
    assert registry["domain_count"] == 11
    assert registry["violation_count"] == 0


def test_custom_domain_registers():
    registry = oracle_universal_market_model_registry_engine.build_registry([
        {
            "domain": "CRYPTO",
            "adapter_type": "crypto_adapter",
            "data_model": "UniversalCryptoMarketRecord",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
        }
    ])

    assert registry["domain_count"] == 1
    assert registry["records"][0]["domain"] == "CRYPTO"
    assert registry["records"][0]["readiness_status"] == "umm_domain_ready"


def test_execution_violation_blocks_registry():
    registry = oracle_universal_market_model_registry_engine.build_registry([
        {
            "domain": "STOCKS",
            "execution_allowed": True,
            "read_only": True,
            "execution_owner": "Q Series",
        }
    ])

    assert registry["registry_status"] == "umm_registry_blocked"
    assert registry["violation_count"] == 1
    assert registry["records"][0]["readiness_status"] == "blocked_execution_violation"


def test_lookup_domain_found():
    registry = oracle_universal_market_model_registry_engine.build_registry()
    result = oracle_universal_market_model_registry_engine.lookup_domain(registry, "crypto")

    assert result["found"] is True
    assert result["domain"] == "CRYPTO"
    assert result["record"]["domain"] == "CRYPTO"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def test_lookup_domain_missing():
    registry = oracle_universal_market_model_registry_engine.build_registry()
    result = oracle_universal_market_model_registry_engine.lookup_domain(registry, "UNKNOWN_DOMAIN")

    assert result["found"] is False
    assert result["record"] is None
    assert result["execution_owner"] == "Q Series"


if __name__ == "__main__":
    test_default_registry_builds_ready()
    test_custom_domain_registers()
    test_execution_violation_blocks_registry()
    test_lookup_domain_found()
    test_lookup_domain_missing()
    print("[PASS] OI-164 Oracle Universal Market Model Registry Engine")
