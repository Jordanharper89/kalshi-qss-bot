from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "volatility_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "volatility_discovery_engine.py"
TEST = ROOT / "test_vld_003_volatility_discovery_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
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
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_discovery_engine import (
    VolatilityDiscoveryEngine,
    discover_volatility_opportunities,
)


RAW = [
    {
        "market_id": "KXVOL-EXPAND",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.42,
        "implied_volatility": 0.20,
        "baseline_volatility": 0.20,
        "price_change": 0.08,
        "volume": 12000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXVOL-CONTRACT",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.10,
        "implied_volatility": 0.24,
        "baseline_volatility": 0.20,
        "price_change": 0.01,
        "volume": 9000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_volatility_discovery_engine_detects_opportunities():
    engine = VolatilityDiscoveryEngine(
        expansion_ratio_threshold=1.5,
        contraction_ratio_threshold=0.7,
        iv_rv_gap_threshold=0.10,
        shock_return_threshold=0.05,
    )
    assert engine.assert_read_only() is True

    result = engine.discover_from_raw(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "VLD-003"
    assert result.engine_id == "oracle.discovery.volatility.discovery_engine"
    assert result.status == "ok"
    assert result.read_only is True
    assert result.opportunity_count >= 4
    assert result.result_hash

    signal_types = sorted(set(o.signal_type for o in result.opportunities))
    assert "volatility_expansion" in signal_types
    assert "volatility_contraction" in signal_types
    assert "iv_rv_divergence" in signal_types
    assert "shock_volatility" in signal_types

    for opportunity in result.opportunities:
        assert opportunity.opportunity_id
        assert opportunity.opportunity_hash
        assert 0.0 <= opportunity.confidence <= 1.0
        assert opportunity.magnitude >= 0.0
        assert "record_hash" in opportunity.evidence


def test_volatility_discovery_engine_is_replayable_and_order_independent():
    result1 = discover_volatility_opportunities(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = discover_volatility_opportunities(
        list(reversed(RAW)),
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.result_hash == result2.result_hash
    assert [o.opportunity_id for o in result1.opportunities] == [
        o.opportunity_id for o in result2.opportunities
    ]


def test_volatility_discovery_engine_empty():
    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.result_hash


if __name__ == "__main__":
    test_volatility_discovery_engine_detects_opportunities()
    test_volatility_discovery_engine_is_replayable_and_order_independent()
    test_volatility_discovery_engine_empty()

    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] VLD-003 Volatility Discovery Engine")
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
from .volatility_discovery_engine import (
    VolatilityDiscoveryEngine,
    VolatilityDiscoveryResult,
    VolatilityOpportunity,
    discover_volatility_opportunities,
)
'''
if "volatility_discovery_engine" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" VLD-003 INSTALLER")
print(" Volatility Discovery Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] VLD-003 installed")
print()
print("Run:")
print("py test_vld_003_volatility_discovery_engine.py")