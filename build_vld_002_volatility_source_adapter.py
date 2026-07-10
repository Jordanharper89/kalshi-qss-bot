from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "volatility_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "volatility_source_adapter.py"
TEST = ROOT / "test_vld_002_volatility_source_adapter.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


READ_ONLY = True
SCHEMA_VERSION = "VLD-002"
ENGINE_ID = "oracle.discovery.volatility.source_adapter"


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
class VolatilitySourceRecord:
    source_id: str
    market_id: str
    venue: str
    asset: str
    observed_at: str
    realized_volatility: float = 0.0
    implied_volatility: float = 0.0
    baseline_volatility: float = 0.0
    volatility_change: float = 0.0
    volatility_ratio: float = 0.0
    price_change: float = 0.0
    volume: float = 0.0
    window: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def record_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class VolatilitySourceSnapshot:
    schema_version: str
    engine_id: str
    status: str
    source_name: str
    observed_at: str
    record_count: int
    records: Tuple[VolatilitySourceRecord, ...]
    read_only: bool = True
    snapshot_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["records"] = [r.canonical() for r in self.records]
        return _deep_sort(data)


class VolatilitySourceAdapter:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(self, source_name: str = "volatility.generic") -> None:
        self.source_name = str(source_name or "volatility.generic")

    def normalize_record(self, raw: Mapping[str, Any]) -> VolatilitySourceRecord:
        if not isinstance(raw, Mapping):
            raise TypeError("raw volatility record must be a mapping")

        market_id = _to_str(raw.get("market_id", raw.get("market", raw.get("symbol", ""))))
        venue = _to_str(raw.get("venue", raw.get("exchange", self.source_name)))
        asset = _to_str(raw.get("asset", raw.get("instrument", raw.get("symbol", market_id))))

        observed_at = _to_str(raw.get("observed_at", raw.get("timestamp", raw.get("time", ""))))
        if not observed_at:
            observed_at = "1970-01-01T00:00:00+00:00"

        realized = _to_float(raw.get("realized_volatility", raw.get("rv", raw.get("realized_vol", 0.0))))
        implied = _to_float(raw.get("implied_volatility", raw.get("iv", raw.get("implied_vol", 0.0))))
        baseline = _to_float(raw.get("baseline_volatility", raw.get("baseline", raw.get("avg_volatility", 0.0))))
        price_change = _to_float(raw.get("price_change", raw.get("return", raw.get("ret", 0.0))))
        volume = _to_float(raw.get("volume", raw.get("vol", 0.0)))
        window = _to_str(raw.get("window", raw.get("lookback", "unknown")))

        volatility_change = _to_float(raw.get("volatility_change", 0.0))
        if volatility_change == 0.0:
            volatility_change = realized - baseline

        volatility_ratio = _to_float(raw.get("volatility_ratio", 0.0))
        if volatility_ratio == 0.0 and baseline > 0:
            volatility_ratio = realized / baseline

        metadata = dict(raw.get("metadata", {})) if isinstance(raw.get("metadata", {}), Mapping) else {}

        identity_payload = {
            "source_name": self.source_name,
            "market_id": market_id,
            "venue": venue,
            "asset": asset,
            "observed_at": observed_at,
            "realized_volatility": realized,
            "implied_volatility": implied,
            "baseline_volatility": baseline,
            "volatility_change": volatility_change,
            "volatility_ratio": volatility_ratio,
            "price_change": price_change,
            "volume": volume,
            "window": window,
        }

        source_id = _to_str(raw.get("source_id", ""))
        if not source_id:
            source_id = _stable_hash(identity_payload)

        metadata["raw_hash"] = _stable_hash(dict(raw))

        return VolatilitySourceRecord(
            source_id=source_id,
            market_id=market_id,
            venue=venue,
            asset=asset,
            observed_at=observed_at,
            realized_volatility=realized,
            implied_volatility=implied,
            baseline_volatility=baseline,
            volatility_change=volatility_change,
            volatility_ratio=volatility_ratio,
            price_change=price_change,
            volume=volume,
            window=window,
            metadata=metadata,
        )

    def snapshot(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> VolatilitySourceSnapshot:
        records: List[VolatilitySourceRecord] = [
            self.normalize_record(raw) for raw in list(raw_records or [])
        ]

        records_sorted = tuple(
            sorted(
                records,
                key=lambda r: (
                    r.market_id,
                    r.venue,
                    r.asset,
                    r.window,
                    r.observed_at,
                    r.source_id,
                ),
            )
        )

        status = "ok" if records_sorted else "empty"
        snapshot_time = observed_at or (records_sorted[0].observed_at if records_sorted else _utc_now_iso())

        unsigned = VolatilitySourceSnapshot(
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

        return VolatilitySourceSnapshot(
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
                "realized_volatility_normalization",
                "implied_volatility_normalization",
                "baseline_ratio_calculation",
            ],
        }

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def build_volatility_source_snapshot(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "volatility.generic",
    observed_at: Optional[str] = None,
) -> VolatilitySourceSnapshot:
    return VolatilitySourceAdapter(source_name=source_name).snapshot(
        raw_records=raw_records,
        observed_at=observed_at,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "VolatilitySourceRecord",
    "VolatilitySourceSnapshot",
    "VolatilitySourceAdapter",
    "build_volatility_source_snapshot",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_source_adapter import (
    VolatilitySourceAdapter,
    build_volatility_source_snapshot,
)


RAW = [
    {
        "market_id": "KXVOL-EXPAND",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.42,
        "implied_volatility": 0.38,
        "baseline_volatility": 0.20,
        "price_change": 0.08,
        "volume": 12000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXVOL-CALM",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.12,
        "implied_volatility": 0.14,
        "baseline_volatility": 0.20,
        "price_change": 0.01,
        "volume": 9000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_volatility_source_adapter_snapshot():
    adapter = VolatilitySourceAdapter(source_name="volatility.test")
    assert adapter.assert_read_only() is True

    snap1 = adapter.snapshot(RAW, observed_at="2026-07-09T00:00:00+00:00")
    snap2 = adapter.snapshot(list(reversed(RAW)), observed_at="2026-07-09T00:00:00+00:00")

    assert snap1.schema_version == "VLD-002"
    assert snap1.engine_id == "oracle.discovery.volatility.source_adapter"
    assert snap1.status == "ok"
    assert snap1.record_count == 2
    assert snap1.read_only is True
    assert snap1.snapshot_hash == snap2.snapshot_hash
    assert snap1.records[0].record_hash
    assert snap1.records[0].volatility_ratio > 0.0


def test_volatility_source_adapter_empty():
    snap = build_volatility_source_snapshot([], source_name="volatility.empty")

    assert snap.status == "empty"
    assert snap.record_count == 0
    assert snap.read_only is True
    assert snap.snapshot_hash


def test_volatility_source_adapter_accepts_aliases():
    snap = build_volatility_source_snapshot(
        [
            {
                "symbol": "TEST",
                "exchange": "demo",
                "rv": 0.30,
                "iv": 0.35,
                "baseline": 0.15,
                "return": 0.05,
                "vol": 1000,
                "lookback": "4h",
                "timestamp": "2026-07-09T00:00:00+00:00",
            }
        ],
        source_name="volatility.alias",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    record = snap.records[0]
    assert record.market_id == "TEST"
    assert record.venue == "demo"
    assert record.asset == "TEST"
    assert record.realized_volatility == 0.30
    assert record.implied_volatility == 0.35
    assert record.baseline_volatility == 0.15
    assert record.volatility_change == 0.15
    assert record.volatility_ratio == 2.0
    assert record.window == "4h"


if __name__ == "__main__":
    test_volatility_source_adapter_snapshot()
    test_volatility_source_adapter_empty()
    test_volatility_source_adapter_accepts_aliases()

    snap = build_volatility_source_snapshot([], source_name="volatility.empty")

    print("[PASS] VLD-002 Volatility Source Adapter")
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
from .volatility_source_adapter import (
    VolatilitySourceAdapter,
    VolatilitySourceRecord,
    VolatilitySourceSnapshot,
    build_volatility_source_snapshot,
)
'''
if "volatility_source_adapter" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" VLD-002 INSTALLER")
print(" Volatility Source Adapter")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] VLD-002 installed")
print()
print("Run:")
print("py test_vld_002_volatility_source_adapter.py")