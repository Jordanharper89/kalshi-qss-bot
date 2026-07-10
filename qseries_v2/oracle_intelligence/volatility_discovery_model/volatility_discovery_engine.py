
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .volatility_source_adapter import (
    VolatilitySourceAdapter,
    VolatilitySourceRecord,
    VolatilitySourceSnapshot,
)


READ_ONLY = True
SCHEMA_VERSION = "VLD-003"
ENGINE_ID = "oracle.discovery.volatility.discovery_engine"


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
class VolatilityOpportunity:
    opportunity_id: str
    market_id: str
    venue: str
    asset: str
    signal_type: str
    regime: str
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
class VolatilityDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    source_snapshot_hash: str
    observed_at: str
    opportunity_count: int
    opportunities: Tuple[VolatilityOpportunity, ...]
    read_only: bool = True
    result_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["opportunities"] = [o.canonical() for o in self.opportunities]
        return _deep_sort(data)


class VolatilityDiscoveryEngine:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        expansion_ratio_threshold: float = 1.50,
        contraction_ratio_threshold: float = 0.70,
        iv_rv_gap_threshold: float = 0.10,
        shock_return_threshold: float = 0.05,
        min_volume: float = 0.0,
    ) -> None:
        self.expansion_ratio_threshold = float(expansion_ratio_threshold)
        self.contraction_ratio_threshold = float(contraction_ratio_threshold)
        self.iv_rv_gap_threshold = float(iv_rv_gap_threshold)
        self.shock_return_threshold = float(shock_return_threshold)
        self.min_volume = float(min_volume)

    def discover_from_raw(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        source_name: str = "volatility.generic",
        observed_at: Optional[str] = None,
    ) -> VolatilityDiscoveryResult:
        snapshot = VolatilitySourceAdapter(source_name=source_name).snapshot(
            raw_records=raw_records,
            observed_at=observed_at,
        )
        return self.discover(snapshot)

    def discover(self, snapshot: VolatilitySourceSnapshot) -> VolatilityDiscoveryResult:
        if not isinstance(snapshot, VolatilitySourceSnapshot):
            raise TypeError("snapshot must be a VolatilitySourceSnapshot")

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
                    o.regime,
                    o.opportunity_id,
                ),
            )
        )

        status = "ok" if opportunities else "empty"

        unsigned = VolatilityDiscoveryResult(
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

        return VolatilityDiscoveryResult(
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

    def _discover_record(self, record: VolatilitySourceRecord) -> Tuple[VolatilityOpportunity, ...]:
        if record.volume < self.min_volume:
            return tuple()

        opportunities: List[VolatilityOpportunity] = []

        if record.volatility_ratio >= self.expansion_ratio_threshold:
            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="volatility_expansion",
                    regime="expanding",
                    magnitude=min(record.volatility_ratio / max(self.expansion_ratio_threshold, 1.0), 2.0) / 2.0,
                    explanation=(
                        f"Detected volatility expansion: realized volatility {record.realized_volatility} "
                        f"versus baseline {record.baseline_volatility}, ratio {round(record.volatility_ratio, 6)}."
                    ),
                )
            )

        if 0 < record.volatility_ratio <= self.contraction_ratio_threshold:
            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="volatility_contraction",
                    regime="contracting",
                    magnitude=1.0 - _clamp(record.volatility_ratio / max(self.contraction_ratio_threshold, 0.000001), 0.0, 1.0),
                    explanation=(
                        f"Detected volatility contraction: realized volatility {record.realized_volatility} "
                        f"below baseline {record.baseline_volatility}, ratio {round(record.volatility_ratio, 6)}."
                    ),
                )
            )

        iv_rv_gap = record.implied_volatility - record.realized_volatility
        if abs(iv_rv_gap) >= self.iv_rv_gap_threshold:
            regime = "implied_rich" if iv_rv_gap > 0 else "realized_rich"
            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="iv_rv_divergence",
                    regime=regime,
                    magnitude=abs(iv_rv_gap),
                    explanation=(
                        f"Detected IV/RV divergence of {round(iv_rv_gap, 6)} "
                        f"from implied {record.implied_volatility} and realized {record.realized_volatility}."
                    ),
                    extra_evidence={"iv_rv_gap": iv_rv_gap},
                )
            )

        if abs(record.price_change) >= self.shock_return_threshold and record.realized_volatility >= record.baseline_volatility:
            regime = "upside_shock" if record.price_change > 0 else "downside_shock"
            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="shock_volatility",
                    regime=regime,
                    magnitude=abs(record.price_change),
                    explanation=(
                        f"Detected {regime} with price change {round(record.price_change, 6)} "
                        f"and realized volatility {record.realized_volatility}."
                    ),
                    extra_evidence={"shock_return": record.price_change},
                )
            )

        return tuple(opportunities)

    def _build_opportunity(
        self,
        record: VolatilitySourceRecord,
        signal_type: str,
        regime: str,
        magnitude: float,
        explanation: str,
        extra_evidence: Optional[Mapping[str, Any]] = None,
    ) -> VolatilityOpportunity:
        normalized_magnitude = _clamp(float(magnitude), 0.0, 1.0)
        ratio_score = _clamp(abs(record.volatility_ratio - 1.0), 0.0, 1.0)
        change_score = _clamp(abs(record.volatility_change), 0.0, 1.0)
        volume_score = _clamp(record.volume / 10000.0, 0.0, 1.0)

        confidence = round(
            _clamp(
                0.45 * normalized_magnitude
                + 0.25 * ratio_score
                + 0.20 * change_score
                + 0.10 * volume_score,
                0.0,
                1.0,
            ),
            6,
        )

        evidence = {
            "realized_volatility": record.realized_volatility,
            "implied_volatility": record.implied_volatility,
            "baseline_volatility": record.baseline_volatility,
            "volatility_change": record.volatility_change,
            "volatility_ratio": record.volatility_ratio,
            "price_change": record.price_change,
            "volume": record.volume,
            "window": record.window,
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
            "regime": regime,
            "magnitude": round(normalized_magnitude, 6),
        }

        return VolatilityOpportunity(
            opportunity_id=_stable_hash(identity),
            market_id=record.market_id,
            venue=record.venue,
            asset=record.asset,
            signal_type=signal_type,
            regime=regime,
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
                "volatility_expansion_detection",
                "volatility_contraction_detection",
                "iv_rv_divergence_detection",
                "shock_volatility_detection",
                "deterministic_order_independent_results",
            ],
            "thresholds": {
                "expansion_ratio_threshold": self.expansion_ratio_threshold,
                "contraction_ratio_threshold": self.contraction_ratio_threshold,
                "iv_rv_gap_threshold": self.iv_rv_gap_threshold,
                "shock_return_threshold": self.shock_return_threshold,
                "min_volume": self.min_volume,
            },
        }

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def discover_volatility_opportunities(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "volatility.generic",
    observed_at: Optional[str] = None,
    expansion_ratio_threshold: float = 1.50,
    contraction_ratio_threshold: float = 0.70,
    iv_rv_gap_threshold: float = 0.10,
    shock_return_threshold: float = 0.05,
    min_volume: float = 0.0,
) -> VolatilityDiscoveryResult:
    engine = VolatilityDiscoveryEngine(
        expansion_ratio_threshold=expansion_ratio_threshold,
        contraction_ratio_threshold=contraction_ratio_threshold,
        iv_rv_gap_threshold=iv_rv_gap_threshold,
        shock_return_threshold=shock_return_threshold,
        min_volume=min_volume,
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
    "VolatilityOpportunity",
    "VolatilityDiscoveryResult",
    "VolatilityDiscoveryEngine",
    "discover_volatility_opportunities",
]
