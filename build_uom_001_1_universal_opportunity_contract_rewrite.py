from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
ORACLE = BASE / "oracle_intelligence"
UOM = ORACLE / "universal_opportunity_model"

MODEL_PATH = UOM / "universal_opportunity.py"
INIT_PATH = UOM / "__init__.py"
ORACLE_INIT_PATH = ORACLE / "__init__.py"
TEST_PATH = ROOT / "test_uom_001_universal_opportunity_contract.py"

MODEL_CODE = r'''"""
UOM-001.1 Universal Opportunity Contract

Clean canonical opportunity representation for Oracle Intelligence V3.

Purpose:
- Normalize any actionable edge into one read-only Opportunity object.
- Support prediction market scalps, settlements, crypto spot, arbitrage,
  Solana token launches, wallet-follow signals, and future opportunity types.
- Provide the future Opportunity Operating System with one stable contract.

Oracle discovers and explains.
Decision Layer filters.
Q Series executes.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


UOM_VERSION = "UOM-001.1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OpportunityType(str, Enum):
    PREDICTION_MARKET_SCALP = "prediction_market_scalp"
    PREDICTION_MARKET_SETTLEMENT = "prediction_market_settlement"
    CRYPTO_SPOT_EDGE = "crypto_spot_edge"
    SOLANA_TOKEN_SNIPE = "solana_token_snipe"
    ARBITRAGE_SPREAD = "arbitrage_spread"
    WALLET_FOLLOW_SIGNAL = "wallet_follow_signal"
    MARKET_MISPRICING = "market_mispricing"
    LIQUIDITY_IMBALANCE = "liquidity_imbalance"
    UNKNOWN = "unknown"


class OpportunityDirection(str, Enum):
    YES = "YES"
    NO = "NO"
    BUY = "BUY"
    SELL = "SELL"
    LONG = "LONG"
    SHORT = "SHORT"
    FOLLOW = "FOLLOW"
    AVOID = "AVOID"
    HOLD = "HOLD"
    UNKNOWN = "UNKNOWN"


class OpportunityStatus(str, Enum):
    NEW = "new"
    VERIFIED = "verified"
    RANKED = "ranked"
    ASSIGNED = "assigned"
    EXECUTED = "executed"
    EXPIRED = "expired"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class OpportunityTimeWindow:
    discovered_at: str = field(default_factory=utc_now)
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    estimated_lifetime_seconds: Optional[int] = None
    urgency_score: float = 0.0
    freshness_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityExecutionProfile:
    required_execution_adapter: Optional[str] = None
    execution_difficulty: float = 0.5
    estimated_slippage: Optional[float] = None
    capital_required: Optional[float] = None
    min_liquidity_required: Optional[float] = None
    max_position_size: Optional[float] = None
    venue_latency_sensitivity: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityEvidenceRef:
    evidence_id: str
    source: str
    evidence_type: str
    weight: float = 1.0
    summary: Optional[str] = None
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UniversalOpportunity:
    opportunity_id: str
    market_id: str
    market_type: str
    venue_id: str
    venue_name: str
    opportunity_type: OpportunityType
    direction: OpportunityDirection
    expected_value: float
    expected_edge: float
    confidence: float
    explanation: str
    status: OpportunityStatus = OpportunityStatus.NEW
    liquidity_score: float = 0.5
    risk_score: float = 0.5
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    time_window: OpportunityTimeWindow = field(default_factory=OpportunityTimeWindow)
    execution: OpportunityExecutionProfile = field(default_factory=OpportunityExecutionProfile)
    evidence_refs: List[OpportunityEvidenceRef] = field(default_factory=list)
    supporting_prediction_ids: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    raw_market: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = UOM_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["opportunity_type"] = self.opportunity_type.value
        data["direction"] = self.direction.value
        data["status"] = self.status.value
        data["risk_level"] = self.risk_level.value
        return data

    def fingerprint(self) -> str:
        return "|".join(
            [
                self.venue_id,
                self.market_type,
                self.market_id,
                self.opportunity_type.value,
                self.direction.value,
                str(round(float(self.expected_edge), 8)),
            ]
        )

    def quality_score(self) -> float:
        confidence = _clamp(self.confidence)
        edge = _clamp(abs(self.expected_edge))
        liquidity = _clamp(self.liquidity_score)
        urgency = _clamp(self.time_window.urgency_score)
        freshness = _clamp(self.time_window.freshness_score)
        risk_penalty = _clamp(self.risk_score)
        execution_penalty = _clamp(self.execution.execution_difficulty)

        score = (
            confidence * 0.30
            + edge * 0.25
            + liquidity * 0.15
            + urgency * 0.10
            + freshness * 0.10
            - risk_penalty * 0.05
            - execution_penalty * 0.05
        )

        return round(max(0.0, min(1.0, score)), 6)

    def is_actionable_candidate(self) -> bool:
        return (
            self.read_only is True
            and self.status in {OpportunityStatus.NEW, OpportunityStatus.VERIFIED, OpportunityStatus.RANKED}
            and self.confidence > 0
            and self.expected_edge != 0
            and self.direction not in {OpportunityDirection.UNKNOWN, OpportunityDirection.HOLD}
        )


class UniversalOpportunityFactory:
    read_only = True

    @staticmethod
    def from_market(
        market: Any,
        opportunity_type: OpportunityType,
        direction: OpportunityDirection,
        expected_value: float,
        expected_edge: float,
        confidence: float,
        explanation: str,
        status: OpportunityStatus = OpportunityStatus.NEW,
        liquidity_score: float = 0.5,
        risk_score: float = 0.5,
        risk_level: RiskLevel = RiskLevel.UNKNOWN,
        time_window: Optional[OpportunityTimeWindow] = None,
        execution: Optional[OpportunityExecutionProfile] = None,
        evidence_refs: Optional[List[OpportunityEvidenceRef]] = None,
        supporting_prediction_ids: Optional[List[str]] = None,
        risk_flags: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        **metadata: Any,
    ) -> UniversalOpportunity:
        market_dict = _market_to_dict(market)
        venue = getattr(market, "venue", None)

        market_type = _enum_value(getattr(market, "market_type", market_dict.get("market_type", "unknown")))
        market_id = str(getattr(market, "market_id", market_dict.get("market_id", "unknown_market")))

        venue_dict = market_dict.get("venue", {})
        if not isinstance(venue_dict, dict):
            venue_dict = {}

        venue_id = str(
            getattr(venue, "venue_id", None)
            or venue_dict.get("venue_id")
            or "unknown_venue"
        )

        venue_name = str(
            getattr(venue, "venue_name", None)
            or venue_dict.get("venue_name")
            or venue_id
        )

        return UniversalOpportunity(
            opportunity_id=make_opportunity_id("opp"),
            market_id=market_id,
            market_type=market_type,
            venue_id=venue_id,
            venue_name=venue_name,
            opportunity_type=opportunity_type,
            direction=direction,
            expected_value=float(expected_value),
            expected_edge=float(expected_edge),
            confidence=_clamp(confidence),
            explanation=explanation,
            status=status,
            liquidity_score=_clamp(liquidity_score),
            risk_score=_clamp(risk_score),
            risk_level=risk_level,
            time_window=time_window or OpportunityTimeWindow(),
            execution=execution or OpportunityExecutionProfile(),
            evidence_refs=evidence_refs or [],
            supporting_prediction_ids=supporting_prediction_ids or [],
            risk_flags=risk_flags or [],
            tags=tags or [],
            raw_market=market_dict,
            metadata=metadata,
        )

    @staticmethod
    def prediction_market_scalp(
        market: Any,
        fair_value: float,
        market_price: float,
        confidence: float,
        direction: OpportunityDirection = OpportunityDirection.YES,
        explanation: str = "Prediction market scalp opportunity.",
        **metadata: Any,
    ) -> UniversalOpportunity:
        edge = round(float(fair_value) - float(market_price), 12)

        return UniversalOpportunityFactory.from_market(
            market=market,
            opportunity_type=OpportunityType.PREDICTION_MARKET_SCALP,
            direction=direction,
            expected_value=float(fair_value),
            expected_edge=edge,
            confidence=confidence,
            explanation=explanation,
            liquidity_score=metadata.pop("liquidity_score", 0.5),
            risk_score=metadata.pop("risk_score", 0.5),
            risk_level=metadata.pop("risk_level", RiskLevel.MEDIUM),
            execution=metadata.pop(
                "execution",
                OpportunityExecutionProfile(required_execution_adapter="prediction_market"),
            ),
            tags=["prediction_market", "scalp"],
            **metadata,
        )

    @staticmethod
    def settlement_edge(
        market: Any,
        payout_certainty: float,
        market_price: float,
        confidence: float,
        explanation: str = "Settlement edge opportunity.",
        **metadata: Any,
    ) -> UniversalOpportunity:
        edge = round(float(payout_certainty) - float(market_price), 12)

        return UniversalOpportunityFactory.from_market(
            market=market,
            opportunity_type=OpportunityType.PREDICTION_MARKET_SETTLEMENT,
            direction=OpportunityDirection.YES if edge >= 0 else OpportunityDirection.NO,
            expected_value=float(payout_certainty),
            expected_edge=edge,
            confidence=confidence,
            explanation=explanation,
            liquidity_score=metadata.pop("liquidity_score", 0.5),
            risk_score=metadata.pop("risk_score", 0.2),
            risk_level=metadata.pop("risk_level", RiskLevel.LOW),
            execution=metadata.pop(
                "execution",
                OpportunityExecutionProfile(required_execution_adapter="prediction_market_settlement"),
            ),
            tags=["prediction_market", "settlement"],
            **metadata,
        )

    @staticmethod
    def crypto_spot_edge(
        market: Any,
        expected_move: float,
        confidence: float,
        direction: OpportunityDirection = OpportunityDirection.BUY,
        explanation: str = "Crypto spot opportunity.",
        **metadata: Any,
    ) -> UniversalOpportunity:
        return UniversalOpportunityFactory.from_market(
            market=market,
            opportunity_type=OpportunityType.CRYPTO_SPOT_EDGE,
            direction=direction,
            expected_value=float(expected_move),
            expected_edge=float(expected_move),
            confidence=confidence,
            explanation=explanation,
            liquidity_score=metadata.pop("liquidity_score", 0.5),
            risk_score=metadata.pop("risk_score", 0.6),
            risk_level=metadata.pop("risk_level", RiskLevel.HIGH),
            execution=metadata.pop(
                "execution",
                OpportunityExecutionProfile(required_execution_adapter="crypto_spot"),
            ),
            tags=["crypto", "spot"],
            **metadata,
        )

    @staticmethod
    def solana_token_snipe(
        market: Any,
        expected_multiple: float,
        confidence: float,
        explanation: str = "Solana token launch snipe candidate.",
        **metadata: Any,
    ) -> UniversalOpportunity:
        return UniversalOpportunityFactory.from_market(
            market=market,
            opportunity_type=OpportunityType.SOLANA_TOKEN_SNIPE,
            direction=OpportunityDirection.BUY,
            expected_value=float(expected_multiple),
            expected_edge=round(max(0.0, float(expected_multiple) - 1.0), 12),
            confidence=confidence,
            explanation=explanation,
            liquidity_score=metadata.pop("liquidity_score", 0.25),
            risk_score=metadata.pop("risk_score", 0.9),
            risk_level=metadata.pop("risk_level", RiskLevel.EXTREME),
            execution=metadata.pop(
                "execution",
                OpportunityExecutionProfile(required_execution_adapter="solana_wallet"),
            ),
            risk_flags=metadata.pop("risk_flags", ["high_volatility", "rug_risk"]),
            tags=["solana", "token_snipe"],
            **metadata,
        )

    @staticmethod
    def arbitrage_spread(
        market: Any,
        spread: float,
        confidence: float,
        explanation: str = "Arbitrage spread opportunity.",
        **metadata: Any,
    ) -> UniversalOpportunity:
        return UniversalOpportunityFactory.from_market(
            market=market,
            opportunity_type=OpportunityType.ARBITRAGE_SPREAD,
            direction=OpportunityDirection.BUY,
            expected_value=float(spread),
            expected_edge=float(spread),
            confidence=confidence,
            explanation=explanation,
            liquidity_score=metadata.pop("liquidity_score", 0.7),
            risk_score=metadata.pop("risk_score", 0.25),
            risk_level=metadata.pop("risk_level", RiskLevel.LOW),
            execution=metadata.pop(
                "execution",
                OpportunityExecutionProfile(required_execution_adapter="arbitrage_router"),
            ),
            tags=["arbitrage"],
            **metadata,
        )

    @staticmethod
    def wallet_follow_signal(
        market: Any,
        trader_edge: float,
        confidence: float,
        explanation: str = "Wallet-follow opportunity.",
        **metadata: Any,
    ) -> UniversalOpportunity:
        return UniversalOpportunityFactory.from_market(
            market=market,
            opportunity_type=OpportunityType.WALLET_FOLLOW_SIGNAL,
            direction=OpportunityDirection.FOLLOW,
            expected_value=float(trader_edge),
            expected_edge=float(trader_edge),
            confidence=confidence,
            explanation=explanation,
            liquidity_score=metadata.pop("liquidity_score", 0.4),
            risk_score=metadata.pop("risk_score", 0.7),
            risk_level=metadata.pop("risk_level", RiskLevel.HIGH),
            execution=metadata.pop(
                "execution",
                OpportunityExecutionProfile(required_execution_adapter="wallet_copy"),
            ),
            tags=["wallet", "copy_intelligence"],
            **metadata,
        )


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _market_to_dict(market: Any) -> Dict[str, Any]:
    if isinstance(market, dict):
        return dict(market)

    to_dict = getattr(market, "to_dict", None)
    if callable(to_dict):
        value = to_dict()
        return value if isinstance(value, dict) else {}

    return {}


def _clamp(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def make_opportunity_id(prefix: str = "opp") -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


__all__ = [
    "UOM_VERSION",
    "OpportunityType",
    "OpportunityDirection",
    "OpportunityStatus",
    "RiskLevel",
    "OpportunityTimeWindow",
    "OpportunityExecutionProfile",
    "OpportunityEvidenceRef",
    "UniversalOpportunity",
    "UniversalOpportunityFactory",
    "make_opportunity_id",
]
'''

INIT_CODE = r'''from .universal_opportunity import (
    UOM_VERSION,
    OpportunityType,
    OpportunityDirection,
    OpportunityStatus,
    RiskLevel,
    OpportunityTimeWindow,
    OpportunityExecutionProfile,
    OpportunityEvidenceRef,
    UniversalOpportunity,
    UniversalOpportunityFactory,
    make_opportunity_id,
)

__all__ = [
    "UOM_VERSION",
    "OpportunityType",
    "OpportunityDirection",
    "OpportunityStatus",
    "RiskLevel",
    "OpportunityTimeWindow",
    "OpportunityExecutionProfile",
    "OpportunityEvidenceRef",
    "UniversalOpportunity",
    "UniversalOpportunityFactory",
    "make_opportunity_id",
]
'''

TEST_CODE = r'''from dataclasses import FrozenInstanceError

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
'''

def ensure_dirs():
    UOM.mkdir(parents=True, exist_ok=True)


def update_oracle_init():
    ORACLE_INIT_PATH.touch(exist_ok=True)
    text = ORACLE_INIT_PATH.read_text(encoding="utf-8")

    line = (
        "from .universal_opportunity_model import "
        "UniversalOpportunity, UniversalOpportunityFactory, OpportunityType, OpportunityDirection"
    )

    if line not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"

    ORACLE_INIT_PATH.write_text(text, encoding="utf-8")


def main():
    print("=" * 40)
    print(" UOM-001.1 INSTALLER")
    print(" Universal Opportunity Contract Clean Rewrite")
    print("=" * 40)

    ensure_dirs()

    MODEL_PATH.write_text(MODEL_CODE, encoding="utf-8")
    print(f"[OK] Rewrote {MODEL_PATH}")

    INIT_PATH.write_text(INIT_CODE, encoding="utf-8")
    print(f"[OK] Rewrote {INIT_PATH}")

    TEST_PATH.write_text(TEST_CODE, encoding="utf-8")
    print(f"[OK] Rewrote {TEST_PATH}")

    update_oracle_init()
    print(f"[OK] Updated {ORACLE_INIT_PATH}")

    print("\n[DONE] UOM-001.1 installed")
    print("\nRun:")
    print("py test_uom_001_universal_opportunity_contract.py")


if __name__ == "__main__":
    main()