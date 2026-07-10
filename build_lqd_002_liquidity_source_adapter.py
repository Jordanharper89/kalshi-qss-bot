from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "liquidity_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "liquidity_source_adapter.py"
TEST = ROOT / "test_lqd_002_liquidity_source_adapter.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
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
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_source_adapter import (
    LiquiditySourceAdapter,
    build_liquidity_source_snapshot,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.42,
        "ask_price": 0.45,
        "bid_depth": 1200,
        "ask_depth": 800,
        "volume_24h": 10000,
        "open_interest": 50000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-NO",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.55,
        "ask_price": 0.58,
        "bid_depth": 900,
        "ask_depth": 1100,
        "volume_24h": 9000,
        "open_interest": 45000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_liquidity_source_adapter_snapshot():
    adapter = LiquiditySourceAdapter(source_name="liquidity.test")
    assert adapter.assert_read_only() is True

    snap1 = adapter.snapshot(RAW, observed_at="2026-07-09T00:00:00+00:00")
    snap2 = adapter.snapshot(list(reversed(RAW)), observed_at="2026-07-09T00:00:00+00:00")

    assert snap1.schema_version == "LQD-002"
    assert snap1.engine_id == "oracle.discovery.liquidity.source_adapter"
    assert snap1.status == "ok"
    assert snap1.record_count == 2
    assert snap1.read_only is True
    assert snap1.snapshot_hash == snap2.snapshot_hash
    assert snap1.records[0].record_hash
    assert snap1.records[0].spread >= 0.0
    assert snap1.records[0].spread_bps > 0.0
    assert snap1.records[0].total_depth == 2000


def test_liquidity_source_adapter_empty():
    snap = build_liquidity_source_snapshot([], source_name="liquidity.empty")

    assert snap.status == "empty"
    assert snap.record_count == 0
    assert snap.read_only is True
    assert snap.snapshot_hash


def test_liquidity_source_adapter_accepts_aliases():
    snap = build_liquidity_source_snapshot(
        [
            {
                "symbol": "TEST",
                "exchange": "demo",
                "bid": 10,
                "ask": 11,
                "bid_size": 50,
                "ask_size": 25,
                "volume": 1000,
                "oi": 2000,
                "timestamp": "2026-07-09T00:00:00+00:00",
            }
        ],
        source_name="liquidity.alias",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    record = snap.records[0]
    assert record.market_id == "TEST"
    assert record.venue == "demo"
    assert record.asset == "TEST"
    assert record.total_depth == 75
    assert record.spread == 1
    assert record.volume_24h == 1000
    assert record.open_interest == 2000


if __name__ == "__main__":
    test_liquidity_source_adapter_snapshot()
    test_liquidity_source_adapter_empty()
    test_liquidity_source_adapter_accepts_aliases()

    snap = build_liquidity_source_snapshot([], source_name="liquidity.empty")

    print("[PASS] LQD-002 Liquidity Source Adapter")
    print(
        {
            "schema_version": snap.schema_version,
            "engine_id": snap.engine_id,
            "status": snap.status,
            "records": snap.record_count,
            "read_only": snap.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
exports = '''
from .liquidity_source_adapter import (
    LiquiditySourceAdapter,
    LiquiditySourceRecord,
    LiquiditySourceSnapshot,
    build_liquidity_source_snapshot,
)
'''
if "liquidity_source_adapter" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" LQD-002 INSTALLER")
print(" Liquidity Source Adapter")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] LQD-002 installed")
print()
print("Run:")
print("py test_lqd_002_liquidity_source_adapter.py")