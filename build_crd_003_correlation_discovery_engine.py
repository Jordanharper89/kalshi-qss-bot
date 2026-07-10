from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "correlation_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "correlation_discovery_engine.py"
TEST = ROOT / "test_crd_003_correlation_discovery_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .correlation_source_adapter import (
    CorrelationSourceAdapter,
    CorrelationSourceRecord,
    CorrelationSourceSnapshot,
)


READ_ONLY = True
SCHEMA_VERSION = "CRD-003"
ENGINE_ID = "oracle.discovery.correlation.discovery_engine"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }
    if isinstance(value, list):
        return [_deep_sort(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(item) for item in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(_deep_sort(payload)).encode("utf-8")
    return sha256(encoded).hexdigest()


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class CorrelationOpportunity:
    opportunity_id: str
    primary_market_id: str
    related_market_id: str
    venue: str
    signal_type: str
    relationship: str
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
class CorrelationDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    source_snapshot_hash: str
    observed_at: str
    opportunity_count: int
    opportunities: Tuple[CorrelationOpportunity, ...]
    read_only: bool = True
    result_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["opportunities"] = [
            opportunity.canonical()
            for opportunity in self.opportunities
        ]
        return _deep_sort(data)


class CorrelationDiscoveryEngine:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        strong_correlation_threshold: float = 0.70,
        correlation_break_threshold: float = 0.30,
        return_divergence_threshold: float = 0.04,
        min_sample_size: int = 20,
    ) -> None:
        self.strong_correlation_threshold = float(
            strong_correlation_threshold
        )
        self.correlation_break_threshold = float(
            correlation_break_threshold
        )
        self.return_divergence_threshold = float(
            return_divergence_threshold
        )
        self.min_sample_size = int(min_sample_size)

    def discover_from_raw(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        source_name: str = "correlation.generic",
        observed_at: Optional[str] = None,
    ) -> CorrelationDiscoveryResult:
        snapshot = CorrelationSourceAdapter(
            source_name=source_name
        ).snapshot(
            raw_records=raw_records,
            observed_at=observed_at,
        )
        return self.discover(snapshot)

    def discover(
        self,
        snapshot: CorrelationSourceSnapshot,
    ) -> CorrelationDiscoveryResult:
        if not isinstance(snapshot, CorrelationSourceSnapshot):
            raise TypeError(
                "snapshot must be a CorrelationSourceSnapshot"
            )

        opportunities = tuple(
            sorted(
                [
                    opportunity
                    for record in snapshot.records
                    for opportunity in self._discover_record(record)
                ],
                key=lambda opportunity: (
                    opportunity.primary_market_id,
                    opportunity.related_market_id,
                    opportunity.venue,
                    opportunity.signal_type,
                    opportunity.relationship,
                    opportunity.opportunity_id,
                ),
            )
        )

        status = "ok" if opportunities else "empty"

        unsigned = CorrelationDiscoveryResult(
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

        return CorrelationDiscoveryResult(
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

    def _discover_record(
        self,
        record: CorrelationSourceRecord,
    ) -> Tuple[CorrelationOpportunity, ...]:
        if record.sample_size < self.min_sample_size:
            return tuple()

        opportunities: List[CorrelationOpportunity] = []

        baseline_strength = abs(record.baseline_correlation)
        recent_strength = abs(record.recent_correlation)
        correlation_break = abs(
            record.recent_correlation
            - record.baseline_correlation
        )
        return_divergence = abs(
            record.primary_return
            - record.related_return
        )

        if (
            baseline_strength >= self.strong_correlation_threshold
            and correlation_break >= self.correlation_break_threshold
        ):
            if record.baseline_correlation >= 0:
                relationship = "positive_correlation_breakdown"
            else:
                relationship = "negative_correlation_breakdown"

            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="correlation_break",
                    relationship=relationship,
                    magnitude=correlation_break,
                    explanation=(
                        f"Detected {relationship}: baseline correlation "
                        f"{round(record.baseline_correlation, 6)} shifted to "
                        f"{round(record.recent_correlation, 6)}."
                    ),
                    extra_evidence={
                        "correlation_break": correlation_break,
                    },
                )
            )

        sign_changed = (
            record.baseline_correlation != 0.0
            and record.recent_correlation != 0.0
            and (
                record.baseline_correlation
                * record.recent_correlation
            ) < 0.0
        )

        if sign_changed:
            relationship = (
                "positive_to_negative"
                if record.baseline_correlation > 0
                else "negative_to_positive"
            )

            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="correlation_sign_flip",
                    relationship=relationship,
                    magnitude=min(
                        1.0,
                        abs(record.baseline_correlation)
                        + abs(record.recent_correlation),
                    ),
                    explanation=(
                        f"Detected correlation sign flip from "
                        f"{round(record.baseline_correlation, 6)} to "
                        f"{round(record.recent_correlation, 6)}."
                    ),
                    extra_evidence={
                        "sign_changed": True,
                    },
                )
            )

        if (
            baseline_strength >= self.strong_correlation_threshold
            and return_divergence >= self.return_divergence_threshold
        ):
            if record.primary_return > record.related_return:
                relationship = "primary_outperforming_related"
            else:
                relationship = "related_outperforming_primary"

            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="return_divergence",
                    relationship=relationship,
                    magnitude=return_divergence,
                    explanation=(
                        f"Detected return divergence of "
                        f"{round(return_divergence, 6)} between "
                        f"{record.primary_market_id} and "
                        f"{record.related_market_id}."
                    ),
                    extra_evidence={
                        "return_divergence": return_divergence,
                    },
                )
            )

        if (
            abs(record.correlation) >= self.strong_correlation_threshold
            and record.lag != 0
        ):
            relationship = (
                "primary_leads_related"
                if record.lag > 0
                else "related_leads_primary"
            )

            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="lead_lag_relationship",
                    relationship=relationship,
                    magnitude=min(
                        1.0,
                        abs(record.correlation),
                    ),
                    explanation=(
                        f"Detected {relationship} with lag "
                        f"{record.lag} and correlation "
                        f"{round(record.correlation, 6)}."
                    ),
                    extra_evidence={
                        "lag": record.lag,
                    },
                )
            )

        if (
            baseline_strength >= self.strong_correlation_threshold
            and recent_strength
            <= (
                self.strong_correlation_threshold
                - self.correlation_break_threshold
            )
        ):
            relationship = "relationship_decay"

            opportunities.append(
                self._build_opportunity(
                    record=record,
                    signal_type="correlation_decay",
                    relationship=relationship,
                    magnitude=_clamp(
                        baseline_strength - recent_strength,
                        0.0,
                        1.0,
                    ),
                    explanation=(
                        f"Detected relationship decay: correlation strength "
                        f"fell from {round(baseline_strength, 6)} to "
                        f"{round(recent_strength, 6)}."
                    ),
                    extra_evidence={
                        "baseline_strength": baseline_strength,
                        "recent_strength": recent_strength,
                    },
                )
            )

        return tuple(opportunities)

    def _build_opportunity(
        self,
        record: CorrelationSourceRecord,
        signal_type: str,
        relationship: str,
        magnitude: float,
        explanation: str,
        extra_evidence: Optional[Mapping[str, Any]] = None,
    ) -> CorrelationOpportunity:
        normalized_magnitude = _clamp(
            float(magnitude),
            0.0,
            1.0,
        )
        baseline_score = _clamp(
            abs(record.baseline_correlation),
            0.0,
            1.0,
        )
        recent_change_score = _clamp(
            abs(record.correlation_change),
            0.0,
            1.0,
        )
        sample_score = _clamp(
            record.sample_size / 250.0,
            0.0,
            1.0,
        )

        confidence = round(
            _clamp(
                0.45 * normalized_magnitude
                + 0.25 * baseline_score
                + 0.20 * recent_change_score
                + 0.10 * sample_score,
                0.0,
                1.0,
            ),
            6,
        )

        evidence = {
            "correlation": record.correlation,
            "baseline_correlation": record.baseline_correlation,
            "recent_correlation": record.recent_correlation,
            "correlation_change": record.correlation_change,
            "lag": record.lag,
            "window": record.window,
            "sample_size": record.sample_size,
            "primary_return": record.primary_return,
            "related_return": record.related_return,
            "record_hash": record.record_hash,
        }
        evidence.update(dict(extra_evidence or {}))

        identity = {
            "record_hash": record.record_hash,
            "primary_market_id": record.primary_market_id,
            "related_market_id": record.related_market_id,
            "venue": record.venue,
            "observed_at": record.observed_at,
            "signal_type": signal_type,
            "relationship": relationship,
            "magnitude": round(normalized_magnitude, 6),
        }

        return CorrelationOpportunity(
            opportunity_id=_stable_hash(identity),
            primary_market_id=record.primary_market_id,
            related_market_id=record.related_market_id,
            venue=record.venue,
            signal_type=signal_type,
            relationship=relationship,
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
                "correlation_break_detection",
                "correlation_sign_flip_detection",
                "return_divergence_detection",
                "lead_lag_relationship_detection",
                "correlation_decay_detection",
                "deterministic_order_independent_results",
            ],
            "thresholds": {
                "strong_correlation_threshold": (
                    self.strong_correlation_threshold
                ),
                "correlation_break_threshold": (
                    self.correlation_break_threshold
                ),
                "return_divergence_threshold": (
                    self.return_divergence_threshold
                ),
                "min_sample_size": self.min_sample_size,
            },
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
                f"mutation-like methods are forbidden: {offenders}"
            )
        return True


def discover_correlation_opportunities(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "correlation.generic",
    observed_at: Optional[str] = None,
    strong_correlation_threshold: float = 0.70,
    correlation_break_threshold: float = 0.30,
    return_divergence_threshold: float = 0.04,
    min_sample_size: int = 20,
) -> CorrelationDiscoveryResult:
    engine = CorrelationDiscoveryEngine(
        strong_correlation_threshold=strong_correlation_threshold,
        correlation_break_threshold=correlation_break_threshold,
        return_divergence_threshold=return_divergence_threshold,
        min_sample_size=min_sample_size,
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
    "CorrelationOpportunity",
    "CorrelationDiscoveryResult",
    "CorrelationDiscoveryEngine",
    "discover_correlation_opportunities",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_discovery_engine import (
    CorrelationDiscoveryEngine,
    discover_correlation_opportunities,
)


RAW = [
    {
        "primary_market_id": "KXTEST-A",
        "related_market_id": "KXTEST-B",
        "venue": "kalshi",
        "correlation": 0.82,
        "baseline_correlation": 0.80,
        "recent_correlation": 0.20,
        "lag": 0,
        "window": "30d",
        "sample_size": 120,
        "primary_return": 0.06,
        "related_return": -0.01,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "primary_market_id": "KXTEST-C",
        "related_market_id": "KXTEST-D",
        "venue": "kalshi",
        "correlation": -0.76,
        "baseline_correlation": -0.72,
        "recent_correlation": 0.31,
        "lag": 2,
        "window": "30d",
        "sample_size": 150,
        "primary_return": -0.03,
        "related_return": 0.04,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_correlation_discovery_engine_detects_opportunities():
    engine = CorrelationDiscoveryEngine(
        strong_correlation_threshold=0.70,
        correlation_break_threshold=0.30,
        return_divergence_threshold=0.04,
        min_sample_size=20,
    )

    assert engine.assert_read_only() is True

    result = engine.discover_from_raw(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "CRD-003"
    assert (
        result.engine_id
        == "oracle.discovery.correlation.discovery_engine"
    )
    assert result.status == "ok"
    assert result.read_only is True
    assert result.opportunity_count >= 5
    assert result.result_hash

    signal_types = sorted(
        set(
            opportunity.signal_type
            for opportunity in result.opportunities
        )
    )

    assert "correlation_break" in signal_types
    assert "correlation_sign_flip" in signal_types
    assert "return_divergence" in signal_types
    assert "lead_lag_relationship" in signal_types
    assert "correlation_decay" in signal_types

    for opportunity in result.opportunities:
        assert opportunity.opportunity_id
        assert opportunity.opportunity_hash
        assert 0.0 <= opportunity.confidence <= 1.0
        assert 0.0 <= opportunity.magnitude <= 1.0
        assert opportunity.relationship
        assert "record_hash" in opportunity.evidence


def test_correlation_discovery_engine_is_replayable_and_order_independent():
    result1 = discover_correlation_opportunities(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = discover_correlation_opportunities(
        list(reversed(RAW)),
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.result_hash == result2.result_hash
    assert [
        opportunity.opportunity_id
        for opportunity in result1.opportunities
    ] == [
        opportunity.opportunity_id
        for opportunity in result2.opportunities
    ]


def test_correlation_discovery_engine_respects_sample_size():
    result = discover_correlation_opportunities(
        [
            {
                "primary_market_id": "A",
                "related_market_id": "B",
                "venue": "demo",
                "correlation": 0.90,
                "baseline_correlation": 0.90,
                "recent_correlation": 0.10,
                "lag": 1,
                "window": "7d",
                "sample_size": 5,
                "primary_return": 0.10,
                "related_return": -0.10,
                "observed_at": "2026-07-09T00:00:00+00:00",
            }
        ],
        source_name="correlation.small_sample",
        observed_at="2026-07-09T00:00:00+00:00",
        min_sample_size=20,
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True


def test_correlation_discovery_engine_empty():
    result = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.result_hash


if __name__ == "__main__":
    test_correlation_discovery_engine_detects_opportunities()
    test_correlation_discovery_engine_is_replayable_and_order_independent()
    test_correlation_discovery_engine_respects_sample_size()
    test_correlation_discovery_engine_empty()

    result = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] CRD-003 Correlation Discovery Engine")
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

existing = INIT.read_text(
    encoding="utf-8"
) if INIT.exists() else ""

exports = '''
from .correlation_discovery_engine import (
    CorrelationDiscoveryEngine,
    CorrelationDiscoveryResult,
    CorrelationOpportunity,
    discover_correlation_opportunities,
)
'''

if "correlation_discovery_engine" not in existing:
    INIT.write_text(
        existing.rstrip() + "\n" + exports.lstrip(),
        encoding="utf-8",
    )

print("========================================")
print(" CRD-003 INSTALLER")
print(" Correlation Discovery Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] CRD-003 installed")
print()
print("Run:")
print("py test_crd_003_correlation_discovery_engine.py")