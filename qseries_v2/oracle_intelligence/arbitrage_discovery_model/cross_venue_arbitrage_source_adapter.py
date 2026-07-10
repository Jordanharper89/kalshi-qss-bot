"""
ADM-002 Cross-Venue Arbitrage Source Adapter

Read-only source adapter for cross-venue arbitrage market quotes.

Normalizes raw venue quotes into deterministic immutable quote snapshots.
No trading, routing, order placement, sizing, leg execution, or exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple


SCHEMA_VERSION = "ADM-002"
ADAPTER_ID = "oracle.discovery.source.cross_venue_arbitrage"
ADAPTER_NAME = "Cross-Venue Arbitrage Source Adapter"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


def _read(raw: Any, key: str, default: Any = None) -> Any:
    if isinstance(raw, Mapping):
        return raw.get(key, default)
    return getattr(raw, key, default)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _stable_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return "{" + ",".join(
            f"{str(k)}:{_stable_text(v)}"
            for k, v in sorted(value.items(), key=lambda x: str(x[0]))
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}.{digest}"


@dataclass(frozen=True)
class CrossVenueQuoteSnapshot:
    quote_id: str
    symbol: str
    base_asset: str
    quote_asset: str
    venue: str
    bid: float
    ask: float
    last: float
    mid: float
    spread: float
    fee_bps: float = 0.0
    liquidity: float = 0.0
    volume_24h: float = 0.0
    latency_ms: float = 0.0
    status: str = "active"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        symbol = str(self.symbol).upper().replace("/", "-")
        base = str(self.base_asset).upper()
        quote = str(self.quote_asset).upper()
        bid = max(0.0, _float(self.bid))
        ask = max(0.0, _float(self.ask))
        last = max(0.0, _float(self.last))
        mid = max(0.0, _float(self.mid))
        spread = max(0.0, _float(self.spread))

        if mid == 0.0 and bid > 0.0 and ask > 0.0:
            mid = round((bid + ask) / 2.0, 12)

        if spread == 0.0 and bid > 0.0 and ask > 0.0:
            spread = round(max(0.0, ask - bid), 12)

        if last == 0.0:
            last = mid if mid > 0.0 else ask if ask > 0.0 else bid

        object.__setattr__(self, "quote_id", str(self.quote_id))
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "base_asset", base)
        object.__setattr__(self, "quote_asset", quote)
        object.__setattr__(self, "venue", str(self.venue).lower())
        object.__setattr__(self, "bid", bid)
        object.__setattr__(self, "ask", ask)
        object.__setattr__(self, "last", last)
        object.__setattr__(self, "mid", mid)
        object.__setattr__(self, "spread", spread)
        object.__setattr__(self, "fee_bps", max(0.0, _float(self.fee_bps)))
        object.__setattr__(self, "liquidity", max(0.0, _float(self.liquidity)))
        object.__setattr__(self, "volume_24h", max(0.0, _float(self.volume_24h)))
        object.__setattr__(self, "latency_ms", max(0.0, _float(self.latency_ms)))
        object.__setattr__(self, "status", str(self.status or "active").lower())
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "symbol": self.symbol,
            "base_asset": self.base_asset,
            "quote_asset": self.quote_asset,
            "venue": self.venue,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "mid": self.mid,
            "spread": self.spread,
            "fee_bps": self.fee_bps,
            "liquidity": self.liquidity,
            "volume_24h": self.volume_24h,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CrossVenueArbitrageSourceBatch:
    schema_version: str
    adapter_id: str
    source_name: str
    snapshots: Tuple[CrossVenueQuoteSnapshot, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class CrossVenueArbitrageSourceAdapter:
    schema_version = SCHEMA_VERSION
    adapter_id = ADAPTER_ID
    adapter_name = ADAPTER_NAME
    read_only = True

    def __init__(self, source_name: str = "generic_cross_venue_arbitrage") -> None:
        self.source_name = str(source_name or "generic_cross_venue_arbitrage")

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "source_name": self.source_name,
            "read_only": True,
            "normalizes_to": "CrossVenueQuoteSnapshot",
            "market_family": "cross_venue_arbitrage",
            "supports_replay": True,
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "route_allowed": False,
            "leg_execution_allowed": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def normalize_batch(self, raw_records: Sequence[Any]) -> CrossVenueArbitrageSourceBatch:
        started_at = _utc_now_iso()
        raw_tuple = tuple(raw_records or ())

        snapshots = tuple(
            sorted(
                (self.normalize_record(raw) for raw in raw_tuple),
                key=lambda s: (s.symbol, s.venue, s.quote_id),
            )
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "adapter_id": self.adapter_id,
                "source_name": self.source_name,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "raw_records_seen": len(raw_tuple),
                "snapshots_emitted": len(snapshots),
                "read_only": True,
                "deterministic_sort": True,
                "execution_allowed": False,
            }
        )

        return CrossVenueArbitrageSourceBatch(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            source_name=self.source_name,
            snapshots=snapshots,
            telemetry=telemetry,
            read_only=True,
        )

    def normalize_record(self, raw: Any) -> CrossVenueQuoteSnapshot:
        symbol = (
            _read(raw, "symbol", None)
            or _read(raw, "pair", None)
            or _read(raw, "market", None)
            or _stable_id("arb.symbol", {"source": self.source_name, "raw": _stable_text(raw)})
        )
        symbol = str(symbol).upper().replace("/", "-")

        if "-" in symbol:
            base_asset, quote_asset = symbol.split("-", 1)
        else:
            base_asset = str(_read(raw, "base_asset", _read(raw, "base", symbol))).upper()
            quote_asset = str(_read(raw, "quote_asset", _read(raw, "quote", "USD"))).upper()
            symbol = f"{base_asset}-{quote_asset}"

        venue = str(_read(raw, "venue", _read(raw, "exchange", "unknown"))).lower()
        bid = _float(_read(raw, "bid", _read(raw, "best_bid", 0.0)))
        ask = _float(_read(raw, "ask", _read(raw, "best_ask", 0.0)))
        last = _float(_read(raw, "last", _read(raw, "last_price", _read(raw, "price", 0.0))))
        mid = _float(_read(raw, "mid", _read(raw, "mid_price", 0.0)))
        spread = _float(_read(raw, "spread", 0.0))

        quote_id = (
            _read(raw, "quote_id", None)
            or _read(raw, "id", None)
            or _stable_id(
                "quote",
                {
                    "symbol": symbol,
                    "venue": venue,
                    "bid": bid,
                    "ask": ask,
                    "last": last,
                    "source": self.source_name,
                },
            )
        )

        metadata = {}
        raw_metadata = _read(raw, "metadata", None)
        if isinstance(raw_metadata, Mapping):
            metadata.update(dict(raw_metadata))

        metadata["source_name"] = self.source_name
        metadata["adapter_id"] = self.adapter_id

        return CrossVenueQuoteSnapshot(
            quote_id=str(quote_id),
            symbol=symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            venue=venue,
            bid=bid,
            ask=ask,
            last=last,
            mid=mid,
            spread=spread,
            fee_bps=_float(_read(raw, "fee_bps", _read(raw, "taker_fee_bps", 0.0))),
            liquidity=_float(_read(raw, "liquidity", _read(raw, "depth", 0.0))),
            volume_24h=_float(_read(raw, "volume_24h", _read(raw, "volume", 0.0))),
            latency_ms=_float(_read(raw, "latency_ms", 0.0)),
            status=str(_read(raw, "status", "active")).lower(),
            metadata=metadata,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ADAPTER_ID",
    "ADAPTER_NAME",
    "CrossVenueQuoteSnapshot",
    "CrossVenueArbitrageSourceBatch",
    "CrossVenueArbitrageSourceAdapter",
]
