from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    WalletIntelligenceFamily,
    WalletIntelligenceDiscoveryRequest,
    EmptyWalletIntelligenceDiscoveryEngine,
)


def test_wdm_001_wallet_intelligence_discovery_contract():
    request = WalletIntelligenceDiscoveryRequest(
        request_id="wallet.discovery.test.request",
        family=WalletIntelligenceFamily.SMART_MONEY,
        source_name="test_source",
        chains=("Solana", "Ethereum"),
        wallets=("wallet_a", "wallet_b"),
        symbols=("sol-usd", "eth-usd"),
        metadata={"records": [{"wallet": "wallet_a", "chain": "solana"}]},
    )

    engine = EmptyWalletIntelligenceDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "WDM-001"
    assert CONTRACT_ID == "oracle.discovery.contract.wallet_intelligence"

    assert request.read_only is True
    assert request.chains == ("solana", "ethereum")
    assert request.wallets == ("wallet_a", "wallet_b")
    assert request.symbols == ("SOL-USD", "ETH-USD")
    assert request.family == WalletIntelligenceFamily.SMART_MONEY

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["signing_allowed"] is False
    assert caps.metadata["fund_movement_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "WDM-001"
    assert result.engine_id == "oracle.discovery.wallet_intelligence.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.wallets_seen == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "WDM-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] WDM-001 Wallet Intelligence Discovery Contract")
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
    test_wdm_001_wallet_intelligence_discovery_contract()
