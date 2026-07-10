from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "solana_launch_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ADAPTER_FILE = MODULE_DIR / "solana_launch_source_adapter.py"
TEST_FILE = ROOT / "test_sld_002_solana_launch_source_adapter.py"
INIT_FILE = MODULE_DIR / "__init__.py"

ADAPTER_CODE = r'''"""
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
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_source_adapter import (
    SolanaLaunchSourceAdapter,
)


def test_sld_002_solana_launch_source_adapter():
    raw_records = [
        {
            "mint": "mint_b",
            "symbol": "BETA",
            "name": "Beta Token",
            "pool": "pool_b",
            "dex": "Raydium",
            "quote": "SOL",
            "liquidity": 25000,
            "market_cap": 120000,
            "volume_5m": 8000,
            "holders": 120,
            "age": 90,
            "mint_disabled": True,
            "freeze_disabled": True,
            "liquidity_burned": True,
            "status": "active",
            "creator": "wallet_b",
            "signature": "tx_b",
            "timestamp": "2026-01-01T00:02:00Z",
        },
        {
            "token_mint": "mint_a",
            "ticker": "ALPHA",
            "name": "Alpha Token",
            "pool_address": "pool_a",
            "dex": "raydium",
            "quote_asset": "SOL",
            "liquidity_usd": 50000,
            "market_cap_usd": 200000,
            "volume_5m_usd": 15000,
            "holder_count": 250,
            "age_seconds": 30,
            "mint_authority_disabled": True,
            "freeze_authority_disabled": True,
            "lp_burned": True,
            "pool_status": "active",
            "deployer_wallet": "wallet_a",
            "tx_signature": "tx_a",
            "detected_at": "2026-01-01T00:01:00Z",
        },
    ]

    adapter = SolanaLaunchSourceAdapter(source_name="sld_002_test_feed")
    caps = adapter.capabilities()
    health = adapter.health()

    batch_1 = adapter.normalize_batch(raw_records)
    batch_2 = adapter.normalize_batch(list(reversed(raw_records)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["snipe_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_1.schema_version == "SLD-002"
    assert batch_1.adapter_id == "oracle.discovery.source.solana_launch"
    assert batch_1.read_only is True
    assert len(batch_1.snapshots) == 2

    order_1 = [(s.symbol, s.mint, s.pool_address) for s in batch_1.snapshots]
    order_2 = [(s.symbol, s.mint, s.pool_address) for s in batch_2.snapshots]
    assert order_1 == order_2
    assert order_1 == [
        ("ALPHA", "mint_a", "pool_a"),
        ("BETA", "mint_b", "pool_b"),
    ]

    first = batch_1.snapshots[0]
    assert first.symbol == "ALPHA"
    assert first.mint == "mint_a"
    assert first.pool_address == "pool_a"
    assert first.dex == "raydium"
    assert first.quote_asset == "SOL"
    assert first.liquidity_usd == 50000.0
    assert first.market_cap_usd == 200000.0
    assert first.volume_5m_usd == 15000.0
    assert first.holder_count == 250
    assert first.age_seconds == 30.0
    assert first.mint_authority_disabled is True
    assert first.freeze_authority_disabled is True
    assert first.lp_burned is True
    assert first.read_only is True
    assert first.metadata["source_name"] == "sld_002_test_feed"

    try:
        first.metadata["new"] = "mutation"
        raise AssertionError("snapshot metadata should be immutable")
    except TypeError:
        pass

    d = batch_1.to_dict()
    assert d["schema_version"] == "SLD-002"
    assert d["read_only"] is True
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["launches_seen"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["signing_allowed"] is False

    print("[PASS] SLD-002 Solana Launch Source Adapter")
    print(
        {
            "schema_version": d["schema_version"],
            "adapter_id": d["adapter_id"],
            "snapshots": len(d["snapshots"]),
            "launches_seen": d["telemetry"]["launches_seen"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_sld_002_solana_launch_source_adapter()
'''

INIT_EXPORT = '''
try:
    from .solana_launch_source_adapter import (
        SolanaLaunchSnapshot,
        SolanaLaunchSourceBatch,
        SolanaLaunchSourceAdapter,
    )
except Exception:
    pass
'''

ADAPTER_FILE.write_text(ADAPTER_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "SolanaLaunchSourceAdapter" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SLD-002 INSTALLER")
print(" Solana Launch Source Adapter")
print("========================================")
print(f"[OK] Wrote {ADAPTER_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] SLD-002 installed")
print()
print("Run:")
print("py test_sld_002_solana_launch_source_adapter.py")