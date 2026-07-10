from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
ORACLE = BASE / "oracle_intelligence"
UMM = ORACLE / "universal_market_model"

MODEL_PATH = UMM / "universal_market.py"
INIT_PATH = UMM / "__init__.py"
ORACLE_INIT_PATH = ORACLE / "__init__.py"
TEST_PATH = ROOT / "test_umm_001_universal_market_model.py"

MODEL_CODE = r'''"""
UMM-001 Universal Market Model

Canonical market representation for Oracle Intelligence V3.

Purpose:
- Normalize any tradable or observable market into one internal object.
- Support prediction markets, crypto spot, settlement markets, arbitrage venues,
  Solana token launches, copy-trader signals, and future market types.
- Keep Oracle read-only.
- Provide clean inputs for future Universal Opportunity Model builds.

Oracle remains intelligence-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


UMM_VERSION = "UMM-001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MarketType(str, Enum):
    PREDICTION_MARKET = "prediction_market"
    CRYPTO_SPOT = "crypto_spot"
    CRYPTO_PERP = "crypto_perp"
    SOLANA_TOKEN_LAUNCH = "solana_token_launch"
    SETTLEMENT_MARKET = "settlement_market"
    ARBITRAGE_PAIR = "arbitrage_pair"
    SPORTS_MARKET = "sports_market"
    WALLET_SIGNAL = "wallet_signal"
    MACRO_MARKET = "macro_market"
    UNKNOWN = "unknown"


class MarketStatus(str, Enum):
    ACTIVE = "active"
    UPCOMING = "upcoming"
    PAUSED = "paused"
    CLOSED = "closed"
    SETTLED = "settled"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class SettlementType(str, Enum):
    BINARY = "binary"
    SCALAR = "scalar"
    TOKEN_PRICE = "token_price"
    CASH_SETTLED = "cash_settled"
    PHYSICAL = "physical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class VenueRef:
    venue_id: str
    venue_name: str
    venue_type: str
    raw_symbol: Optional[str] = None
    raw_market_id: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketPriceSnapshot:
    bid: Optional[float] = None
    ask: Optional[float] = None
    mid: Optional[float] = None
    last: Optional[float] = None
    volume_24h: Optional[float] = None
    liquidity: Optional[float] = None
    spread: Optional[float] = None
    currency: str = "USD"
    observed_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketTimeWindow:
    opens_at: Optional[str] = None
    closes_at: Optional[str] = None
    settles_at: Optional[str] = None
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UniversalMarket:
    market_id: str
    market_type: MarketType
    title: str
    venue: VenueRef
    status: MarketStatus = MarketStatus.UNKNOWN
    settlement_type: SettlementType = SettlementType.UNKNOWN
    base_asset: Optional[str] = None
    quote_asset: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[MarketPriceSnapshot] = None
    time_window: Optional[MarketTimeWindow] = None
    tags: List[str] = field(default_factory=list)
    related_market_ids: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = UMM_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["market_type"] = self.market_type.value
        data["status"] = self.status.value
        data["settlement_type"] = self.settlement_type.value
        return data

    def fingerprint(self) -> str:
        return "|".join(
            [
                self.venue.venue_id,
                self.market_type.value,
                str(self.venue.raw_market_id or ""),
                str(self.venue.raw_symbol or ""),
                self.title.strip().lower(),
            ]
        )

    def is_tradeable_observation(self) -> bool:
        return self.status in {MarketStatus.ACTIVE, MarketStatus.UPCOMING}

    def has_price_context(self) -> bool:
        if self.price is None:
            return False
        return any(
            value is not None
            for value in [self.price.bid, self.price.ask, self.price.mid, self.price.last]
        )


class UniversalMarketFactory:
    """
    Factory for building canonical UniversalMarket objects from source payloads.

    This is intentionally read-only and does not fetch external data.
    """

    read_only = True

    @staticmethod
    def from_prediction_market(
        venue_id: str,
        venue_name: str,
        market_id: str,
        title: str,
        status: str = "active",
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        last: Optional[float] = None,
        liquidity: Optional[float] = None,
        closes_at: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
        **metadata: Any,
    ) -> UniversalMarket:
        price = UniversalMarketFactory._price(bid=bid, ask=ask, last=last, liquidity=liquidity)

        return UniversalMarket(
            market_id=market_id,
            market_type=MarketType.PREDICTION_MARKET,
            title=title,
            venue=VenueRef(
                venue_id=venue_id,
                venue_name=venue_name,
                venue_type="prediction_market",
                raw_market_id=market_id,
            ),
            status=UniversalMarketFactory._status(status),
            settlement_type=SettlementType.BINARY,
            price=price,
            time_window=MarketTimeWindow(closes_at=closes_at),
            raw=raw or {},
            metadata=metadata,
        )

    @staticmethod
    def from_crypto_spot(
        venue_id: str,
        venue_name: str,
        symbol: str,
        base_asset: str,
        quote_asset: str = "USD",
        last: Optional[float] = None,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        volume_24h: Optional[float] = None,
        liquidity: Optional[float] = None,
        raw: Optional[Dict[str, Any]] = None,
        **metadata: Any,
    ) -> UniversalMarket:
        market_id = f"{venue_id}:{symbol}".lower()
        price = UniversalMarketFactory._price(
            bid=bid,
            ask=ask,
            last=last,
            volume_24h=volume_24h,
            liquidity=liquidity,
            currency=quote_asset,
        )

        return UniversalMarket(
            market_id=market_id,
            market_type=MarketType.CRYPTO_SPOT,
            title=f"{base_asset}/{quote_asset}",
            venue=VenueRef(
                venue_id=venue_id,
                venue_name=venue_name,
                venue_type="crypto_exchange",
                raw_symbol=symbol,
            ),
            status=MarketStatus.ACTIVE,
            settlement_type=SettlementType.TOKEN_PRICE,
            base_asset=base_asset,
            quote_asset=quote_asset,
            price=price,
            raw=raw or {},
            metadata=metadata,
        )

    @staticmethod
    def from_solana_token_launch(
        token_mint: str,
        token_symbol: Optional[str] = None,
        token_name: Optional[str] = None,
        liquidity: Optional[float] = None,
        launch_time: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
        **metadata: Any,
    ) -> UniversalMarket:
        title = token_name or token_symbol or token_mint

        return UniversalMarket(
            market_id=f"solana:token:{token_mint}",
            market_type=MarketType.SOLANA_TOKEN_LAUNCH,
            title=title,
            venue=VenueRef(
                venue_id="solana",
                venue_name="Solana",
                venue_type="blockchain",
                raw_market_id=token_mint,
                raw_symbol=token_symbol,
            ),
            status=MarketStatus.UPCOMING if launch_time else MarketStatus.ACTIVE,
            settlement_type=SettlementType.TOKEN_PRICE,
            base_asset=token_symbol or token_mint,
            quote_asset="SOL",
            price=UniversalMarketFactory._price(liquidity=liquidity, currency="SOL"),
            time_window=MarketTimeWindow(opens_at=launch_time),
            tags=["solana", "token_launch"],
            raw=raw or {},
            metadata=metadata,
        )

    @staticmethod
    def from_arbitrage_pair(
        market_id: str,
        title: str,
        venue_a: str,
        venue_b: str,
        asset: str,
        spread: Optional[float] = None,
        liquidity: Optional[float] = None,
        raw: Optional[Dict[str, Any]] = None,
        **metadata: Any,
    ) -> UniversalMarket:
        return UniversalMarket(
            market_id=market_id,
            market_type=MarketType.ARBITRAGE_PAIR,
            title=title,
            venue=VenueRef(
                venue_id=f"{venue_a}:{venue_b}".lower(),
                venue_name=f"{venue_a} / {venue_b}",
                venue_type="arbitrage_pair",
                raw_symbol=asset,
            ),
            status=MarketStatus.ACTIVE,
            settlement_type=SettlementType.CASH_SETTLED,
            base_asset=asset,
            price=UniversalMarketFactory._price(spread=spread, liquidity=liquidity),
            tags=["arbitrage"],
            raw=raw or {},
            metadata=metadata,
        )

    @staticmethod
    def from_wallet_signal(
        wallet_address: str,
        chain: str,
        asset: Optional[str] = None,
        signal_title: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
        **metadata: Any,
    ) -> UniversalMarket:
        title = signal_title or f"{chain} wallet signal"

        return UniversalMarket(
            market_id=f"{chain}:wallet:{wallet_address}".lower(),
            market_type=MarketType.WALLET_SIGNAL,
            title=title,
            venue=VenueRef(
                venue_id=chain.lower(),
                venue_name=chain,
                venue_type="blockchain_wallet",
                raw_market_id=wallet_address,
                raw_symbol=asset,
            ),
            status=MarketStatus.ACTIVE,
            settlement_type=SettlementType.UNKNOWN,
            base_asset=asset,
            tags=[chain.lower(), "wallet_signal"],
            raw=raw or {},
            metadata=metadata,
        )

    @staticmethod
    def _price(
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        mid: Optional[float] = None,
        last: Optional[float] = None,
        volume_24h: Optional[float] = None,
        liquidity: Optional[float] = None,
        spread: Optional[float] = None,
        currency: str = "USD",
    ) -> MarketPriceSnapshot:
        if mid is None and bid is not None and ask is not None:
            mid = (float(bid) + float(ask)) / 2.0

        if spread is None and bid is not None and ask is not None:
            spread = float(ask) - float(bid)

        return MarketPriceSnapshot(
            bid=bid,
            ask=ask,
            mid=mid,
            last=last,
            volume_24h=volume_24h,
            liquidity=liquidity,
            spread=spread,
            currency=currency,
        )

    @staticmethod
    def _status(value: str) -> MarketStatus:
        try:
            return MarketStatus(str(value).lower())
        except Exception:
            return MarketStatus.UNKNOWN


def make_market_id(prefix: str = "umm") -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


__all__ = [
    "UMM_VERSION",
    "MarketType",
    "MarketStatus",
    "SettlementType",
    "VenueRef",
    "MarketPriceSnapshot",
    "MarketTimeWindow",
    "UniversalMarket",
    "UniversalMarketFactory",
    "make_market_id",
]
'''

INIT_CODE = r'''from .universal_market import (
    UMM_VERSION,
    MarketType,
    MarketStatus,
    SettlementType,
    VenueRef,
    MarketPriceSnapshot,
    MarketTimeWindow,
    UniversalMarket,
    UniversalMarketFactory,
    make_market_id,
)

__all__ = [
    "UMM_VERSION",
    "MarketType",
    "MarketStatus",
    "SettlementType",
    "VenueRef",
    "MarketPriceSnapshot",
    "MarketTimeWindow",
    "UniversalMarket",
    "UniversalMarketFactory",
    "make_market_id",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.universal_market_model import (
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
    assert market.price.spread == 0.04
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
    assert market.price.spread == 20


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
'''

def ensure_dirs():
    UMM.mkdir(parents=True, exist_ok=True)


def update_oracle_init():
    ORACLE_INIT_PATH.touch(exist_ok=True)
    text = ORACLE_INIT_PATH.read_text(encoding="utf-8")

    line = "from .universal_market_model import UniversalMarket, UniversalMarketFactory, MarketType, MarketStatus"

    if line not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"

    ORACLE_INIT_PATH.write_text(text, encoding="utf-8")


def main():
    print("=" * 40)
    print(" UMM-001 INSTALLER")
    print(" Universal Market Model")
    print("=" * 40)

    ensure_dirs()

    MODEL_PATH.write_text(MODEL_CODE, encoding="utf-8")
    print(f"[OK] Wrote {MODEL_PATH}")

    INIT_PATH.write_text(INIT_CODE, encoding="utf-8")
    print(f"[OK] Wrote {INIT_PATH}")

    TEST_PATH.write_text(TEST_CODE, encoding="utf-8")
    print(f"[OK] Wrote {TEST_PATH}")

    update_oracle_init()
    print(f"[OK] Updated {ORACLE_INIT_PATH}")

    print("\n[DONE] UMM-001 installed")
    print("\nRun:")
    print("py test_umm_001_universal_market_model.py")


if __name__ == "__main__":
    main()