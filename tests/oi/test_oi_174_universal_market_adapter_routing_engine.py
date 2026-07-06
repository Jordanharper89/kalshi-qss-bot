from qseries_v2.oracle_intelligence.universal_market_adapter_routing_engine import (
    oracle_universal_market_adapter_routing_engine,
)


def adapter_registry():
    return {
        "adapter_registry_id": "reg-001",
        "registry_status": "adapter_registry_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "registry_record_id": "reg-rec-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "lifecycle_state": "active_institutional_read_only",
                "lifecycle_status": "lifecycle_institutional",
                "registry_status": "registered_institutional_adapter",
                "registered": True,
                "promoted": True,
                "blocked": False,
                "adapter_role": "crypto_umm_ingestion_adapter",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_routing_table_institutional():
    table = oracle_universal_market_adapter_routing_engine.build_routing_table(adapter_registry())

    assert table["read_only"] is True
    assert table["execution_allowed"] is False
    assert table["execution_owner"] == "Q Series"
    assert table["routing_status"] == "adapter_routing_institutional"
    assert table["route_count"] == 1
    assert table["ready_count"] == 1
    assert table["blocked_count"] == 0
    assert table["routes"][0]["route_status"] == "route_institutional_ready"


def test_routing_table_review():
    registry = adapter_registry()
    registry["records"][0]["registry_status"] = "registered_review_adapter"

    table = oracle_universal_market_adapter_routing_engine.build_routing_table(registry)

    assert table["routing_status"] == "adapter_routing_ready"
    assert table["routes"][0]["route_status"] == "route_ready_with_review"
    assert table["routes"][0]["route_priority"] == 3


def test_routing_table_blocked():
    registry = adapter_registry()
    registry["records"][0]["registry_status"] = "registry_blocked_lifecycle"
    registry["records"][0]["blocked"] = True

    table = oracle_universal_market_adapter_routing_engine.build_routing_table(registry)

    assert table["routing_status"] == "adapter_routing_blocked"
    assert table["blocked_count"] == 1
    assert table["routes"][0]["route_status"] == "route_blocked"


def test_route_domain_found():
    table = oracle_universal_market_adapter_routing_engine.build_routing_table(adapter_registry())
    result = oracle_universal_market_adapter_routing_engine.route_domain(table, "crypto")

    assert result["found"] is True
    assert result["domain"] == "CRYPTO"
    assert result["selected_route"]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def test_route_domain_missing():
    table = oracle_universal_market_adapter_routing_engine.build_routing_table(adapter_registry())
    result = oracle_universal_market_adapter_routing_engine.route_domain(table, "FOREX")

    assert result["found"] is False
    assert result["selected_route"] is None
    assert result["candidate_count"] == 0
    assert result["execution_owner"] == "Q Series"


def test_empty_routing_table():
    table = oracle_universal_market_adapter_routing_engine.build_routing_table({
        "adapter_registry_id": "empty",
        "records": [],
    })

    assert table["routing_status"] == "empty_adapter_routing_table"
    assert table["route_count"] == 0
    assert table["routes"] == []
    assert table["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_routing_table_institutional()
    test_routing_table_review()
    test_routing_table_blocked()
    test_route_domain_found()
    test_route_domain_missing()
    test_empty_routing_table()
    print("[PASS] OI-174 Oracle Universal Market Adapter Routing Engine")
