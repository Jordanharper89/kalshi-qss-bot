
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    OrderFlowFamily,
    OrderFlowDiscoveryRequest,
    EmptyOrderFlowDiscoveryEngine,
)


def test_ofd_001_order_flow_discovery_contract():
    request = OrderFlowDiscoveryRequest(
        request_id="order.flow.discovery.test.request",
        family=OrderFlowFamily.ORDER_BOOK_PRESSURE,
        source_name="test_source",
        market_ids=("market_a", "market_b"),
        venues=("Kalshi", "Polymarket"),
        symbols=("btc", "eth"),
        metadata={"records": [{"market_id": "market_a", "bid_depth": 100}]},
    )

    engine = EmptyOrderFlowDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "OFD-001"
    assert CONTRACT_ID == "oracle.discovery.contract.order_flow"

    assert request.read_only is True
    assert request.market_ids == ("market_a", "market_b")
    assert request.venues == ("kalshi", "polymarket")
    assert request.symbols == ("BTC", "ETH")
    assert request.family == OrderFlowFamily.ORDER_BOOK_PRESSURE

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["execution"] is False
    assert caps.metadata["order_allowed"] is False
    assert caps.metadata["position_sizing_allowed"] is False
    assert caps.metadata["broker_connectivity_allowed"] is False
    assert caps.metadata["wallet_signing_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "OFD-001"
    assert result.engine_id == "oracle.discovery.order_flow.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.markets_seen == 0
    assert result.telemetry.opportunities_emitted == 0

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "OFD-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] OFD-001 Order Flow Discovery Contract")
    print({
        "schema_version": d["schema_version"],
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_ofd_001_order_flow_discovery_contract()
