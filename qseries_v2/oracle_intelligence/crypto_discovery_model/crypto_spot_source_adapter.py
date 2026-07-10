"""
CDM-002 Crypto Spot Source Adapter

Read-only source adapter for crypto spot market snapshots.

Normalizes raw crypto records into deterministic immutable spot snapshots.
No trading, swapping, sizing, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple


SCHEMA_VERSION = "CDM-002"
ADAPTER_ID = "oracle.discovery.source.crypto_spot"
ADAPTER_NAME = "Crypto Spot Source Adapter"


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
        return "{" + ",".join(f"{k}:{_stable_text(v)}" for k, v in sorted(value.items())) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}.{digest}"


@dataclass(frozen=True)
class CryptoSpotSnapshot:
    symbol: str
    base_asset: str
    quote_asset: str
    exchange: str
    price: float
    fair_value: float
    bid: float = 0.0
    ask: float = 0.0
    spread: float = 0.0
    volume_24h: float = 0.0
    liquidity: float = 0.0
    volatility: float = 0.0
    status: str = "active"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        symbol = str(self.symbol).upper().replace("/", "-")
        base = str(self.base_asset).upper()
        quote = str(self.quote_asset).upper()
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "base_asset", base)
        object.__setattr__(self, "quote_asset", quote)
        object.__setattr__(self, "exchange", str(self.exchange).lower())
        object.__setattr__(self, "price", max(0.0, _float(self.price)))
        object.__setattr__(self, "fair_value", max(0.0, _float(self.fair_value, self.price)))
        object.__setattr__(self, "bid", max(0.0, _float(self.bid)))
        object.__setattr__(self, "ask", max(0.0, _float(self.ask)))
        object.__setattr__(self, "spread", max(0.0, _float(self.spread)))
        object.__setattr__(self, "volume_24h", max(0.0, _float(self.volume_24h)))
        object.__setattr__(self, "liquidity", max(0.0, _float(self.liquidity)))
        object.__setattr__(self, "volatility", max(0.0, _float(self.volatility)))
        object.__setattr__(self, "status", str(self.status or "active").lower())
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "base_asset": self.base_asset,
            "quote_asset": self.quote_asset,
            "exchange": self.exchange,
            "price": self.price,
            "fair_value": self.fair_value,
            "bid": self.bid,
            "ask": self.ask,
            "spread": self.spread,
            "volume_24h": self.volume_24h,
            "liquidity": self.liquidity,
            "volatility": self.volatility,
            "status": self.status,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CryptoSpotSourceBatch:
    schema_version: str
    adapter_id: str
    source_name: str
    snapshots: Tuple[CryptoSpotSnapshot, ...]
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


class CryptoSpotSourceAdapter:
    schema_version = SCHEMA_VERSION
    adapter_id = ADAPTER_ID
    adapter_name = ADAPTER_NAME
    read_only = True

    def __init__(self, source_name: str = "generic_crypto_spot") -> None:
        self.source_name = str(source_name or "generic_crypto_spot")

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "source_name": self.source_name,
            "read_only": True,
            "normalizes_to": "CryptoSpotSnapshot",
            "market_family": "crypto_spot",
            "supports_replay": True,
            "deterministic": True,
            "telemetry": True,
            "execution": False,
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

    def normalize_batch(self, raw_records: Sequence[Any]) -> CryptoSpotSourceBatch:
        started_at = _utc_now_iso()
        raw_tuple = tuple(raw_records or ())

        snapshots = tuple(
            sorted(
                (self.normalize_record(raw) for raw in raw_tuple),
                key=lambda s: (s.exchange, s.symbol),
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
            }
        )

        return CryptoSpotSourceBatch(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            source_name=self.source_name,
            snapshots=snapshots,
            telemetry=telemetry,
            read_only=True,
        )

    def normalize_record(self, raw: Any) -> CryptoSpotSnapshot:
        symbol = (
            _read(raw, "symbol", None)
            or _read(raw, "pair", None)
            or _read(raw, "market", None)
            or _stable_id("crypto.symbol", {"source": self.source_name, "raw": _stable_text(raw)})
        )

        symbol = str(symbol).upper().replace("/", "-")

        if "-" in symbol:
            base_asset, quote_asset = symbol.split("-", 1)
        else:
            base_asset = str(_read(raw, "base_asset", _read(raw, "base", symbol))).upper()
            quote_asset = str(_read(raw, "quote_asset", _read(raw, "quote", "USD"))).upper()
            symbol = f"{base_asset}-{quote_asset}"

        price = _float(_read(raw, "price", _read(raw, "last", _read(raw, "last_price", 0.0))))
        fair_value = _float(_read(raw, "fair_value", _read(raw, "model_price", price)), price)

        bid = _float(_read(raw, "bid", 0.0))
        ask = _float(_read(raw, "ask", 0.0))
        spread = _float(_read(raw, "spread", 0.0))
        if spread == 0.0 and bid > 0.0 and ask > 0.0:
            spread = max(0.0, ask - bid)

        metadata = {}
        raw_metadata = _read(raw, "metadata", None)
        if isinstance(raw_metadata, Mapping):
            metadata.update(dict(raw_metadata))

        metadata["source_name"] = self.source_name
        metadata["adapter_id"] = self.adapter_id

        return CryptoSpotSnapshot(
            symbol=symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            exchange=str(_read(raw, "exchange", self.source_name)),
            price=price,
            fair_value=fair_value,
            bid=bid,
            ask=ask,
            spread=spread,
            volume_24h=_float(_read(raw, "volume_24h", _read(raw, "volume", 0.0))),
            liquidity=_float(_read(raw, "liquidity", _read(raw, "depth", 0.0))),
            volatility=_float(_read(raw, "volatility", _read(raw, "volatility_24h", 0.0))),
            status=str(_read(raw, "status", "active")).lower(),
            metadata=metadata,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ADAPTER_ID",
    "ADAPTER_NAME",
    "CryptoSpotSnapshot",
    "CryptoSpotSourceBatch",
    "CryptoSpotSourceAdapter",
]
