"""
WDM-002 Wallet Intelligence Source Adapter

Read-only source adapter for wallet activity records.

Normalizes raw wallet/on-chain records into deterministic immutable wallet
activity snapshots.

No signing, fund movement, swaps, trading, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple


SCHEMA_VERSION = "WDM-002"
ADAPTER_ID = "oracle.discovery.source.wallet_intelligence"
ADAPTER_NAME = "Wallet Intelligence Source Adapter"


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
class WalletActivitySnapshot:
    event_id: str
    wallet: str
    chain: str
    symbol: str
    token_address: str
    action: str
    amount: float
    usd_value: float
    price: float
    tx_hash: str
    block_time: str
    counterparty: str = ""
    wallet_score: float = 0.0
    realized_pnl: float = 0.0
    win_rate: float = 0.0
    holding_count: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "event_id", str(self.event_id))
        object.__setattr__(self, "wallet", str(self.wallet))
        object.__setattr__(self, "chain", str(self.chain).lower())
        object.__setattr__(self, "symbol", str(self.symbol).upper())
        object.__setattr__(self, "token_address", str(self.token_address))
        object.__setattr__(self, "action", str(self.action).lower())
        object.__setattr__(self, "amount", max(0.0, _float(self.amount)))
        object.__setattr__(self, "usd_value", max(0.0, _float(self.usd_value)))
        object.__setattr__(self, "price", max(0.0, _float(self.price)))
        object.__setattr__(self, "tx_hash", str(self.tx_hash))
        object.__setattr__(self, "block_time", str(self.block_time))
        object.__setattr__(self, "counterparty", str(self.counterparty or ""))
        object.__setattr__(self, "wallet_score", max(0.0, min(1.0, _float(self.wallet_score))))
        object.__setattr__(self, "realized_pnl", _float(self.realized_pnl))
        object.__setattr__(self, "win_rate", max(0.0, min(1.0, _float(self.win_rate))))
        object.__setattr__(self, "holding_count", int(max(0, _float(self.holding_count))))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "wallet": self.wallet,
            "chain": self.chain,
            "symbol": self.symbol,
            "token_address": self.token_address,
            "action": self.action,
            "amount": self.amount,
            "usd_value": self.usd_value,
            "price": self.price,
            "tx_hash": self.tx_hash,
            "block_time": self.block_time,
            "counterparty": self.counterparty,
            "wallet_score": self.wallet_score,
            "realized_pnl": self.realized_pnl,
            "win_rate": self.win_rate,
            "holding_count": self.holding_count,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligenceSourceBatch:
    schema_version: str
    adapter_id: str
    source_name: str
    snapshots: Tuple[WalletActivitySnapshot, ...]
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


class WalletIntelligenceSourceAdapter:
    schema_version = SCHEMA_VERSION
    adapter_id = ADAPTER_ID
    adapter_name = ADAPTER_NAME
    read_only = True

    def __init__(self, source_name: str = "generic_wallet_intelligence") -> None:
        self.source_name = str(source_name or "generic_wallet_intelligence")

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "source_name": self.source_name,
            "read_only": True,
            "normalizes_to": "WalletActivitySnapshot",
            "market_family": "wallet_intelligence",
            "supports_replay": True,
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
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

    def normalize_batch(self, raw_records: Sequence[Any]) -> WalletIntelligenceSourceBatch:
        started_at = _utc_now_iso()
        raw_tuple = tuple(raw_records or ())

        snapshots = tuple(
            sorted(
                (self.normalize_record(raw) for raw in raw_tuple),
                key=lambda s: (s.chain, s.wallet, s.block_time, s.tx_hash, s.event_id),
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
                "wallets_seen": len({s.wallet for s in snapshots}),
                "read_only": True,
                "deterministic_sort": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
            }
        )

        return WalletIntelligenceSourceBatch(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            source_name=self.source_name,
            snapshots=snapshots,
            telemetry=telemetry,
            read_only=True,
        )

    def normalize_record(self, raw: Any) -> WalletActivitySnapshot:
        wallet = str(_read(raw, "wallet", _read(raw, "address", _read(raw, "owner", ""))))
        chain = str(_read(raw, "chain", _read(raw, "network", "unknown"))).lower()
        symbol = str(_read(raw, "symbol", _read(raw, "token_symbol", "UNKNOWN"))).upper()
        token_address = str(_read(raw, "token_address", _read(raw, "mint", _read(raw, "contract", ""))))
        action = str(_read(raw, "action", _read(raw, "type", _read(raw, "side", "unknown")))).lower()
        tx_hash = str(_read(raw, "tx_hash", _read(raw, "signature", _read(raw, "transaction_hash", ""))))
        block_time = str(_read(raw, "block_time", _read(raw, "timestamp", "")))

        event_id = (
            _read(raw, "event_id", None)
            or _read(raw, "id", None)
            or _stable_id(
                "wallet.event",
                {
                    "wallet": wallet,
                    "chain": chain,
                    "symbol": symbol,
                    "token_address": token_address,
                    "action": action,
                    "tx_hash": tx_hash,
                    "block_time": block_time,
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

        return WalletActivitySnapshot(
            event_id=str(event_id),
            wallet=wallet,
            chain=chain,
            symbol=symbol,
            token_address=token_address,
            action=action,
            amount=_float(_read(raw, "amount", _read(raw, "token_amount", 0.0))),
            usd_value=_float(_read(raw, "usd_value", _read(raw, "value_usd", 0.0))),
            price=_float(_read(raw, "price", _read(raw, "token_price", 0.0))),
            tx_hash=tx_hash,
            block_time=block_time,
            counterparty=str(_read(raw, "counterparty", _read(raw, "to", ""))),
            wallet_score=_float(_read(raw, "wallet_score", _read(raw, "smart_money_score", 0.0))),
            realized_pnl=_float(_read(raw, "realized_pnl", _read(raw, "pnl", 0.0))),
            win_rate=_float(_read(raw, "win_rate", 0.0)),
            holding_count=int(max(0, _float(_read(raw, "holding_count", _read(raw, "positions", 0))))),
            metadata=metadata,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ADAPTER_ID",
    "ADAPTER_NAME",
    "WalletActivitySnapshot",
    "WalletIntelligenceSourceBatch",
    "WalletIntelligenceSourceAdapter",
]
