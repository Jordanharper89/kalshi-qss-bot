from qseries_v2.oracle_intelligence.universal_market_adapter_directory_engine import (
    oracle_universal_market_adapter_directory_engine,
)


def routing_table():
    return {
        "adapter_routing_table_id": "route-table-001",
        "routing_status": "adapter_routing_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "routes": [
            {
                "route_id": "route-001",
                "domain": "CRYPTO",
                "adapter_id": "adp.crypto",
                "adapter_role": "crypto_umm_ingestion_adapter",
                "route_status": "route_institutional_ready",
                "route_priority": 1,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            {
                "route_id": "route-002",
                "domain": "STOCKS",
                "adapter_id": "adp.stocks",
                "adapter_role": "stocks_umm_ingestion_adapter",
                "route_status": "route_ready",
                "route_priority": 2,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        ],
    }


def test_directory_builds():
    directory = oracle_universal_market_adapter_directory_engine.build_directory(routing_table())

    assert directory["read_only"] is True
    assert directory["execution_allowed"] is False
    assert directory["execution_owner"] == "Q Series"
    assert directory["directory_status"] == "adapter_directory_active"
    assert directory["entry_count"] == 2
    assert directory["domain_count"] == 2
    assert directory["adapter_count"] == 2
    assert directory["blocked_count"] == 0


def test_institutional_directory():
    table = routing_table()
    table["routes"] = [table["routes"][0]]

    directory = oracle_universal_market_adapter_directory_engine.build_directory(table)

    assert directory["directory_status"] == "adapter_directory_institutional"
    assert directory["institutional_count"] == 1
    assert directory["entries"][0]["directory_status"] == "directory_institutional"


def test_blocked_directory():
    table = routing_table()
    table["routes"][0]["route_status"] = "route_blocked"

    directory = oracle_universal_market_adapter_directory_engine.build_directory(table)

    assert directory["directory_status"] == "adapter_directory_blocked"
    assert directory["blocked_count"] == 1


def test_lookup_adapter():
    directory = oracle_universal_market_adapter_directory_engine.build_directory(routing_table())
    result = oracle_universal_market_adapter_directory_engine.lookup_adapter(directory, "adp.crypto")

    assert result["found"] is True
    assert result["match_count"] == 1
    assert result["entries"][0]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True


def test_lookup_domain():
    directory = oracle_universal_market_adapter_directory_engine.build_directory(routing_table())
    result = oracle_universal_market_adapter_directory_engine.lookup_domain(directory, "crypto")

    assert result["found"] is True
    assert result["domain"] == "CRYPTO"
    assert result["entries"][0]["domain"] == "CRYPTO"


def test_search_directory():
    directory = oracle_universal_market_adapter_directory_engine.build_directory(routing_table())
    result = oracle_universal_market_adapter_directory_engine.search(directory, "crypto institutional")

    assert result["match_count"] == 1
    assert result["entries"][0]["adapter_id"] == "adp.crypto"
    assert result["execution_allowed"] is False


def test_empty_directory():
    directory = oracle_universal_market_adapter_directory_engine.build_directory({
        "adapter_routing_table_id": "empty",
        "routes": [],
    })

    assert directory["directory_status"] == "empty_adapter_directory"
    assert directory["entry_count"] == 0
    assert directory["entries"] == []
    assert directory["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_directory_builds()
    test_institutional_directory()
    test_blocked_directory()
    test_lookup_adapter()
    test_lookup_domain()
    test_search_directory()
    test_empty_directory()
    print("[PASS] OI-175 Oracle Universal Market Adapter Directory Engine")
