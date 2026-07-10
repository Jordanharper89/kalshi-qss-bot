
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


READ_ONLY = True
SCHEMA_VERSION = "LQD-002"
ENGINE_ID = "oracle.discovery.liquidity.source_adapter"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_sort(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_deep_sort(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(v) for v in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return sha256(repr(_deep_sort(payload)).encode("utf-8")).hexdigest()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


@dataclass(frozen=True)
class LiquiditySourceRecord:
    source_id: str
    market_id: str
    venue: str
    asset: str
    observed_at: str
    bid_price: float = 0.0
    ask_price: float = 0.0
    bid_depth: float = 0.0
    ask_depth: float = 0.0
    total_depth: float = 0.0
    spread: float = 0.0
    spread_bps: float = 0.0
    volume_24h: float = 0.0
    open_interest: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def record_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class LiquiditySourceSnapshot:
    schema_version: str
    engine_id: str
    status: str
    source_name: str
    observed_at: str
    record_count: int
    records: Tuple[LiquiditySourceRecord, ...]
    read_only: bool = True
    snapshot_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["records"] = [r.canonical() for r in self.records]
        return _deep_sort(data)


class LiquiditySourceAdapter:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(self, source_name: str = "liquidity.generic") -> None:
        self.source_name = str(source_name or "liquidity.generic")

    def normalize_record(self, raw: Mapping[str, Any]) -> LiquiditySourceRecord:
        if not isinstance(raw, Mapping):
            raise TypeError("raw liquidity record must be a mapping")

        market_id = _to_str(raw.get("market_id", raw.get("market", raw.get("symbol", ""))))
        venue = _to_str(raw.get("venue", raw.get("exchange", self.source_name)))
        asset = _to_str(raw.get("asset", raw.get("instrument", raw.get("symbol", market_id))))

        observed_at = _to_str(raw.get("observed_at", raw.get("timestamp", raw.get("time", ""))))
        if not observed_at:
            observed_at = "1970-01-01T00:00:00+00:00"

        bid_price = _to_float(raw.get("bid_price", raw.get("bid", 0.0)))
        ask_price = _to_float(raw.get("ask_price", raw.get("ask", 0.0)))
        bid_depth = _to_float(raw.get("bid_depth", raw.get("bid_size", raw.get("bidQty", 0.0))))
        ask_depth = _to_float(raw.get("ask_depth", raw.get("ask_size", raw.get("askQty", 0.0))))
        total_depth = _to_float(raw.get("total_depth", bid_depth + ask_depth))
        volume_24h = _to_float(raw.get("volume_24h", raw.get("volume", raw.get("vol", 0.0))))
        open_interest = _to_float(raw.get("open_interest", raw.get("oi", 0.0)))

        spread = _to_float(raw.get("spread", 0.0))
        if spread == 0.0 and ask_price and bid_price:
            spread = max(0.0, ask_price - bid_price)

        mid = (bid_price + ask_price) / 2.0 if bid_price and ask_price else 0.0
        spread_bps = _to_float(raw.get("spread_bps", 0.0))
        if spread_bps == 0.0 and mid > 0.0:
            spread_bps = (spread / mid) * 10000.0

        metadata = dict(raw.get("metadata", {})) if isinstance(raw.get("metadata", {}), Mapping) else {}

        identity_payload = {
            "source_name": self.source_name,
            "market_id": market_id,
            "venue": venue,
            "asset": asset,
            "observed_at": observed_at,
            "bid_price": bid_price,
            "ask_price": ask_price,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "total_depth": total_depth,
            "spread": spread,
            "spread_bps": spread_bps,
            "volume_24h": volume_24h,
            "open_interest": open_interest,
        }

        source_id = _to_str(raw.get("source_id", ""))
        if not source_id:
            source_id = _stable_hash(identity_payload)

        metadata["raw_hash"] = _stable_hash(dict(raw))

        return LiquiditySourceRecord(
            source_id=source_id,
            market_id=market_id,
            venue=venue,
            asset=asset,
            observed_at=observed_at,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            total_depth=total_depth,
            spread=spread,
            spread_bps=spread_bps,
            volume_24h=volume_24h,
            open_interest=open_interest,
            metadata=metadata,
        )

    def snapshot(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> LiquiditySourceSnapshot:
        records: List[LiquiditySourceRecord] = [
            self.normalize_record(raw) for raw in list(raw_records or [])
        ]

        records_sorted = tuple(
            sorted(
                records,
                key=lambda r: (
                    r.market_id,
                    r.venue,
                    r.asset,
                    r.observed_at,
                    r.source_id,
                ),
            )
        )

        status = "ok" if records_sorted else "empty"
        snapshot_time = observed_at or (records_sorted[0].observed_at if records_sorted else _utc_now_iso())

        unsigned = LiquiditySourceSnapshot(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            source_name=self.source_name,
            observed_at=snapshot_time,
            record_count=len(records_sorted),
            records=records_sorted,
            read_only=True,
            snapshot_hash="",
        )

        return LiquiditySourceSnapshot(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            source_name=unsigned.source_name,
            observed_at=unsigned.observed_at,
            record_count=unsigned.record_count,
            records=unsigned.records,
            read_only=True,
            snapshot_hash=_stable_hash(unsigned.canonical()),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "normalize_record",
                "snapshot",
                "deterministic_order_independent_hashing",
                "spread_calculation",
                "spread_bps_calculation",
                "depth_normalization",
            ],
        }

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def build_liquidity_source_snapshot(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "liquidity.generic",
    observed_at: Optional[str] = None,
) -> LiquiditySourceSnapshot:
    return LiquiditySourceAdapter(source_name=source_name).snapshot(
        raw_records=raw_records,
        observed_at=observed_at,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "LiquiditySourceRecord",
    "LiquiditySourceSnapshot",
    "LiquiditySourceAdapter",
    "build_liquidity_source_snapshot",
]
