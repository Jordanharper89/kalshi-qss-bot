"""
SLD-002 Solana Launch Source Adapter

Read-only source adapter for Solana token launch / pool records.

No signing, fund movement, swaps, sniping, routing, buying, selling, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple


SCHEMA_VERSION = "SLD-002"
ADAPTER_ID = "oracle.discovery.source.solana_launch"
ADAPTER_NAME = "Solana Launch Source Adapter"


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


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "ok", "locked", "burned", "disabled"}
    return bool(value)


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
class SolanaLaunchSnapshot:
    launch_id: str
    mint: str
    symbol: str
    name: str
    pool_address: str
    dex: str
    quote_asset: str
    liquidity_usd: float
    market_cap_usd: float
    volume_5m_usd: float
    holder_count: int
    age_seconds: float
    mint_authority_disabled: bool
    freeze_authority_disabled: bool
    lp_burned: bool
    pool_status: str
    deployer_wallet: str = ""
    tx_signature: str = ""
    detected_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "launch_id", str(self.launch_id))
        object.__setattr__(self, "mint", str(self.mint))
        object.__setattr__(self, "symbol", str(self.symbol).upper())
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "pool_address", str(self.pool_address))
        object.__setattr__(self, "dex", str(self.dex).lower())
        object.__setattr__(self, "quote_asset", str(self.quote_asset).upper())
        object.__setattr__(self, "liquidity_usd", max(0.0, _float(self.liquidity_usd)))
        object.__setattr__(self, "market_cap_usd", max(0.0, _float(self.market_cap_usd)))
        object.__setattr__(self, "volume_5m_usd", max(0.0, _float(self.volume_5m_usd)))
        object.__setattr__(self, "holder_count", int(max(0, _float(self.holder_count))))
        object.__setattr__(self, "age_seconds", max(0.0, _float(self.age_seconds)))
        object.__setattr__(self, "mint_authority_disabled", bool(self.mint_authority_disabled))
        object.__setattr__(self, "freeze_authority_disabled", bool(self.freeze_authority_disabled))
        object.__setattr__(self, "lp_burned", bool(self.lp_burned))
        object.__setattr__(self, "pool_status", str(self.pool_status or "unknown").lower())
        object.__setattr__(self, "deployer_wallet", str(self.deployer_wallet or ""))
        object.__setattr__(self, "tx_signature", str(self.tx_signature or ""))
        object.__setattr__(self, "detected_at", str(self.detected_at or ""))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "launch_id": self.launch_id,
            "mint": self.mint,
            "symbol": self.symbol,
            "name": self.name,
            "pool_address": self.pool_address,
            "dex": self.dex,
            "quote_asset": self.quote_asset,
            "liquidity_usd": self.liquidity_usd,
            "market_cap_usd": self.market_cap_usd,
            "volume_5m_usd": self.volume_5m_usd,
            "holder_count": self.holder_count,
            "age_seconds": self.age_seconds,
            "mint_authority_disabled": self.mint_authority_disabled,
            "freeze_authority_disabled": self.freeze_authority_disabled,
            "lp_burned": self.lp_burned,
            "pool_status": self.pool_status,
            "deployer_wallet": self.deployer_wallet,
            "tx_signature": self.tx_signature,
            "detected_at": self.detected_at,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SolanaLaunchSourceBatch:
    schema_version: str
    adapter_id: str
    source_name: str
    snapshots: Tuple[SolanaLaunchSnapshot, ...]
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


class SolanaLaunchSourceAdapter:
    schema_version = SCHEMA_VERSION
    adapter_id = ADAPTER_ID
    adapter_name = ADAPTER_NAME
    read_only = True

    def __init__(self, source_name: str = "generic_solana_launch") -> None:
        self.source_name = str(source_name or "generic_solana_launch")

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "source_name": self.source_name,
            "read_only": True,
            "normalizes_to": "SolanaLaunchSnapshot",
            "market_family": "solana_launch",
            "supports_replay": True,
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
            "snipe_allowed": False,
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

    def normalize_batch(self, raw_records: Sequence[Any]) -> SolanaLaunchSourceBatch:
        started_at = _utc_now_iso()
        raw_tuple = tuple(raw_records or ())

        snapshots = tuple(
            sorted(
                (self.normalize_record(raw) for raw in raw_tuple),
                key=lambda s: (s.age_seconds, s.dex, s.symbol, s.mint, s.pool_address),
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
                "launches_seen": len({s.mint for s in snapshots}),
                "read_only": True,
                "deterministic_sort": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            }
        )

        return SolanaLaunchSourceBatch(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            source_name=self.source_name,
            snapshots=snapshots,
            telemetry=telemetry,
            read_only=True,
        )

    def normalize_record(self, raw: Any) -> SolanaLaunchSnapshot:
        mint = str(_read(raw, "mint", _read(raw, "token_mint", _read(raw, "address", ""))))
        symbol = str(_read(raw, "symbol", _read(raw, "ticker", "UNKNOWN"))).upper()
        name = str(_read(raw, "name", symbol))
        pool_address = str(_read(raw, "pool_address", _read(raw, "pool", _read(raw, "pair_address", ""))))
        dex = str(_read(raw, "dex", _read(raw, "source", "raydium"))).lower()
        tx_signature = str(_read(raw, "tx_signature", _read(raw, "signature", "")))

        launch_id = (
            _read(raw, "launch_id", None)
            or _read(raw, "id", None)
            or _stable_id(
                "solana.launch",
                {
                    "mint": mint,
                    "symbol": symbol,
                    "pool_address": pool_address,
                    "dex": dex,
                    "tx_signature": tx_signature,
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

        return SolanaLaunchSnapshot(
            launch_id=str(launch_id),
            mint=mint,
            symbol=symbol,
            name=name,
            pool_address=pool_address,
            dex=dex,
            quote_asset=str(_read(raw, "quote_asset", _read(raw, "quote", "SOL"))),
            liquidity_usd=_float(_read(raw, "liquidity_usd", _read(raw, "liquidity", 0.0))),
            market_cap_usd=_float(_read(raw, "market_cap_usd", _read(raw, "market_cap", 0.0))),
            volume_5m_usd=_float(_read(raw, "volume_5m_usd", _read(raw, "volume_5m", 0.0))),
            holder_count=int(max(0, _float(_read(raw, "holder_count", _read(raw, "holders", 0))))),
            age_seconds=_float(_read(raw, "age_seconds", _read(raw, "age", 0.0))),
            mint_authority_disabled=_bool(_read(raw, "mint_authority_disabled", _read(raw, "mint_disabled", False))),
            freeze_authority_disabled=_bool(_read(raw, "freeze_authority_disabled", _read(raw, "freeze_disabled", False))),
            lp_burned=_bool(_read(raw, "lp_burned", _read(raw, "liquidity_burned", False))),
            pool_status=str(_read(raw, "pool_status", _read(raw, "status", "active"))),
            deployer_wallet=str(_read(raw, "deployer_wallet", _read(raw, "creator", ""))),
            tx_signature=tx_signature,
            detected_at=str(_read(raw, "detected_at", _read(raw, "timestamp", ""))),
            metadata=metadata,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ADAPTER_ID",
    "ADAPTER_NAME",
    "SolanaLaunchSnapshot",
    "SolanaLaunchSourceBatch",
    "SolanaLaunchSourceAdapter",
]
