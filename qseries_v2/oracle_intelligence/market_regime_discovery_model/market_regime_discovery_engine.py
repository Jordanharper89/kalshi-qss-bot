
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

from .market_regime_discovery_contract import (
    ALLOWED_REGIMES,
    MarketRegimeDiscoveryResult,
    MarketRegimeEvidence,
    MarketRegimeOpportunity,
    build_market_regime_discovery_result,
    validate_market_regime_discovery_result,
)


READ_ONLY = True
SCHEMA_VERSION = "RGD-003"

ENGINE_ID = (
    "oracle.discovery.market_regime."
    "discovery_engine"
)

DEFAULT_CONFIDENCE_THRESHOLD = 0.55
DEFAULT_MAGNITUDE_THRESHOLD = 0.15

SUPPORTED_SIGNAL_TYPES = frozenset(
    {
        "trend_strength",
        "momentum",
        "mean_reversion",
        "volatility",
        "liquidity",
        "dislocation",
        "event_pressure",
        "risk_appetite",
        "correlation_breakdown",
        "dispersion",
        "market_stability",
    }
)


@dataclass(frozen=True)
class MarketRegimeEngineConfig:
    confidence_threshold: float = (
        DEFAULT_CONFIDENCE_THRESHOLD
    )
    magnitude_threshold: float = (
        DEFAULT_MAGNITUDE_THRESHOLD
    )
    minimum_signal_count: int = 1
    require_transition: bool = True

    def __post_init__(self) -> None:
        if not (
            0.0
            <= float(
                self.confidence_threshold
            )
            <= 1.0
        ):
            raise ValueError(
                "confidence_threshold must be "
                "between 0.0 and 1.0"
            )

        if not (
            0.0
            <= float(
                self.magnitude_threshold
            )
            <= 1.0
        ):
            raise ValueError(
                "magnitude_threshold must be "
                "between 0.0 and 1.0"
            )

        if int(self.minimum_signal_count) < 1:
            raise ValueError(
                "minimum_signal_count must be "
                "at least 1"
            )


@dataclass(frozen=True)
class NormalizedRegimeSignal:
    signal_id: str
    market_id: str
    venue: str
    asset: str
    source_family: str
    signal_type: str
    value: float
    reliability: float
    observed_at: str
    source_hash: str
    prior_regime: str = "unknown"
    details: Tuple[
        Tuple[str, Any],
        ...,
    ] = tuple()

    def __post_init__(self) -> None:
        required_values = {
            "signal_id": self.signal_id,
            "market_id": self.market_id,
            "venue": self.venue,
            "asset": self.asset,
            "source_family": (
                self.source_family
            ),
            "signal_type": self.signal_type,
            "observed_at": self.observed_at,
            "source_hash": self.source_hash,
        }

        for field_name, value in (
            required_values.items()
        ):
            if not str(value).strip():
                raise ValueError(
                    f"{field_name} must not "
                    "be empty"
                )

        if self.signal_type not in (
            SUPPORTED_SIGNAL_TYPES
        ):
            raise ValueError(
                "signal_type is not supported"
            )

        if not -1.0 <= float(self.value) <= 1.0:
            raise ValueError(
                "value must be between "
                "-1.0 and 1.0"
            )

        if not (
            0.0
            <= float(self.reliability)
            <= 1.0
        ):
            raise ValueError(
                "reliability must be between "
                "0.0 and 1.0"
            )

        if self.prior_regime not in (
            ALLOWED_REGIMES
        ):
            raise ValueError(
                "prior_regime is not supported"
            )


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    return max(
        minimum,
        min(
            maximum,
            float(value),
        ),
    )


def _stable_value(
    value: Any,
) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _stable_value(value[key])
            for key in sorted(
                value.keys(),
                key=str,
            )
        }

    if isinstance(value, tuple):
        return tuple(
            _stable_value(item)
            for item in value
        )

    if isinstance(value, list):
        return [
            _stable_value(item)
            for item in value
        ]

    if isinstance(value, set):
        return tuple(
            sorted(
                (
                    _stable_value(item)
                    for item in value
                ),
                key=repr,
            )
        )

    return value


def _stable_hash(
    value: Any,
) -> str:
    return sha256(
        repr(
            _stable_value(value)
        ).encode("utf-8")
    ).hexdigest()


def _read_value(
    record: Any,
    key: str,
    default: Any = None,
) -> Any:
    if isinstance(record, Mapping):
        return record.get(
            key,
            default,
        )

    return getattr(
        record,
        key,
        default,
    )


def _first_value(
    record: Any,
    keys: Sequence[str],
    default: Any = None,
) -> Any:
    for key in keys:
        value = _read_value(
            record,
            key,
            None,
        )

        if value is not None:
            return value

    return default


def _normalize_details(
    details: Any,
) -> Tuple[
    Tuple[str, Any],
    ...,
]:
    if not isinstance(details, Mapping):
        return tuple()

    return tuple(
        (
            str(key),
            _stable_value(details[key]),
        )
        for key in sorted(
            details.keys(),
            key=str,
        )
    )


def _details_dict(
    details: Tuple[
        Tuple[str, Any],
        ...,
    ],
) -> Dict[str, Any]:
    return {
        str(key): _stable_value(value)
        for key, value in details
    }


def _normalize_signal_type(
    value: Any,
) -> str:
    normalized = (
        str(value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    aliases = {
        "trend": "trend_strength",
        "trending": "trend_strength",
        "trend_signal": "trend_strength",
        "momentum_signal": "momentum",
        "reversion": "mean_reversion",
        "mean_reverting": "mean_reversion",
        "volatility_expansion": "volatility",
        "realized_volatility": "volatility",
        "vol": "volatility",
        "liquidity_stress": "liquidity",
        "illiquidity": "liquidity",
        "market_dislocation": "dislocation",
        "event": "event_pressure",
        "event_driven": "event_pressure",
        "risk_on_off": "risk_appetite",
        "risk_sentiment": "risk_appetite",
        "correlation": "correlation_breakdown",
        "correlation_shift": (
            "correlation_breakdown"
        ),
        "cross_asset_dispersion": "dispersion",
        "stability": "market_stability",
        "stable": "market_stability",
    }

    return aliases.get(
        normalized,
        normalized,
    )


def _normalize_signed_value(
    value: Any,
) -> float:
    normalized = float(value)

    if normalized > 1.0:
        normalized = normalized / 100.0

    return _clamp(
        normalized,
        -1.0,
        1.0,
    )


def _normalize_probability(
    value: Any,
    default: float,
) -> float:
    if value is None:
        return float(default)

    normalized = float(value)

    if normalized > 1.0:
        normalized = normalized / 100.0

    return _clamp(normalized)


def normalize_regime_signal(
    record: Any,
) -> NormalizedRegimeSignal:
    market_id = str(
        _first_value(
            record,
            (
                "market_id",
                "market",
                "ticker",
                "symbol",
                "instrument_id",
            ),
            "",
        )
    ).strip()

    venue = str(
        _first_value(
            record,
            (
                "venue",
                "exchange",
                "platform",
                "source_venue",
            ),
            "unknown",
        )
    ).strip()

    asset = str(
        _first_value(
            record,
            (
                "asset",
                "asset_type",
                "instrument_type",
                "category",
            ),
            "unknown",
        )
    ).strip()

    source_family = str(
        _first_value(
            record,
            (
                "source_family",
                "family",
                "discovery_family",
                "source",
            ),
            "unknown",
        )
    ).strip()

    signal_type = _normalize_signal_type(
        _first_value(
            record,
            (
                "signal_type",
                "metric",
                "feature",
                "indicator",
                "type",
            ),
            "",
        )
    )

    raw_value = _first_value(
        record,
        (
            "value",
            "signal_value",
            "score",
            "normalized_value",
            "strength",
        ),
        0.0,
    )

    reliability = _normalize_probability(
        _first_value(
            record,
            (
                "reliability",
                "confidence",
                "quality",
                "weight",
            ),
            1.0,
        ),
        1.0,
    )

    observed_at = str(
        _first_value(
            record,
            (
                "observed_at",
                "timestamp",
                "as_of",
                "captured_at",
            ),
            "",
        )
    ).strip()

    prior_regime = str(
        _first_value(
            record,
            (
                "prior_regime",
                "previous_regime",
                "baseline_regime",
            ),
            "unknown",
        )
    ).strip().lower()

    details = _normalize_details(
        _first_value(
            record,
            (
                "details",
                "metadata",
                "payload",
                "attributes",
            ),
            {},
        )
    )

    source_hash = str(
        _first_value(
            record,
            (
                "source_hash",
                "record_hash",
                "payload_hash",
                "hash",
            ),
            "",
        )
    ).strip()

    signal_id = str(
        _first_value(
            record,
            (
                "signal_id",
                "record_id",
                "source_id",
                "id",
            ),
            "",
        )
    ).strip()

    value = _normalize_signed_value(
        raw_value
    )

    if not source_hash:
        source_hash = _stable_hash(
            {
                "market_id": market_id,
                "venue": venue,
                "asset": asset,
                "source_family": source_family,
                "signal_type": signal_type,
                "value": value,
                "reliability": reliability,
                "observed_at": observed_at,
                "prior_regime": prior_regime,
                "details": details,
            }
        )

    if not signal_id:
        signal_id = (
            "regime-signal-"
            + source_hash[:20]
        )

    return NormalizedRegimeSignal(
        signal_id=signal_id,
        market_id=market_id,
        venue=venue,
        asset=asset,
        source_family=source_family,
        signal_type=signal_type,
        value=value,
        reliability=reliability,
        observed_at=observed_at,
        source_hash=source_hash,
        prior_regime=prior_regime,
        details=details,
    )


def normalize_regime_signals(
    records: Iterable[Any],
) -> Tuple[
    NormalizedRegimeSignal,
    ...,
]:
    normalized = tuple(
        normalize_regime_signal(record)
        for record in tuple(records or tuple())
    )

    signal_ids = [
        signal.signal_id
        for signal in normalized
    ]

    if len(signal_ids) != len(
        set(signal_ids)
    ):
        raise ValueError(
            "signal identifiers must be unique"
        )

    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.market_id,
                item.venue,
                item.asset,
                item.signal_type,
                item.source_family,
                item.signal_id,
            ),
        )
    )


def _extract_records(
    source_result: Any,
) -> Tuple[Any, ...]:
    if source_result is None:
        return tuple()

    if isinstance(
        source_result,
        (list, tuple),
    ):
        return tuple(source_result)

    records = _first_value(
        source_result,
        (
            "records",
            "signals",
            "items",
            "observations",
            "source_records",
        ),
        tuple(),
    )

    if records is None:
        return tuple()

    return tuple(records)


def _resolve_observed_at(
    source_result: Any,
    signals: Tuple[
        NormalizedRegimeSignal,
        ...,
    ],
    observed_at: str | None,
) -> str:
    if observed_at is not None:
        resolved = str(observed_at).strip()

        if not resolved:
            raise ValueError(
                "observed_at must not be empty"
            )

        return resolved

    source_observed_at = _first_value(
        source_result,
        (
            "observed_at",
            "generated_at",
            "as_of",
            "captured_at",
        ),
        None,
    )

    if source_observed_at is not None:
        resolved = str(
            source_observed_at
        ).strip()

        if resolved:
            return resolved

    signal_times = sorted(
        {
            signal.observed_at
            for signal in signals
            if signal.observed_at
        }
    )

    if signal_times:
        return signal_times[-1]

    return "1970-01-01T00:00:00+00:00"


def _weighted_average(
    signals: Sequence[
        NormalizedRegimeSignal
    ],
) -> float:
    if not signals:
        return 0.0

    total_weight = sum(
        signal.reliability
        for signal in signals
    )

    if total_weight <= 0.0:
        return 0.0

    return sum(
        (
            signal.value
            * signal.reliability
        )
        for signal in signals
    ) / total_weight


def _weighted_absolute_average(
    signals: Sequence[
        NormalizedRegimeSignal
    ],
) -> float:
    if not signals:
        return 0.0

    total_weight = sum(
        signal.reliability
        for signal in signals
    )

    if total_weight <= 0.0:
        return 0.0

    return sum(
        (
            abs(signal.value)
            * signal.reliability
        )
        for signal in signals
    ) / total_weight


def _signals_by_type(
    signals: Sequence[
        NormalizedRegimeSignal
    ],
) -> Dict[
    str,
    Tuple[
        NormalizedRegimeSignal,
        ...,
    ],
]:
    grouped: Dict[
        str,
        list[
            NormalizedRegimeSignal
        ],
    ] = {}

    for signal in signals:
        grouped.setdefault(
            signal.signal_type,
            [],
        ).append(signal)

    return {
        signal_type: tuple(
            sorted(
                items,
                key=lambda item: (
                    item.source_family,
                    item.signal_id,
                ),
            )
        )
        for signal_type, items
        in sorted(grouped.items())
    }


def _score_regimes(
    signals: Sequence[
        NormalizedRegimeSignal
    ],
) -> Dict[str, float]:
    grouped = _signals_by_type(signals)

    trend = _weighted_absolute_average(
        grouped.get(
            "trend_strength",
            tuple(),
        )
    )

    momentum = _weighted_average(
        grouped.get(
            "momentum",
            tuple(),
        )
    )

    mean_reversion = (
        _weighted_absolute_average(
            grouped.get(
                "mean_reversion",
                tuple(),
            )
        )
    )

    volatility = (
        _weighted_absolute_average(
            grouped.get(
                "volatility",
                tuple(),
            )
        )
    )

    liquidity = _weighted_average(
        grouped.get(
            "liquidity",
            tuple(),
        )
    )

    dislocation = (
        _weighted_absolute_average(
            grouped.get(
                "dislocation",
                tuple(),
            )
        )
    )

    event_pressure = (
        _weighted_absolute_average(
            grouped.get(
                "event_pressure",
                tuple(),
            )
        )
    )

    risk_appetite = _weighted_average(
        grouped.get(
            "risk_appetite",
            tuple(),
        )
    )

    correlation_breakdown = (
        _weighted_absolute_average(
            grouped.get(
                "correlation_breakdown",
                tuple(),
            )
        )
    )

    dispersion = (
        _weighted_absolute_average(
            grouped.get(
                "dispersion",
                tuple(),
            )
        )
    )

    stability = _weighted_average(
        grouped.get(
            "market_stability",
            tuple(),
        )
    )

    instability = _clamp(
        max(
            volatility,
            dislocation,
            correlation_breakdown,
            dispersion,
            max(0.0, -liquidity),
        )
    )

    transition_score = _clamp(
        (
            volatility
            + dislocation
            + correlation_breakdown
            + dispersion
            + abs(momentum)
        )
        / 5.0
    )

    scores = {
        "stable": _clamp(
            (
                max(0.0, stability)
                + max(0.0, liquidity)
                + (1.0 - instability)
            )
            / 3.0
        ),
        "trending": _clamp(
            (
                trend
                + abs(momentum)
                + max(
                    0.0,
                    1.0 - mean_reversion,
                )
            )
            / 3.0
        ),
        "mean_reverting": _clamp(
            (
                mean_reversion
                + max(
                    0.0,
                    1.0 - trend,
                )
                + max(
                    0.0,
                    1.0 - abs(momentum),
                )
            )
            / 3.0
        ),
        "volatile": _clamp(
            (
                volatility
                + dispersion
                + correlation_breakdown
            )
            / 3.0
        ),
        "illiquid": _clamp(
            max(
                0.0,
                -liquidity,
            )
        ),
        "dislocated": _clamp(
            (
                dislocation
                + correlation_breakdown
                + dispersion
            )
            / 3.0
        ),
        "event_driven": _clamp(
            (
                event_pressure
                + volatility
                + abs(momentum)
            )
            / 3.0
        ),
        "risk_on": _clamp(
            (
                max(
                    0.0,
                    risk_appetite,
                )
                + max(
                    0.0,
                    momentum,
                )
                + max(
                    0.0,
                    liquidity,
                )
            )
            / 3.0
        ),
        "risk_off": _clamp(
            (
                max(
                    0.0,
                    -risk_appetite,
                )
                + max(
                    0.0,
                    -momentum,
                )
                + volatility
            )
            / 3.0
        ),
        "transition": transition_score,
    }

    return {
        regime: round(
            score,
            12,
        )
        for regime, score
        in sorted(scores.items())
    }


def _determine_regime(
    scores: Mapping[str, float],
) -> Tuple[str, float, float]:
    ordered = sorted(
        scores.items(),
        key=lambda item: (
            -float(item[1]),
            str(item[0]),
        ),
    )

    if not ordered:
        return (
            "unknown",
            0.0,
            0.0,
        )

    current_regime = ordered[0][0]
    top_score = float(ordered[0][1])

    second_score = (
        float(ordered[1][1])
        if len(ordered) > 1
        else 0.0
    )

    margin = _clamp(
        top_score - second_score
    )

    return (
        current_regime,
        top_score,
        margin,
    )


def _resolve_prior_regime(
    signals: Sequence[
        NormalizedRegimeSignal
    ],
) -> str:
    weighted: Dict[str, float] = {}

    for signal in signals:
        regime = signal.prior_regime

        if regime == "unknown":
            continue

        weighted[regime] = (
            weighted.get(regime, 0.0)
            + signal.reliability
        )

    if not weighted:
        return "unknown"

    return sorted(
        weighted.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )[0][0]


def _build_confidence(
    signals: Sequence[
        NormalizedRegimeSignal
    ],
    top_score: float,
    margin: float,
) -> float:
    if not signals:
        return 0.0

    mean_reliability = sum(
        signal.reliability
        for signal in signals
    ) / len(signals)

    source_families = {
        signal.source_family
        for signal in signals
    }

    diversity = _clamp(
        len(source_families) / 4.0
    )

    confidence = (
        0.45 * top_score
        + 0.30 * mean_reliability
        + 0.15 * margin
        + 0.10 * diversity
    )

    return round(
        _clamp(confidence),
        12,
    )


def _build_magnitude(
    scores: Mapping[str, float],
    current_regime: str,
    margin: float,
) -> float:
    current_score = float(
        scores.get(
            current_regime,
            0.0,
        )
    )

    magnitude = (
        0.75 * current_score
        + 0.25 * margin
    )

    return round(
        _clamp(magnitude),
        12,
    )


def _build_transition_type(
    prior_regime: str,
    current_regime: str,
) -> str:
    if prior_regime == current_regime:
        return (
            f"{current_regime}_continuation"
        )

    if prior_regime == "unknown":
        return (
            f"{current_regime}_emergence"
        )

    return (
        f"{prior_regime}_to_"
        f"{current_regime}"
    )


def _build_evidence(
    signals: Sequence[
        NormalizedRegimeSignal
    ],
) -> Tuple[
    MarketRegimeEvidence,
    ...,
]:
    evidence = []

    total_weight = sum(
        (
            abs(signal.value)
            * signal.reliability
        )
        for signal in signals
    )

    for signal in signals:
        raw_contribution = (
            abs(signal.value)
            * signal.reliability
        )

        contribution = (
            raw_contribution / total_weight
            if total_weight > 0.0
            else 0.0
        )

        details = _details_dict(
            signal.details
        )

        details.update(
            {
                "signal_id": signal.signal_id,
                "signal_value": signal.value,
                "reliability": (
                    signal.reliability
                ),
                "observed_at": (
                    signal.observed_at
                ),
                "market_id": signal.market_id,
                "venue": signal.venue,
                "asset": signal.asset,
            }
        )

        evidence.append(
            MarketRegimeEvidence(
                evidence_id=(
                    "regime-evidence-"
                    + signal.signal_id
                ),
                source_family=(
                    signal.source_family
                ),
                signal_type=(
                    signal.signal_type
                ),
                contribution=round(
                    _clamp(contribution),
                    12,
                ),
                source_hash=(
                    signal.source_hash
                ),
                details=details,
            )
        )

    return tuple(
        sorted(
            evidence,
            key=lambda item: (
                item.source_family,
                item.signal_type,
                item.evidence_id,
            ),
        )
    )


def _build_explanation(
    market_id: str,
    prior_regime: str,
    current_regime: str,
    confidence: float,
    magnitude: float,
    scores: Mapping[str, float],
    signals: Sequence[
        NormalizedRegimeSignal
    ],
) -> str:
    ranked_scores = sorted(
        scores.items(),
        key=lambda item: (
            -float(item[1]),
            item[0],
        ),
    )[:3]

    score_text = ", ".join(
        (
            f"{regime}="
            f"{float(score):.4f}"
        )
        for regime, score
        in ranked_scores
    )

    families = ", ".join(
        sorted(
            {
                signal.source_family
                for signal in signals
            }
        )
    )

    return (
        f"Market {market_id} was classified "
        f"as {current_regime} from prior "
        f"regime {prior_regime}. "
        f"Confidence={confidence:.4f}; "
        f"magnitude={magnitude:.4f}; "
        f"leading regime scores: "
        f"{score_text}. "
        f"Evidence families: {families}."
    )


def _group_signals(
    signals: Sequence[
        NormalizedRegimeSignal
    ],
) -> Tuple[
    Tuple[
        Tuple[str, str, str],
        Tuple[
            NormalizedRegimeSignal,
            ...,
        ],
    ],
    ...,
]:
    grouped: Dict[
        Tuple[str, str, str],
        list[
            NormalizedRegimeSignal
        ],
    ] = {}

    for signal in signals:
        key = (
            signal.market_id,
            signal.venue,
            signal.asset,
        )

        grouped.setdefault(
            key,
            [],
        ).append(signal)

    return tuple(
        (
            key,
            tuple(
                sorted(
                    items,
                    key=lambda item: (
                        item.signal_type,
                        item.source_family,
                        item.signal_id,
                    ),
                )
            ),
        )
        for key, items
        in sorted(grouped.items())
    )


def discover_market_regimes(
    source_result: Any,
    observed_at: str | None = None,
    config: MarketRegimeEngineConfig | None = None,
) -> MarketRegimeDiscoveryResult:
    resolved_config = (
        config
        if config is not None
        else MarketRegimeEngineConfig()
    )

    source_records = _extract_records(
        source_result
    )

    signals = normalize_regime_signals(
        source_records
    )

    resolved_observed_at = (
        _resolve_observed_at(
            source_result=source_result,
            signals=signals,
            observed_at=observed_at,
        )
    )

    opportunities = []
    rejected_market_count = 0

    for key, market_signals in (
        _group_signals(signals)
    ):
        market_id, venue, asset = key

        if (
            len(market_signals)
            < resolved_config.minimum_signal_count
        ):
            rejected_market_count += 1
            continue

        scores = _score_regimes(
            market_signals
        )

        (
            current_regime,
            top_score,
            margin,
        ) = _determine_regime(scores)

        prior_regime = _resolve_prior_regime(
            market_signals
        )

        confidence = _build_confidence(
            signals=market_signals,
            top_score=top_score,
            margin=margin,
        )

        magnitude = _build_magnitude(
            scores=scores,
            current_regime=current_regime,
            margin=margin,
        )

        transition_type = (
            _build_transition_type(
                prior_regime=prior_regime,
                current_regime=(
                    current_regime
                ),
            )
        )

        is_transition = (
            prior_regime == "unknown"
            or prior_regime
            != current_regime
        )

        if (
            confidence
            < resolved_config.confidence_threshold
        ):
            rejected_market_count += 1
            continue

        if (
            magnitude
            < resolved_config.magnitude_threshold
        ):
            rejected_market_count += 1
            continue

        if (
            resolved_config.require_transition
            and not is_transition
        ):
            rejected_market_count += 1
            continue

        evidence = _build_evidence(
            market_signals
        )

        opportunity_seed = {
            "market_id": market_id,
            "venue": venue,
            "asset": asset,
            "prior_regime": prior_regime,
            "current_regime": (
                current_regime
            ),
            "transition_type": (
                transition_type
            ),
            "confidence": confidence,
            "magnitude": magnitude,
            "observed_at": (
                resolved_observed_at
            ),
            "signal_ids": tuple(
                signal.signal_id
                for signal in market_signals
            ),
        }

        opportunity_id = (
            "regime-opportunity-"
            + _stable_hash(
                opportunity_seed
            )[:24]
        )

        opportunities.append(
            MarketRegimeOpportunity(
                opportunity_id=(
                    opportunity_id
                ),
                market_id=market_id,
                venue=venue,
                asset=asset,
                prior_regime=prior_regime,
                current_regime=(
                    current_regime
                ),
                transition_type=(
                    transition_type
                ),
                confidence=confidence,
                magnitude=magnitude,
                observed_at=(
                    resolved_observed_at
                ),
                explanation=(
                    _build_explanation(
                        market_id=market_id,
                        prior_regime=(
                            prior_regime
                        ),
                        current_regime=(
                            current_regime
                        ),
                        confidence=confidence,
                        magnitude=magnitude,
                        scores=scores,
                        signals=market_signals,
                    )
                ),
                evidence=evidence,
            )
        )

    source_families = sorted(
        {
            signal.source_family
            for signal in signals
        }
    )

    markets = sorted(
        {
            (
                signal.market_id,
                signal.venue,
                signal.asset,
            )
            for signal in signals
        }
    )

    metadata = {
        "engine_schema_version": (
            SCHEMA_VERSION
        ),
        "source_schema_version": str(
            _first_value(
                source_result,
                ("schema_version",),
                "unknown",
            )
        ),
        "source_engine_id": str(
            _first_value(
                source_result,
                ("engine_id",),
                "unknown",
            )
        ),
        "source_status": str(
            _first_value(
                source_result,
                ("status",),
                (
                    "ok"
                    if signals
                    else "empty"
                ),
            )
        ),
        "source_record_count": (
            len(source_records)
        ),
        "normalized_signal_count": (
            len(signals)
        ),
        "market_count": len(markets),
        "source_family_count": (
            len(source_families)
        ),
        "source_families": (
            source_families
        ),
        "accepted_market_count": (
            len(opportunities)
        ),
        "rejected_market_count": (
            rejected_market_count
        ),
        "confidence_threshold": (
            resolved_config
            .confidence_threshold
        ),
        "magnitude_threshold": (
            resolved_config
            .magnitude_threshold
        ),
        "minimum_signal_count": (
            resolved_config
            .minimum_signal_count
        ),
        "require_transition": (
            resolved_config
            .require_transition
        ),
        "deterministic": True,
        "replayable": True,
        "read_only": True,
    }

    result = (
        build_market_regime_discovery_result(
            engine_id=ENGINE_ID,
            observed_at=resolved_observed_at,
            opportunities=tuple(
                opportunities
            ),
            metadata=metadata,
        )
    )

    validation = (
        validate_market_regime_discovery_result(
            result
        )
    )

    if validation["accepted"] is not True:
        raise AssertionError(
            "market regime discovery engine "
            "produced an invalid result"
        )

    return result


def run_market_regime_discovery(
    source_result: Any,
    observed_at: str | None = None,
    config: MarketRegimeEngineConfig | None = None,
) -> MarketRegimeDiscoveryResult:
    return discover_market_regimes(
        source_result=source_result,
        observed_at=observed_at,
        config=config,
    )


def assert_market_regime_engine_read_only(
    result: MarketRegimeDiscoveryResult,
) -> bool:
    if not isinstance(
        result,
        MarketRegimeDiscoveryResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimeDiscoveryResult"
        )

    if READ_ONLY is not True:
        raise AssertionError(
            "market regime discovery engine "
            "must be read-only"
        )

    if result.read_only is not True:
        raise AssertionError(
            "market regime discovery result "
            "must be read-only"
        )

    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "DEFAULT_MAGNITUDE_THRESHOLD",
    "SUPPORTED_SIGNAL_TYPES",
    "MarketRegimeEngineConfig",
    "NormalizedRegimeSignal",
    "normalize_regime_signal",
    "normalize_regime_signals",
    "discover_market_regimes",
    "run_market_regime_discovery",
    "assert_market_regime_engine_read_only",
]
