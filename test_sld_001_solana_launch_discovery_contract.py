from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryRequest,
    EmptySolanaLaunchDiscoveryEngine,
)


def test_sld_001_solana_launch_discovery_contract():
    request = SolanaLaunchDiscoveryRequest(
        request_id="solana.launch.discovery.test.request",
        family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
        source_name="test_source",
        mints=("mint_a", "mint_b"),
        pools=("pool_a",),
        metadata={"records": [{"mint": "mint_a", "pool": "pool_a"}]},
    )

    engine = EmptySolanaLaunchDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "SLD-001"
    assert CONTRACT_ID == "oracle.discovery.contract.solana_launch"

    assert request.read_only is True
    assert request.mints == ("mint_a", "mint_b")
    assert request.pools == ("pool_a",)
    assert request.family == SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["signing_allowed"] is False
    assert caps.metadata["fund_movement_allowed"] is False
    assert caps.metadata["swap_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "SLD-001"
    assert result.engine_id == "oracle.discovery.solana_launch.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.launches_seen == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "SLD-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] SLD-001 Solana Launch Discovery Contract")
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
    test_sld_001_solana_launch_discovery_contract()
