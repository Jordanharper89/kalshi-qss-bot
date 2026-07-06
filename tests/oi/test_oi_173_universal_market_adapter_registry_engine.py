from qseries_v2.oracle_intelligence.universal_market_adapter_registry_engine import (
    oracle_universal_market_adapter_registry_engine,
)


def institutional_lifecycle():
    return {
        "adapter_lifecycle_batch_id": "life-001",
        "lifecycle_status": "adapter_lifecycle_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "lifecycle_record_id": "life-rec-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "certification_status": "adapter_institutionally_certified",
                "certification_score": 100.0,
                "lifecycle_state": "active_institutional_read_only",
                "lifecycle_status": "lifecycle_institutional",
                "promoted": True,
                "blocked": False,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_institutional_registry():
    registry = oracle_universal_market_adapter_registry_engine.build_registry(institutional_lifecycle())

    assert registry["read_only"] is True
    assert registry["execution_allowed"] is False
    assert registry["execution_owner"] == "Q Series"
    assert registry["registry_status"] == "adapter_registry_institutional"
    assert registry["adapter_count"] == 1
    assert registry["registered_count"] == 1
    assert registry["blocked_count"] == 0
    assert registry["records"][0]["registry_status"] == "registered_institutional_adapter"


def test_review_registry():
    lifecycle = institutional_lifecycle()
    lifecycle["records"][0]["lifecycle_state"] = "active_review_read_only"
    lifecycle["records"][0]["lifecycle_status"] = "lifecycle_active_with_review"

    registry = oracle_universal_market_adapter_registry_engine.build_registry(lifecycle)

    assert registry["registry_status"] == "adapter_registry_ready"
    assert registry["records"][0]["registry_status"] == "registered_review_adapter"
    assert registry["registered_count"] == 1


def test_blocked_registry():
    lifecycle = institutional_lifecycle()
    lifecycle["records"][0]["lifecycle_state"] = "blocked"
    lifecycle["records"][0]["lifecycle_status"] = "lifecycle_blocked"
    lifecycle["records"][0]["blocked"] = True
    lifecycle["records"][0]["promoted"] = False

    registry = oracle_universal_market_adapter_registry_engine.build_registry(lifecycle)

    assert registry["registry_status"] == "adapter_registry_blocked"
    assert registry["blocked_count"] == 1
    assert registry["records"][0]["registry_status"] == "registry_blocked_lifecycle"


def test_lookup_adapter():
    registry = oracle_universal_market_adapter_registry_engine.build_registry(institutional_lifecycle())
    result = oracle_universal_market_adapter_registry_engine.lookup_adapter(registry, "adp.crypto")

    assert result["found"] is True
    assert result["record"]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def test_lookup_domain():
    registry = oracle_universal_market_adapter_registry_engine.build_registry(institutional_lifecycle())
    result = oracle_universal_market_adapter_registry_engine.lookup_domain(registry, "crypto")

    assert result["found"] is True
    assert result["domain"] == "CRYPTO"
    assert result["match_count"] == 1
    assert result["records"][0]["domain"] == "CRYPTO"


def test_empty_registry():
    registry = oracle_universal_market_adapter_registry_engine.build_registry({
        "adapter_lifecycle_batch_id": "empty",
        "records": [],
    })

    assert registry["registry_status"] == "empty_adapter_registry"
    assert registry["adapter_count"] == 0
    assert registry["records"] == []
    assert registry["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_institutional_registry()
    test_review_registry()
    test_blocked_registry()
    test_lookup_adapter()
    test_lookup_domain()
    test_empty_registry()
    print("[PASS] OI-173 Oracle Universal Market Adapter Registry Engine")
