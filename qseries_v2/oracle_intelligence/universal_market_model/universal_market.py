"""
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
            mid = round((float(bid) + float(ask)) / 2.0, 12)

        if spread is None and bid is not None and ask is not None:
            spread = round(float(ask) - float(bid), 12)

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
