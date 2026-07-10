from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "liquidity_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "liquidity_discovery_engine.py"
TEST = ROOT / "test_lqd_003_liquidity_discovery_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .liquidity_source_adapter import LiquiditySourceAdapter, LiquiditySourceRecord, LiquiditySourceSnapshot


READ_ONLY = True
SCHEMA_VERSION = "LQD-003"
ENGINE_ID = "oracle.discovery.liquidity.discovery_engine"


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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class LiquidityOpportunity:
    opportunity_id: str
    market_id: str
    venue: str
    asset: str
    signal_type: str
    direction: str
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
class LiquidityDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    source_snapshot_hash: str
    observed_at: str
    opportunity_count: int
    opportunities: Tuple[LiquidityOpportunity, ...]
    read_only: bool = True
    result_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["opportunities"] = [o.canonical() for o in self.opportunities]
        return _deep_sort(data)


class LiquidityDiscoveryEngine:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        min_spread_bps: float = 250.0,
        max_total_depth: float = 1000.0,
        min_depth_imbalance: float = 0.35,
        min_volume_24h: float = 0.0,
    ) -> None:
        self.min_spread_bps = float(min_spread_bps)
        self.max_total_depth = float(max_total_depth)
        self.min_depth_imbalance = float(min_depth_imbalance)
        self.min_volume_24h = float(min_volume_24h)

    def discover_from_raw(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        source_name: str = "liquidity.generic",
        observed_at: Optional[str] = None,
    ) -> LiquidityDiscoveryResult:
        snapshot = LiquiditySourceAdapter(source_name=source_name).snapshot(
            raw_records=raw_records,
            observed_at=observed_at,
        )
        return self.discover(snapshot)

    def discover(self, snapshot: LiquiditySourceSnapshot) -> LiquidityDiscoveryResult:
        if not isinstance(snapshot, LiquiditySourceSnapshot):
            raise TypeError("snapshot must be a LiquiditySourceSnapshot")

        opportunities = tuple(
            sorted(
                [
                    opportunity
                    for record in snapshot.records
                    for opportunity in self._discover_record(record)
                ],
                key=lambda o: (
                    o.market_id,
                    o.venue,
                    o.asset,
                    o.signal_type,
                    o.direction,
                    o.opportunity_id,
                ),
            )
        )

        status = "ok" if opportunities else "empty"

        unsigned = LiquidityDiscoveryResult(
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

        return LiquidityDiscoveryResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            source_snapshot_hash=unsigned.source_snapshot_hash,
            observed_at=unsigned.observed_at,
            opportunity_count=unsigned.opportunity_count,
            opportunities=unsigned.opportunities,
            read_only=True,
            result_hash=_stable_hash(unsigned.canonical()),
        )

    def _discover_record(self, record: LiquiditySourceRecord) -> Tuple[LiquidityOpportunity, ...]:
        if record.volume_24h < self.min_volume_24h:
            return tuple()

        opportunities: List[LiquidityOpportunity] = []

        if record.spread_bps >= self.min_spread_bps:
            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="wide_spread",
                    direction="liquidity_gap",
                    magnitude=record.spread_bps / 10000.0,
                    explanation=(
                        f"Detected wide spread of {round(record.spread_bps, 6)} bps "
                        f"between bid {record.bid_price} and ask {record.ask_price}."
                    ),
                )
            )

        if 0 <= record.total_depth <= self.max_total_depth:
            depth_gap = 1.0 - _clamp(record.total_depth / max(self.max_total_depth, 1.0), 0.0, 1.0)
            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="thin_depth",
                    direction="low_liquidity",
                    magnitude=depth_gap,
                    explanation=(
                        f"Detected thin visible depth of {record.total_depth} "
                        f"against threshold {self.max_total_depth}."
                    ),
                )
            )

        denom = record.bid_depth + record.ask_depth
        imbalance = 0.0 if denom == 0 else (record.bid_depth - record.ask_depth) / denom

        if abs(imbalance) >= self.min_depth_imbalance:
            direction = "bid_depth_dominant" if imbalance > 0 else "ask_depth_dominant"
            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="depth_imbalance",
                    direction=direction,
                    magnitude=abs(imbalance),
                    explanation=(
                        f"Detected {direction} depth imbalance of {round(imbalance, 6)} "
                        f"from bid depth {record.bid_depth} and ask depth {record.ask_depth}."
                    ),
                    extra_evidence={"depth_imbalance": imbalance},
                )
            )

        return tuple(opportunities)

    def _build_opportunity(
        self,
        record: LiquiditySourceRecord,
        signal_type: str,
        direction: str,
        magnitude: float,
        explanation: str,
        extra_evidence: Optional[Mapping[str, Any]] = None,
    ) -> LiquidityOpportunity:
        normalized_magnitude = _clamp(float(magnitude), 0.0, 1.0)
        depth_score = 1.0 - _clamp(record.total_depth / max(self.max_total_depth, 1.0), 0.0, 1.0)
        spread_score = _clamp(record.spread_bps / max(self.min_spread_bps, 1.0), 0.0, 1.0)
        volume_score = _clamp(record.volume_24h / 10000.0, 0.0, 1.0)

        confidence = round(
            _clamp(
                0.45 * normalized_magnitude
                + 0.25 * depth_score
                + 0.20 * spread_score
                + 0.10 * volume_score,
                0.0,
                1.0,
            ),
            6,
        )

        evidence = {
            "bid_price": record.bid_price,
            "ask_price": record.ask_price,
            "bid_depth": record.bid_depth,
            "ask_depth": record.ask_depth,
            "total_depth": record.total_depth,
            "spread": record.spread,
            "spread_bps": record.spread_bps,
            "volume_24h": record.volume_24h,
            "open_interest": record.open_interest,
            "record_hash": record.record_hash,
        }
        evidence.update(dict(extra_evidence or {}))

        identity = {
            "record_hash": record.record_hash,
            "market_id": record.market_id,
            "venue": record.venue,
            "asset": record.asset,
            "observed_at": record.observed_at,
            "signal_type": signal_type,
            "direction": direction,
            "magnitude": round(normalized_magnitude, 6),
        }

        return LiquidityOpportunity(
            opportunity_id=_stable_hash(identity),
            market_id=record.market_id,
            venue=record.venue,
            asset=record.asset,
            signal_type=signal_type,
            direction=direction,
            confidence=confidence,
            magnitude=round(normalized_magnitude, 6),
            observed_at=record.observed_at,
            explanation=explanation,
            evidence=evidence,
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "discover",
                "discover_from_raw",
                "wide_spread_detection",
                "thin_depth_detection",
                "depth_imbalance_detection",
                "deterministic_order_independent_results",
            ],
            "thresholds": {
                "min_spread_bps": self.min_spread_bps,
                "max_total_depth": self.max_total_depth,
                "min_depth_imbalance": self.min_depth_imbalance,
                "min_volume_24h": self.min_volume_24h,
            },
        }

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def discover_liquidity_opportunities(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "liquidity.generic",
    observed_at: Optional[str] = None,
    min_spread_bps: float = 250.0,
    max_total_depth: float = 1000.0,
    min_depth_imbalance: float = 0.35,
    min_volume_24h: float = 0.0,
) -> LiquidityDiscoveryResult:
    engine = LiquidityDiscoveryEngine(
        min_spread_bps=min_spread_bps,
        max_total_depth=max_total_depth,
        min_depth_imbalance=min_depth_imbalance,
        min_volume_24h=min_volume_24h,
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
    "LiquidityOpportunity",
    "LiquidityDiscoveryResult",
    "LiquidityDiscoveryEngine",
    "discover_liquidity_opportunities",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_discovery_engine import (
    LiquidityDiscoveryEngine,
    discover_liquidity_opportunities,
)


RAW = [
    {
        "market_id": "KXTHIN",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.40,
        "ask_price": 0.48,
        "bid_depth": 100,
        "ask_depth": 50,
        "volume_24h": 12000,
        "open_interest": 50000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXDEEP",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.49,
        "ask_price": 0.50,
        "bid_depth": 5000,
        "ask_depth": 5200,
        "volume_24h": 50000,
        "open_interest": 100000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_liquidity_discovery_engine_detects_opportunities():
    engine = LiquidityDiscoveryEngine(
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )
    assert engine.assert_read_only() is True

    result = engine.discover_from_raw(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "LQD-003"
    assert result.engine_id == "oracle.discovery.liquidity.discovery_engine"
    assert result.status == "ok"
    assert result.read_only is True
    assert result.opportunity_count >= 2
    assert result.result_hash

    signal_types = sorted(set(o.signal_type for o in result.opportunities))
    assert "wide_spread" in signal_types
    assert "thin_depth" in signal_types
    assert "depth_imbalance" in signal_types

    for opportunity in result.opportunities:
        assert opportunity.opportunity_id
        assert opportunity.opportunity_hash
        assert 0.0 <= opportunity.confidence <= 1.0
        assert opportunity.magnitude >= 0.0
        assert "record_hash" in opportunity.evidence


def test_liquidity_discovery_engine_is_replayable_and_order_independent():
    result1 = discover_liquidity_opportunities(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )
    result2 = discover_liquidity_opportunities(
        list(reversed(RAW)),
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )

    assert result1.result_hash == result2.result_hash
    assert [o.opportunity_id for o in result1.opportunities] == [
        o.opportunity_id for o in result2.opportunities
    ]


def test_liquidity_discovery_engine_empty():
    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.result_hash


if __name__ == "__main__":
    test_liquidity_discovery_engine_detects_opportunities()
    test_liquidity_discovery_engine_is_replayable_and_order_independent()
    test_liquidity_discovery_engine_empty()

    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] LQD-003 Liquidity Discovery Engine")
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
from .liquidity_discovery_engine import (
    LiquidityDiscoveryEngine,
    LiquidityDiscoveryResult,
    LiquidityOpportunity,
    discover_liquidity_opportunities,
)
'''
if "liquidity_discovery_engine" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" LQD-003 INSTALLER")
print(" Liquidity Discovery Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] LQD-003 installed")
print()
print("Run:")
print("py test_lqd_003_liquidity_discovery_engine.py")