from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "order_flow_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "order_flow_discovery_engine.py"
TEST = ROOT / "test_ofd_003_order_flow_discovery_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .order_flow_source_adapter import (
    OrderFlowSourceAdapter,
    OrderFlowSourceRecord,
    OrderFlowSourceSnapshot,
)


READ_ONLY = True
SCHEMA_VERSION = "OFD-003"
ENGINE_ID = "oracle.discovery.order_flow.discovery_engine"


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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class OrderFlowOpportunity:
    opportunity_id: str
    market_id: str
    venue: str
    instrument: str
    direction: str
    signal_type: str
    confidence: float
    magnitude: float
    observed_at: str
    explanation: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def opportunity_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class OrderFlowDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    source_snapshot_hash: str
    observed_at: str
    opportunity_count: int
    opportunities: Tuple[OrderFlowOpportunity, ...]
    read_only: bool = True
    result_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["opportunities"] = [o.canonical() for o in self.opportunities]
        return _deep_sort(data)


class OrderFlowDiscoveryEngine:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        min_abs_imbalance: float = 0.25,
        min_volume: float = 0.0,
        min_open_interest: float = 0.0,
    ) -> None:
        self.min_abs_imbalance = float(min_abs_imbalance)
        self.min_volume = float(min_volume)
        self.min_open_interest = float(min_open_interest)

    def discover_from_raw(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        source_name: str = "order_flow.generic",
        observed_at: Optional[str] = None,
    ) -> OrderFlowDiscoveryResult:
        snapshot = OrderFlowSourceAdapter(source_name=source_name).snapshot(
            raw_records,
            observed_at=observed_at,
        )
        return self.discover(snapshot)

    def discover(self, snapshot: OrderFlowSourceSnapshot) -> OrderFlowDiscoveryResult:
        if not isinstance(snapshot, OrderFlowSourceSnapshot):
            raise TypeError("snapshot must be an OrderFlowSourceSnapshot")

        opportunities = tuple(
            sorted(
                [
                    opp
                    for record in snapshot.records
                    for opp in self._discover_record(record)
                ],
                key=lambda o: (
                    o.market_id,
                    o.venue,
                    o.instrument,
                    o.signal_type,
                    o.opportunity_id,
                ),
            )
        )

        status = "ok" if opportunities else "empty"
        unsigned = OrderFlowDiscoveryResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            source_snapshot_hash=snapshot.snapshot_hash,
            observed_at=snapshot.observed_at,
            opportunity_count=len(opportunities),
            opportunities=opportunities,
            read_only=True,
            result_hash="",
        )

        result_hash = _stable_hash(unsigned.canonical())

        return OrderFlowDiscoveryResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            source_snapshot_hash=unsigned.source_snapshot_hash,
            observed_at=unsigned.observed_at,
            opportunity_count=unsigned.opportunity_count,
            opportunities=unsigned.opportunities,
            read_only=True,
            result_hash=result_hash,
        )

    def _discover_record(self, record: OrderFlowSourceRecord) -> Tuple[OrderFlowOpportunity, ...]:
        if abs(record.imbalance) < self.min_abs_imbalance:
            return tuple()

        if record.volume < self.min_volume:
            return tuple()

        if record.open_interest < self.min_open_interest:
            return tuple()

        direction = "bid_pressure" if record.imbalance > 0 else "ask_pressure"
        signal_type = "order_flow_imbalance"
        magnitude = abs(record.imbalance)

        liquidity = max(record.bid_size + record.ask_size, 0.0)
        activity = max(record.volume, 0.0)
        depth_component = _clamp(liquidity / 1000.0, 0.0, 1.0)
        activity_component = _clamp(activity / 5000.0, 0.0, 1.0)
        imbalance_component = _clamp(magnitude, 0.0, 1.0)

        confidence = round(
            _clamp(
                0.50 * imbalance_component
                + 0.25 * depth_component
                + 0.25 * activity_component,
                0.0,
                1.0,
            ),
            6,
        )

        evidence = {
            "bid_size": record.bid_size,
            "ask_size": record.ask_size,
            "bid_price": record.bid_price,
            "ask_price": record.ask_price,
            "last_price": record.last_price,
            "volume": record.volume,
            "open_interest": record.open_interest,
            "imbalance": record.imbalance,
            "record_hash": record.record_hash,
        }

        identity = {
            "market_id": record.market_id,
            "venue": record.venue,
            "instrument": record.instrument,
            "observed_at": record.observed_at,
            "signal_type": signal_type,
            "direction": direction,
            "record_hash": record.record_hash,
        }

        explanation = (
            f"Detected {direction} with imbalance "
            f"{round(record.imbalance, 6)} from bid size {record.bid_size} "
            f"and ask size {record.ask_size}."
        )

        return (
            OrderFlowOpportunity(
                opportunity_id=_stable_hash(identity),
                market_id=record.market_id,
                venue=record.venue,
                instrument=record.instrument,
                direction=direction,
                signal_type=signal_type,
                confidence=confidence,
                magnitude=round(magnitude, 6),
                observed_at=record.observed_at,
                explanation=explanation,
                evidence=evidence,
            ),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "discover",
                "discover_from_raw",
                "order_flow_imbalance_opportunity_detection",
                "deterministic_order_independent_results",
                "replayable_result_hashing",
            ],
            "thresholds": {
                "min_abs_imbalance": self.min_abs_imbalance,
                "min_volume": self.min_volume,
                "min_open_interest": self.min_open_interest,
            },
        }

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        methods = set(dir(self))
        offenders = sorted(word for word in forbidden if word in methods)
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def discover_order_flow_opportunities(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "order_flow.generic",
    observed_at: Optional[str] = None,
    min_abs_imbalance: float = 0.25,
    min_volume: float = 0.0,
    min_open_interest: float = 0.0,
) -> OrderFlowDiscoveryResult:
    engine = OrderFlowDiscoveryEngine(
        min_abs_imbalance=min_abs_imbalance,
        min_volume=min_volume,
        min_open_interest=min_open_interest,
    )
    return engine.discover_from_raw(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OrderFlowOpportunity",
    "OrderFlowDiscoveryResult",
    "OrderFlowDiscoveryEngine",
    "discover_order_flow_opportunities",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_discovery_engine import (
    OrderFlowDiscoveryEngine,
    discover_order_flow_opportunities,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 80,
        "ask_size": 20,
        "bid_price": 0.42,
        "ask_price": 0.45,
        "last_price": 0.43,
        "volume": 2000,
        "open_interest": 7000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-NO",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 25,
        "ask_size": 75,
        "bid_price": 0.55,
        "ask_price": 0.58,
        "last_price": 0.56,
        "volume": 1800,
        "open_interest": 6000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-FLAT",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 51,
        "ask_size": 49,
        "volume": 1000,
        "open_interest": 3000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_order_flow_discovery_engine_detects_opportunities():
    engine = OrderFlowDiscoveryEngine(min_abs_imbalance=0.25)
    assert engine.assert_read_only() is True

    result = engine.discover_from_raw(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "OFD-003"
    assert result.engine_id == "oracle.discovery.order_flow.discovery_engine"
    assert result.status == "ok"
    assert result.read_only is True
    assert result.opportunity_count == 2
    assert result.result_hash

    directions = sorted(o.direction for o in result.opportunities)
    assert directions == ["ask_pressure", "bid_pressure"]

    for opportunity in result.opportunities:
        assert opportunity.opportunity_id
        assert opportunity.opportunity_hash
        assert 0.0 <= opportunity.confidence <= 1.0
        assert opportunity.magnitude >= 0.25
        assert "record_hash" in opportunity.evidence


def test_order_flow_discovery_engine_is_replayable_and_order_independent():
    result1 = discover_order_flow_opportunities(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = discover_order_flow_opportunities(
        list(reversed(RAW)),
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.result_hash == result2.result_hash
    assert [o.opportunity_id for o in result1.opportunities] == [
        o.opportunity_id for o in result2.opportunities
    ]


def test_order_flow_discovery_engine_empty():
    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.result_hash


if __name__ == "__main__":
    test_order_flow_discovery_engine_detects_opportunities()
    test_order_flow_discovery_engine_is_replayable_and_order_independent()
    test_order_flow_discovery_engine_empty()

    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] OFD-003 Order Flow Discovery Engine")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
exports = '''
from .order_flow_discovery_engine import (
    OrderFlowDiscoveryEngine,
    OrderFlowDiscoveryResult,
    OrderFlowOpportunity,
    discover_order_flow_opportunities,
)
'''
if "order_flow_discovery_engine" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" OFD-003 INSTALLER")
print(" Order Flow Discovery Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OFD-003 installed")
print()
print("Run:")
print("py test_ofd_003_order_flow_discovery_engine.py")