from qseries_v2.oracle_intelligence.universal_market_model import (
    MarketStatus,
    MarketType,
    SettlementType,
    UniversalMarketFactory,
)


def test_umm_001_prediction_market_normalization():
    market = UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id="KXBTC-YES",
        title="Will BTC close above 100k?",
        bid=0.54,
        ask=0.58,
        liquidity=25000,
        closes_at="2026-12-31T23:59:00+00:00",
    )

    assert market.read_only is True
    assert market.market_type == MarketType.PREDICTION_MARKET
    assert market.status == MarketStatus.ACTIVE
    assert market.settlement_type == SettlementType.BINARY
    assert market.price.mid == 0.56
    assert round(market.price.spread, 2) == 0.04
    assert market.is_tradeable_observation() is True
    assert market.has_price_context() is True


def test_umm_001_crypto_spot_normalization():
    market = UniversalMarketFactory.from_crypto_spot(
        venue_id="coinbase",
        venue_name="Coinbase",
        symbol="BTC-USD",
        base_asset="BTC",
        quote_asset="USD",
        last=100000,
        bid=99990,
        ask=100010,
        volume_24h=2500000000,
    )

    assert market.market_id == "coinbase:btc-usd"
    assert market.market_type == MarketType.CRYPTO_SPOT
    assert market.base_asset == "BTC"
    assert market.quote_asset == "USD"
    assert market.price.mid == 100000
    assert round(market.price.spread, 2) == 20


def test_umm_001_solana_token_launch_normalization():
    market = UniversalMarketFactory.from_solana_token_launch(
        token_mint="Mint111",
        token_symbol="MEME",
        token_name="Meme Token",
        liquidity=1200,
        launch_time="2026-07-07T20:00:00+00:00",
        mint_authority_disabled=True,
        lp_burned=True,
    )

    assert market.market_type == MarketType.SOLANA_TOKEN_LAUNCH
    assert market.status == MarketStatus.UPCOMING
    assert market.base_asset == "MEME"
    assert market.quote_asset == "SOL"
    assert "token_launch" in market.tags
    assert market.metadata["mint_authority_disabled"] is True
    assert market.metadata["lp_burned"] is True


def test_umm_001_arbitrage_pair_normalization():
    market = UniversalMarketFactory.from_arbitrage_pair(
        market_id="arb:btc:venue-a:venue-b",
        title="BTC venue spread",
        venue_a="VenueA",
        venue_b="VenueB",
        asset="BTC",
        spread=0.012,
        liquidity=50000,
    )

    assert market.market_type == MarketType.ARBITRAGE_PAIR
    assert market.settlement_type == SettlementType.CASH_SETTLED
    assert market.price.spread == 0.012
    assert "arbitrage" in market.tags


def test_umm_001_wallet_signal_normalization():
    market = UniversalMarketFactory.from_wallet_signal(
        wallet_address="Wallet111",
        chain="Solana",
        asset="SOL",
        signal_title="Profitable wallet accumulation",
        win_rate=0.71,
    )

    assert market.market_type == MarketType.WALLET_SIGNAL
    assert market.venue.venue_type == "blockchain_wallet"
    assert market.base_asset == "SOL"
    assert market.metadata["win_rate"] == 0.71


def test_umm_001_to_dict_and_fingerprint():
    market = UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id="KXTEST",
        title="Test Market",
        bid=0.40,
        ask=0.44,
    )

    data = market.to_dict()

    assert data["market_type"] == "prediction_market"
    assert data["status"] == "active"
    assert data["settlement_type"] == "binary"
    assert data["read_only"] is True
    assert "kalshi" in market.fingerprint()


if __name__ == "__main__":
    test_umm_001_prediction_market_normalization()
    test_umm_001_crypto_spot_normalization()
    test_umm_001_solana_token_launch_normalization()
    test_umm_001_arbitrage_pair_normalization()
    test_umm_001_wallet_signal_normalization()
    test_umm_001_to_dict_and_fingerprint()

    print("[PASS] UMM-001 Universal Market Model")
    print(
        {
            "models": [
                "UniversalMarket",
                "VenueRef",
                "MarketPriceSnapshot",
                "MarketTimeWindow",
            ],
            "market_types": [
                "prediction_market",
                "crypto_spot",
                "solana_token_launch",
                "arbitrage_pair",
                "wallet_signal",
            ],
            "read_only": True,
        }
    )
