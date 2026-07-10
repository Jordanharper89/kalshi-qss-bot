from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    CryptoDiscoveryFamily,
    CryptoDiscoveryRequest,
    EmptyCryptoDiscoveryEngine,
)


def test_cdm_001_crypto_discovery_contract():
    request = CryptoDiscoveryRequest(
        request_id="crypto.discovery.test.request",
        family=CryptoDiscoveryFamily.CRYPTO_SPOT,
        source_name="test_source",
        symbols=("btc-usd", "eth-usd"),
        metadata={"records": [{"symbol": "BTC-USD"}]},
    )

    engine = EmptyCryptoDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "CDM-001"
    assert CONTRACT_ID == "oracle.discovery.contract.crypto"

    assert request.read_only is True
    assert request.symbols == ("BTC-USD", "ETH-USD")
    assert request.family == CryptoDiscoveryFamily.CRYPTO_SPOT

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "CDM-001"
    assert result.engine_id == "oracle.discovery.crypto.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "CDM-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] CDM-001 Crypto Discovery Contract")
    print(
        {
            "schema_version": d["schema_version"],
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_cdm_001_crypto_discovery_contract()
