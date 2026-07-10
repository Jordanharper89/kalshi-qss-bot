from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityDirection,
    OpportunityEvidenceRef,
    OpportunityType,
    RiskLevel,
    UOM_VERSION,
    UniversalOpportunityFactory,
)


def _prediction_market():
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id="KXBTC-YES",
        title="Will BTC close above 100k?",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def test_uom_001_prediction_market_scalp():
    market = _prediction_market()

    opportunity = UniversalOpportunityFactory.prediction_market_scalp(
        market=market,
        fair_value=0.67,
        market_price=0.55,
        confidence=0.84,
        explanation="Oracle fair value is meaningfully above market ask.",
        liquidity_score=0.76,
        risk_score=0.31,
    )

    assert opportunity.read_only is True
    assert opportunity.schema_version == UOM_VERSION
    assert opportunity.market_id == market.market_id
    assert opportunity.opportunity_type == OpportunityType.PREDICTION_MARKET_SCALP
    assert opportunity.direction == OpportunityDirection.YES
    assert round(opportunity.expected_edge, 2) == 0.12
    assert opportunity.is_actionable_candidate() is True
    assert opportunity.quality_score() > 0


def test_uom_001_settlement_edge():
    market = _prediction_market()

    opportunity = UniversalOpportunityFactory.settlement_edge(
        market=market,
        payout_certainty=0.99,
        market_price=0.94,
        confidence=0.97,
        explanation="Outcome appears effectively settled while market still trades below payout.",
    )

    assert opportunity.opportunity_type == OpportunityType.PREDICTION_MARKET_SETTLEMENT
    assert opportunity.opportunity_type.value == "prediction_market_settlement"
    assert opportunity.direction == OpportunityDirection.YES
    assert round(opportunity.expected_edge, 2) == 0.05
    assert opportunity.risk_level == RiskLevel.LOW
    assert "settlement" in opportunity.tags


def test_uom_001_crypto_spot_edge():
    market = UniversalMarketFactory.from_crypto_spot(
        venue_id="coinbase",
        venue_name="Coinbase",
        symbol="BTC-USD",
        base_asset="BTC",
        quote_asset="USD",
        last=100000,
    )

    opportunity = UniversalOpportunityFactory.crypto_spot_edge(
        market=market,
        expected_move=0.035,
        confidence=0.73,
        explanation="Momentum and liquidity support short-term upside.",
    )

    assert opportunity.opportunity_type == OpportunityType.CRYPTO_SPOT_EDGE
    assert opportunity.direction == OpportunityDirection.BUY
    assert opportunity.execution.required_execution_adapter == "crypto_spot"
    assert "crypto" in opportunity.tags


def test_uom_001_solana_token_snipe():
    market = UniversalMarketFactory.from_solana_token_launch(
        token_mint="Mint111",
        token_symbol="MEME",
        liquidity=1200,
        mint_authority_disabled=True,
        lp_burned=True,
    )

    opportunity = UniversalOpportunityFactory.solana_token_snipe(
        market=market,
        expected_multiple=2.5,
        confidence=0.62,
        explanation="Launch profile resembles prior successful token launches.",
    )

    assert opportunity.opportunity_type == OpportunityType.SOLANA_TOKEN_SNIPE
    assert opportunity.direction == OpportunityDirection.BUY
    assert opportunity.expected_edge == 1.5
    assert opportunity.risk_level == RiskLevel.EXTREME
    assert "rug_risk" in opportunity.risk_flags


def test_uom_001_arbitrage_spread():
    market = UniversalMarketFactory.from_arbitrage_pair(
        market_id="arb:btc:a:b",
        title="BTC cross-venue spread",
        venue_a="VenueA",
        venue_b="VenueB",
        asset="BTC",
        spread=0.012,
        liquidity=50000,
    )

    opportunity = UniversalOpportunityFactory.arbitrage_spread(
        market=market,
        spread=0.012,
        confidence=0.91,
        explanation="Cross-venue price spread exceeds execution cost estimate.",
    )

    assert opportunity.opportunity_type == OpportunityType.ARBITRAGE_SPREAD
    assert opportunity.execution.required_execution_adapter == "arbitrage_router"
    assert opportunity.risk_level == RiskLevel.LOW


def test_uom_001_wallet_follow_signal():
    market = UniversalMarketFactory.from_wallet_signal(
        wallet_address="Wallet111",
        chain="Solana",
        asset="SOL",
        win_rate=0.71,
    )

    opportunity = UniversalOpportunityFactory.wallet_follow_signal(
        market=market,
        trader_edge=0.19,
        confidence=0.69,
        explanation="Wallet has strong recent realized performance.",
    )

    assert opportunity.opportunity_type == OpportunityType.WALLET_FOLLOW_SIGNAL
    assert opportunity.direction == OpportunityDirection.FOLLOW
    assert opportunity.execution.required_execution_adapter == "wallet_copy"
    assert "copy_intelligence" in opportunity.tags


def test_uom_001_serializable_fingerprint_evidence_and_immutability():
    market = _prediction_market()
    evidence = OpportunityEvidenceRef(
        evidence_id="ev_001",
        source="oracle.test",
        evidence_type="fair_value_gap",
        weight=0.8,
        summary="Fair value exceeds ask.",
    )

    opportunity = UniversalOpportunityFactory.prediction_market_scalp(
        market=market,
        fair_value=0.67,
        market_price=0.55,
        confidence=0.84,
        explanation="Oracle fair value is above market ask.",
        evidence_refs=[evidence],
        supporting_prediction_ids=["pred_001"],
    )

    data = opportunity.to_dict()

    assert data["schema_version"] == UOM_VERSION
    assert data["read_only"] is True
    assert data["opportunity_type"] == "prediction_market_scalp"
    assert data["evidence_refs"][0]["evidence_id"] == "ev_001"
    assert "kalshi" in opportunity.fingerprint()
    assert "KXBTC-YES" in opportunity.fingerprint()

    try:
        opportunity.confidence = 0.1
        raise AssertionError("UniversalOpportunity should be immutable.")
    except FrozenInstanceError:
        pass


if __name__ == "__main__":
    test_uom_001_prediction_market_scalp()
    test_uom_001_settlement_edge()
    test_uom_001_crypto_spot_edge()
    test_uom_001_solana_token_snipe()
    test_uom_001_arbitrage_spread()
    test_uom_001_wallet_follow_signal()
    test_uom_001_serializable_fingerprint_evidence_and_immutability()

    print("[PASS] UOM-001.1 Universal Opportunity Contract")
    print(
        {
            "schema_version": UOM_VERSION,
            "opportunity_types": [
                "prediction_market_scalp",
                "prediction_market_settlement",
                "crypto_spot_edge",
                "solana_token_snipe",
                "arbitrage_spread",
                "wallet_follow_signal",
            ],
            "read_only": True,
        }
    )
