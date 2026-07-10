
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
