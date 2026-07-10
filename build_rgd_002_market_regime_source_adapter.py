from pathlib import Path

ROOT = Path.cwd()
PKG = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "market_regime_discovery_model"
)
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "market_regime_source_adapter.py"
TEST = ROOT / "test_rgd_002_market_regime_source_adapter.py"
INIT = PKG / "__init__.py"

MODULE.write_text(
r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


READ_ONLY = True
SCHEMA_VERSION = "RGD-002"
ENGINE_ID = "oracle.discovery.market_regime.source_adapter"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }

    if isinstance(value, list):
        return [
            _deep_sort(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return tuple(
            _deep_sort(item)
            for item in value
        )

    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(
        _deep_sort(payload)
    ).encode("utf-8")

    return sha256(encoded).hexdigest()


def _to_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None:
            return default

        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        if value is None:
            return default

        return int(value)
    except (TypeError, ValueError):
        return default


def _to_str(
    value: Any,
    default: str = "",
) -> str:
    if value is None:
        return default

    return str(value)


def _clamp(
    value: float,
    low: float = 0.0,
    high: float = 1.0,
) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class MarketRegimeSourceRecord:
    source_id: str
    market_id: str
    venue: str
    asset: str
    observed_at: str
    source_family: str
    signal_type: str
    signal_direction: str
    confidence: float
    magnitude: float
    prior_regime: str = "unknown"
    candidate_regime: str = "unknown"
    transition_type: str = "unknown"
    source_hash: str = ""
    sequence: int = 0
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def record_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class MarketRegimeSourceSnapshot:
    schema_version: str
    engine_id: str
    status: str
    source_name: str
    observed_at: str
    record_count: int
    family_count: int
    market_count: int
    records: Tuple[
        MarketRegimeSourceRecord,
        ...,
    ]
    read_only: bool = True
    snapshot_hash: str = ""

    def canonical(
        self,
        include_snapshot_hash: bool = True,
    ) -> Dict[str, Any]:
        data = asdict(self)
        data["records"] = [
            record.canonical()
            for record in self.records
        ]

        if not include_snapshot_hash:
            data["snapshot_hash"] = ""

        return _deep_sort(data)

    def expected_snapshot_hash(self) -> str:
        return _stable_hash(
            self.canonical(
                include_snapshot_hash=False
            )
        )

    def verify_snapshot_hash(self) -> bool:
        return (
            bool(self.snapshot_hash)
            and self.snapshot_hash
            == self.expected_snapshot_hash()
        )


class MarketRegimeSourceAdapter:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        source_name: str = "market_regime.generic",
    ) -> None:
        self.source_name = str(
            source_name
            or "market_regime.generic"
        )

    def normalize_record(
        self,
        raw: Mapping[str, Any],
    ) -> MarketRegimeSourceRecord:
        if not isinstance(raw, Mapping):
            raise TypeError(
                "raw market regime record "
                "must be a mapping"
            )

        market_id = _to_str(
            raw.get(
                "market_id",
                raw.get(
                    "market",
                    raw.get(
                        "symbol",
                        raw.get("instrument_id", ""),
                    ),
                ),
            )
        )

        venue = _to_str(
            raw.get(
                "venue",
                raw.get(
                    "exchange",
                    raw.get("source_venue", self.source_name),
                ),
            )
        )

        asset = _to_str(
            raw.get(
                "asset",
                raw.get(
                    "instrument",
                    raw.get("symbol", market_id),
                ),
            )
        )

        observed_at = _to_str(
            raw.get(
                "observed_at",
                raw.get(
                    "timestamp",
                    raw.get("time", ""),
                ),
            )
        )

        if not observed_at:
            observed_at = (
                "1970-01-01T00:00:00+00:00"
            )

        source_family = _to_str(
            raw.get(
                "source_family",
                raw.get(
                    "family",
                    raw.get(
                        "discovery_family",
                        "unknown",
                    ),
                ),
            )
        )

        signal_type = _to_str(
            raw.get(
                "signal_type",
                raw.get(
                    "signal",
                    raw.get("event_type", "unknown"),
                ),
            )
        )

        signal_direction = _to_str(
            raw.get(
                "signal_direction",
                raw.get(
                    "direction",
                    raw.get(
                        "relationship",
                        raw.get("regime", "unknown"),
                    ),
                ),
            )
        )

        confidence = _clamp(
            _to_float(
                raw.get(
                    "confidence",
                    raw.get("score", 0.0),
                )
            )
        )

        magnitude = _clamp(
            abs(
                _to_float(
                    raw.get(
                        "magnitude",
                        raw.get(
                            "strength",
                            raw.get("severity", 0.0),
                        ),
                    )
                )
            )
        )

        prior_regime = _to_str(
            raw.get(
                "prior_regime",
                raw.get(
                    "previous_regime",
                    "unknown",
                ),
            )
        )

        candidate_regime = _to_str(
            raw.get(
                "candidate_regime",
                raw.get(
                    "current_regime",
                    raw.get(
                        "target_regime",
                        raw.get("regime", "unknown"),
                    ),
                ),
            )
        )

        transition_type = _to_str(
            raw.get(
                "transition_type",
                raw.get(
                    "transition",
                    "unknown",
                ),
            )
        )

        sequence = _to_int(
            raw.get(
                "sequence",
                raw.get("index", 0),
            )
        )

        source_hash = _to_str(
            raw.get(
                "source_hash",
                raw.get(
                    "result_hash",
                    raw.get(
                        "record_hash",
                        raw.get("event_hash", ""),
                    ),
                ),
            )
        )

        metadata = (
            dict(raw.get("metadata", {}))
            if isinstance(
                raw.get("metadata", {}),
                Mapping,
            )
            else {}
        )

        metadata.update(
            {
                "normalized_by": self.engine_id,
                "source_name": self.source_name,
                "raw_hash": _stable_hash(
                    dict(raw)
                ),
            }
        )

        identity_payload = {
            "source_name": self.source_name,
            "market_id": market_id,
            "venue": venue,
            "asset": asset,
            "observed_at": observed_at,
            "source_family": source_family,
            "signal_type": signal_type,
            "signal_direction": signal_direction,
            "confidence": confidence,
            "magnitude": magnitude,
            "prior_regime": prior_regime,
            "candidate_regime": candidate_regime,
            "transition_type": transition_type,
            "source_hash": source_hash,
            "sequence": sequence,
        }

        source_id = _to_str(
            raw.get("source_id", "")
        )

        if not source_id:
            source_id = _stable_hash(
                identity_payload
            )

        if not source_hash:
            source_hash = _stable_hash(
                {
                    "source_family": source_family,
                    "signal_type": signal_type,
                    "market_id": market_id,
                    "observed_at": observed_at,
                    "raw_hash": metadata["raw_hash"],
                }
            )

        return MarketRegimeSourceRecord(
            source_id=source_id,
            market_id=market_id,
            venue=venue,
            asset=asset,
            observed_at=observed_at,
            source_family=source_family,
            signal_type=signal_type,
            signal_direction=signal_direction,
            confidence=confidence,
            magnitude=magnitude,
            prior_regime=prior_regime,
            candidate_regime=candidate_regime,
            transition_type=transition_type,
            source_hash=source_hash,
            sequence=sequence,
            metadata=metadata,
        )

    def snapshot(
        self,
        raw_records: Iterable[
            Mapping[str, Any]
        ],
        observed_at: Optional[str] = None,
    ) -> MarketRegimeSourceSnapshot:
        records: List[
            MarketRegimeSourceRecord
        ] = [
            self.normalize_record(raw)
            for raw in list(raw_records or [])
        ]

        ordered_records = tuple(
            sorted(
                records,
                key=lambda record: (
                    record.market_id,
                    record.venue,
                    record.asset,
                    record.source_family,
                    record.signal_type,
                    record.observed_at,
                    record.sequence,
                    record.source_id,
                ),
            )
        )

        status = (
            "ok"
            if ordered_records
            else "empty"
        )

        snapshot_time = (
            observed_at
            or (
                ordered_records[0].observed_at
                if ordered_records
                else _utc_now_iso()
            )
        )

        family_count = len(
            {
                record.source_family
                for record in ordered_records
            }
        )

        market_count = len(
            {
                (
                    record.market_id,
                    record.venue,
                    record.asset,
                )
                for record in ordered_records
            }
        )

        unsigned = MarketRegimeSourceSnapshot(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            source_name=self.source_name,
            observed_at=str(snapshot_time),
            record_count=len(ordered_records),
            family_count=family_count,
            market_count=market_count,
            records=ordered_records,
            read_only=True,
            snapshot_hash="",
        )

        return MarketRegimeSourceSnapshot(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            source_name=unsigned.source_name,
            observed_at=unsigned.observed_at,
            record_count=unsigned.record_count,
            family_count=unsigned.family_count,
            market_count=unsigned.market_count,
            records=unsigned.records,
            read_only=True,
            snapshot_hash=(
                unsigned.expected_snapshot_hash()
            ),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "normalize_record",
                "snapshot",
                "multi_family_signal_normalization",
                "regime_candidate_normalization",
                "transition_normalization",
                "deterministic_order_independent_hashing",
                "source_provenance_hashing",
                "immutable_snapshot_generation",
            ],
        }

    def assert_read_only(self) -> bool:
        forbidden = [
            "buy",
            "sell",
            "trade",
            "execute",
            "order",
            "sign",
            "submit",
            "broadcast",
        ]

        offenders = sorted(
            word
            for word in forbidden
            if word in set(dir(self))
        )

        if offenders:
            raise AssertionError(
                "mutation-like methods are "
                f"forbidden: {offenders}"
            )

        return True


def build_market_regime_source_snapshot(
    raw_records: Iterable[
        Mapping[str, Any]
    ],
    source_name: str = "market_regime.generic",
    observed_at: Optional[str] = None,
) -> MarketRegimeSourceSnapshot:
    return MarketRegimeSourceAdapter(
        source_name=source_name
    ).snapshot(
        raw_records=raw_records,
        observed_at=observed_at,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "MarketRegimeSourceRecord",
    "MarketRegimeSourceSnapshot",
    "MarketRegimeSourceAdapter",
    "build_market_regime_source_snapshot",
]
''',
    encoding="utf-8",
)

TEST.write_text(
r'''
from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_source_adapter import (
    MarketRegimeSourceAdapter,
    build_market_regime_source_snapshot,
)


OBSERVED_AT = "2026-07-09T00:00:00+00:00"

RAW = [
    {
        "market_id": "KXTEST",
        "venue": "kalshi",
        "asset": "binary_event",
        "source_family": "volatility_discovery",
        "signal_type": "volatility_expansion",
        "signal_direction": "expanding",
        "confidence": 0.84,
        "magnitude": 0.72,
        "prior_regime": "stable",
        "candidate_regime": "volatile",
        "transition_type": "stable_to_volatile",
        "source_hash": "volatility-source-hash",
        "sequence": 2,
        "observed_at": OBSERVED_AT,
        "metadata": {
            "realized_volatility": 0.42,
            "baseline_volatility": 0.20,
        },
    },
    {
        "market_id": "KXTEST",
        "venue": "kalshi",
        "asset": "binary_event",
        "source_family": "liquidity_discovery",
        "signal_type": "thin_depth",
        "direction": "low_liquidity",
        "confidence": 0.76,
        "magnitude": 0.61,
        "previous_regime": "stable",
        "current_regime": "illiquid",
        "transition": "stable_to_illiquid",
        "result_hash": "liquidity-source-hash",
        "sequence": 1,
        "timestamp": OBSERVED_AT,
    },
    {
        "market_id": "KXRELATED",
        "venue": "kalshi",
        "asset": "binary_event",
        "family": "correlation_discovery",
        "signal": "correlation_break",
        "relationship": "relationship_decay",
        "score": 0.71,
        "strength": 0.54,
        "prior_regime": "stable",
        "target_regime": "dislocated",
        "transition_type": "stable_to_dislocated",
        "event_hash": "correlation-source-hash",
        "sequence": 3,
        "time": OBSERVED_AT,
    },
]


def test_market_regime_source_adapter_snapshot():
    adapter = MarketRegimeSourceAdapter(
        source_name="market_regime.test"
    )

    assert adapter.assert_read_only() is True

    snapshot1 = adapter.snapshot(
        RAW,
        observed_at=OBSERVED_AT,
    )

    snapshot2 = adapter.snapshot(
        list(reversed(RAW)),
        observed_at=OBSERVED_AT,
    )

    assert snapshot1.schema_version == "RGD-002"
    assert snapshot1.engine_id == (
        "oracle.discovery.market_regime."
        "source_adapter"
    )
    assert snapshot1.status == "ok"
    assert snapshot1.record_count == 3
    assert snapshot1.family_count == 3
    assert snapshot1.market_count == 2
    assert snapshot1.read_only is True
    assert snapshot1.snapshot_hash
    assert (
        snapshot1.snapshot_hash
        == snapshot2.snapshot_hash
    )
    assert (
        snapshot1.verify_snapshot_hash()
        is True
    )

    for record in snapshot1.records:
        assert record.source_id
        assert record.source_hash
        assert record.record_hash
        assert 0.0 <= record.confidence <= 1.0
        assert 0.0 <= record.magnitude <= 1.0
        assert (
            record.metadata["normalized_by"]
            == (
                "oracle.discovery.market_regime."
                "source_adapter"
            )
        )
        assert record.metadata["raw_hash"]


def test_market_regime_source_adapter_normalizes_aliases():
    snapshot = build_market_regime_source_snapshot(
        [
            {
                "symbol": "TEST",
                "exchange": "demo",
                "instrument": "event_contract",
                "discovery_family": (
                    "order_flow_discovery"
                ),
                "event_type": (
                    "order_flow_imbalance"
                ),
                "direction": "bid_pressure",
                "score": 1.40,
                "severity": -0.60,
                "previous_regime": "stable",
                "regime": "trending",
                "transition": (
                    "stable_to_trending"
                ),
                "record_hash": (
                    "order-flow-source-hash"
                ),
                "index": 4,
                "timestamp": OBSERVED_AT,
            }
        ],
        source_name="market_regime.alias",
        observed_at=OBSERVED_AT,
    )

    record = snapshot.records[0]

    assert record.market_id == "TEST"
    assert record.venue == "demo"
    assert record.asset == "event_contract"
    assert (
        record.source_family
        == "order_flow_discovery"
    )
    assert (
        record.signal_type
        == "order_flow_imbalance"
    )
    assert record.signal_direction == "bid_pressure"
    assert record.confidence == 1.0
    assert record.magnitude == 0.60
    assert record.prior_regime == "stable"
    assert record.candidate_regime == "trending"
    assert (
        record.transition_type
        == "stable_to_trending"
    )
    assert record.sequence == 4
    assert (
        record.source_hash
        == "order-flow-source-hash"
    )


def test_market_regime_source_adapter_generates_source_hash():
    snapshot = build_market_regime_source_snapshot(
        [
            {
                "market_id": "KXHASH",
                "venue": "kalshi",
                "asset": "binary_event",
                "source_family": "news_discovery",
                "signal_type": "event_shock",
                "direction": "event_driven",
                "confidence": 0.80,
                "magnitude": 0.70,
                "candidate_regime": "event_driven",
                "observed_at": OBSERVED_AT,
            }
        ],
        source_name="market_regime.hash",
        observed_at=OBSERVED_AT,
    )

    record = snapshot.records[0]

    assert record.source_id
    assert record.source_hash
    assert record.record_hash


def test_market_regime_source_adapter_empty():
    snapshot = build_market_regime_source_snapshot(
        [],
        source_name="market_regime.empty",
        observed_at=OBSERVED_AT,
    )

    assert snapshot.status == "empty"
    assert snapshot.record_count == 0
    assert snapshot.family_count == 0
    assert snapshot.market_count == 0
    assert snapshot.records == tuple()
    assert snapshot.read_only is True
    assert snapshot.snapshot_hash
    assert (
        snapshot.verify_snapshot_hash()
        is True
    )


def test_market_regime_source_adapter_is_replayable():
    snapshot1 = build_market_regime_source_snapshot(
        RAW,
        source_name="market_regime.replay",
        observed_at=OBSERVED_AT,
    )

    snapshot2 = build_market_regime_source_snapshot(
        RAW,
        source_name="market_regime.replay",
        observed_at=OBSERVED_AT,
    )

    assert (
        snapshot1.snapshot_hash
        == snapshot2.snapshot_hash
    )

    assert [
        record.record_hash
        for record in snapshot1.records
    ] == [
        record.record_hash
        for record in snapshot2.records
    ]


def test_market_regime_source_adapter_rejects_invalid_record():
    adapter = MarketRegimeSourceAdapter()

    try:
        adapter.normalize_record(
            ["not", "a", "mapping"]
        )
    except TypeError as exc:
        assert str(exc) == (
            "raw market regime record "
            "must be a mapping"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid record"
        )


if __name__ == "__main__":
    test_market_regime_source_adapter_snapshot()
    test_market_regime_source_adapter_normalizes_aliases()
    test_market_regime_source_adapter_generates_source_hash()
    test_market_regime_source_adapter_empty()
    test_market_regime_source_adapter_is_replayable()
    test_market_regime_source_adapter_rejects_invalid_record()

    snapshot = build_market_regime_source_snapshot(
        [],
        source_name="market_regime.empty",
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-002 "
        "Market Regime Source Adapter"
    )
    print(
        {
            "schema_version": (
                snapshot.schema_version
            ),
            "engine_id": snapshot.engine_id,
            "status": snapshot.status,
            "records": snapshot.record_count,
            "families": snapshot.family_count,
            "markets": snapshot.market_count,
            "read_only": snapshot.read_only,
        }
    )
''',
    encoding="utf-8",
)

existing = (
    INIT.read_text(encoding="utf-8")
    if INIT.exists()
    else ""
)

exports = '''
from .market_regime_source_adapter import (
    MarketRegimeSourceAdapter,
    MarketRegimeSourceRecord,
    MarketRegimeSourceSnapshot,
    build_market_regime_source_snapshot,
)
'''

if "market_regime_source_adapter" not in existing:
    INIT.write_text(
        existing.rstrip()
        + "\n"
        + exports.lstrip(),
        encoding="utf-8",
    )

print("========================================")
print(" RGD-002 INSTALLER")
print(" Market Regime Source Adapter")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] RGD-002 installed")
print()
print("Run:")
print(
    "py "
    "test_rgd_002_market_regime_"
    "source_adapter.py"
)