from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.oracle_discovery_model import (
    ODM_VERSION,
    DiscoveryMode,
    DiscoveryStatus,
    DiscoveryCapability,
    DiscoveryTelemetry,
    OracleDiscoveryEngineContract,
    TestDiscoveryEngine,
    make_discovery_request,
)


def test_odm_001_request_serialization():
    request = make_discovery_request(
        request_id="req_001",
        market_types=["prediction_market"],
        venues=["kalshi"],
        mode=DiscoveryMode.TEST,
        limit=10,
        filters={"min_liquidity": 1000},
    )

    data = request.to_dict()

    assert data["request_id"] == "req_001"
    assert data["mode"] == "test"
    assert data["market_types"] == ["prediction_market"]
    assert data["venues"] == ["kalshi"]
    assert data["limit"] == 10
    assert data["read_only"] is True
    assert data["schema_version"] == ODM_VERSION


def test_odm_001_capability_serialization():
    capability = DiscoveryCapability(
        name="prediction_market_discovery",
        description="Finds prediction market opportunities.",
        supported_market_types=["prediction_market"],
        supported_modes=["snapshot"],
    )

    data = capability.to_dict()

    assert data["name"] == "prediction_market_discovery"
    assert data["produces_opportunities"] is True
    assert data["read_only"] is True
    assert data["schema_version"] == ODM_VERSION


def test_odm_001_test_engine_contract_shape():
    engine = TestDiscoveryEngine()

    assert isinstance(engine, OracleDiscoveryEngineContract)
    assert engine.read_only is True
    assert engine.schema_version == ODM_VERSION
    assert engine.engine_id() == "oracle.discovery.test"
    assert engine.engine_name() == "Test Discovery Engine"
    assert engine.engine_version() == ODM_VERSION
    assert "prediction_market" in engine.supported_market_types()


def test_odm_001_health_check():
    engine = TestDiscoveryEngine()
    health = engine.health_check()

    assert health.engine_id == engine.engine_id()
    assert health.status == DiscoveryStatus.OK
    assert health.ready is True
    assert health.read_only is True

    data = health.to_dict()
    assert data["status"] == "ok"
    assert data["schema_version"] == ODM_VERSION


def test_odm_001_discover_empty_result():
    engine = TestDiscoveryEngine()
    request = make_discovery_request(
        request_id="req_002",
        mode=DiscoveryMode.TEST,
    )

    result = engine.discover(request)
    data = result.to_dict()

    assert result.engine_id == engine.engine_id()
    assert result.status == DiscoveryStatus.EMPTY
    assert result.request.request_id == "req_002"
    assert result.opportunities == []
    assert result.read_only is True
    assert result.telemetry.opportunities_discovered == 0
    assert data["status"] == "empty"
    assert data["read_only"] is True


def test_odm_001_validate_result():
    engine = TestDiscoveryEngine()
    request = make_discovery_request("req_003", mode=DiscoveryMode.TEST)
    result = engine.discover(request)

    assert engine.validate_result(result) is True


def test_odm_001_telemetry_default():
    engine = TestDiscoveryEngine()
    telemetry = engine.telemetry()

    assert isinstance(telemetry, DiscoveryTelemetry)
    assert telemetry.engine_id == engine.engine_id()
    assert telemetry.opportunities_discovered == 0
    assert telemetry.read_only is True
    assert telemetry.schema_version == ODM_VERSION


def test_odm_001_immutability():
    request = make_discovery_request("req_004")

    try:
        request.request_id = "changed"
        raise AssertionError("DiscoveryRequest should be immutable.")
    except FrozenInstanceError:
        pass


if __name__ == "__main__":
    test_odm_001_request_serialization()
    test_odm_001_capability_serialization()
    test_odm_001_test_engine_contract_shape()
    test_odm_001_health_check()
    test_odm_001_discover_empty_result()
    test_odm_001_validate_result()
    test_odm_001_telemetry_default()
    test_odm_001_immutability()

    engine = TestDiscoveryEngine()
    result = engine.discover(make_discovery_request("req_final", mode=DiscoveryMode.TEST))

    print("[PASS] ODM-001 Oracle Discovery Contract")
    print(
        {
            "schema_version": ODM_VERSION,
            "engine_id": engine.engine_id(),
            "status": result.status.value,
            "opportunities": len(result.opportunities),
            "read_only": result.read_only,
        }
    )
