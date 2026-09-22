"""
OIA-006
Oracle Opportunity Candidate Generator

Read-only deterministic research candidate generation over OIA-004 canonical
features admitted by OIA-005 market usefulness scoring. Candidates are research
hypotheses only. They are not signals, alerts, recommendations, or execution input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence

from .oracle_market_feature_extraction_engine import (
    OracleCanonicalMarketFeatureExtractionEngine,
    OracleCanonicalMarketFeatureRecord,
    OracleCanonicalMarketFeatureReport,
)
from .oracle_market_usefulness_scoring_engine import (
    USEFUL,
    OracleMarketUsefulnessReport,
    OracleMarketUsefulnessScoringEngine,
)

SCHEMA_VERSION = "OIA-006"
ENGINE_ID = "OIA-006"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
OPPORTUNITY_CANDIDATES_ALLOWED = True
RAW_CORPUS_MUTATION_ALLOWED = False

CANDIDATE = "candidate"
EXCLUDED = "excluded"
MOMENTUM_CONTINUATION = "momentum_continuation"
VOLATILITY_REVERSION_WATCH = "volatility_reversion_watch"
NO_CANDIDATE = "none"
YES_DIRECTION = "yes"
NO_DIRECTION = "no"
NEUTRAL_DIRECTION = "neutral"


class OpportunityCandidateError(RuntimeError):
    pass


class OpportunityCandidateConfigurationError(OpportunityCandidateError):
    pass


class OpportunityCandidateInvariantError(OpportunityCandidateError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OpportunityCandidateInvariantError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return Decimal(default)
    return result if result.is_finite() else Decimal(default)


def _clamp(value: Decimal, low: Decimal = Decimal("0"), high: Decimal = Decimal("1")) -> Decimal:
    return max(low, min(high, value))


def _score_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


@dataclass(frozen=True)
class OracleOpportunityCandidateRecord:
    market_id: str
    disposition: str
    candidate_family: str
    research_direction: str
    candidate_score: str
    usefulness_score: str
    latest_price_dollars: Optional[str]
    directional_change_dollars: Optional[str]
    directional_change_ratio: Optional[str]
    normalized_volatility_ratio: Optional[str]
    movement_efficiency_ratio: Optional[str]
    spread_to_price_ratio: Optional[str]
    observation_count: int
    reason_codes: tuple[str, ...]
    feature_hash: str
    usefulness_hash: str
    candidate_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleOpportunityCandidateReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    feature_report_hash: str
    usefulness_report_hash: str
    reviewed_market_count: int
    candidate_market_count: int
    excluded_market_count: int
    momentum_candidate_count: int
    reversion_watch_count: int
    average_candidate_score: str
    markets: tuple[OracleOpportunityCandidateRecord, ...]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    opportunity_candidates_allowed: bool
    raw_corpus_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleOpportunityCandidateGenerator:
    read_only = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    opportunity_candidates_allowed = True
    raw_corpus_mutation_allowed = False

    def __init__(
        self,
        *,
        connection_factory: Callable[[], Any],
        stale_after_seconds: int = 300,
        minimum_observations: int = 3,
        market_limit: int = 1000,
        history_limit_per_market: int = 1000,
        useful_threshold: Decimal | str = "70",
        watchlist_threshold: Decimal | str = "45",
        minimum_directional_change_ratio: Decimal | str = "0.04",
        minimum_movement_efficiency: Decimal | str = "0.35",
        minimum_reversion_volatility: Decimal | str = "0.05",
    ) -> None:
        if not callable(connection_factory):
            raise OpportunityCandidateConfigurationError("connection_factory must be callable.")
        self._connection_factory = connection_factory
        self._stale_after_seconds = int(stale_after_seconds)
        self._minimum_observations = int(minimum_observations)
        self._market_limit = int(market_limit)
        self._history_limit_per_market = int(history_limit_per_market)
        for name, value in (
            ("stale_after_seconds", self._stale_after_seconds),
            ("minimum_observations", self._minimum_observations),
            ("market_limit", self._market_limit),
            ("history_limit_per_market", self._history_limit_per_market),
        ):
            if value <= 0:
                raise OpportunityCandidateConfigurationError(f"{name} must be positive.")
        self._useful_threshold = _decimal(useful_threshold)
        self._watchlist_threshold = _decimal(watchlist_threshold)
        self._minimum_directional_change_ratio = _decimal(minimum_directional_change_ratio)
        self._minimum_movement_efficiency = _decimal(minimum_movement_efficiency)
        self._minimum_reversion_volatility = _decimal(minimum_reversion_volatility)
        if self._minimum_directional_change_ratio < 0 or self._minimum_movement_efficiency < 0 or self._minimum_reversion_volatility < 0:
            raise OpportunityCandidateConfigurationError("Candidate thresholds cannot be negative.")

    def generate(self, *, generated_at: Optional[datetime] = None) -> OracleOpportunityCandidateReport:
        checked = _aware_utc(generated_at or datetime.now(timezone.utc), "generated_at")
        feature_report = OracleCanonicalMarketFeatureExtractionEngine(
            connection_factory=self._connection_factory,
            stale_after_seconds=self._stale_after_seconds,
            minimum_observations=self._minimum_observations,
            market_limit=self._market_limit,
            history_limit_per_market=self._history_limit_per_market,
        ).extract(extracted_at=checked)
        usefulness_report = OracleMarketUsefulnessScoringEngine(
            connection_factory=self._connection_factory,
            stale_after_seconds=self._stale_after_seconds,
            minimum_observations=self._minimum_observations,
            market_limit=self._market_limit,
            history_limit_per_market=self._history_limit_per_market,
            useful_threshold=self._useful_threshold,
            watchlist_threshold=self._watchlist_threshold,
        ).score_feature_report(feature_report=feature_report, scored_at=checked)
        return self.generate_from_reports(feature_report=feature_report, usefulness_report=usefulness_report, generated_at=checked)

    def generate_from_reports(
        self,
        *,
        feature_report: OracleCanonicalMarketFeatureReport,
        usefulness_report: OracleMarketUsefulnessReport,
        generated_at: Optional[datetime] = None,
    ) -> OracleOpportunityCandidateReport:
        checked = _aware_utc(generated_at or usefulness_report.scored_at, "generated_at")
        if usefulness_report.feature_report_hash != feature_report.report_hash:
            raise OpportunityCandidateInvariantError("Usefulness report does not reference the supplied feature report.")
        features = {item.market_id: item for item in feature_report.markets}
        usefulness = {item.market_id: item for item in usefulness_report.markets}
        if set(features) != set(usefulness):
            raise OpportunityCandidateInvariantError("Feature and usefulness market cohorts must match exactly.")
        records = tuple(
            self._classify_market(features[market_id], usefulness[market_id])
            for market_id in sorted(features)
        )
        candidates = tuple(item for item in records if item.disposition == CANDIDATE)
        average = Decimal("0") if not candidates else sum((_decimal(item.candidate_score) for item in candidates), Decimal("0")) / Decimal(len(candidates))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": checked,
            "feature_report_hash": feature_report.report_hash,
            "usefulness_report_hash": usefulness_report.report_hash,
            "reviewed_market_count": len(records),
            "candidate_market_count": len(candidates),
            "excluded_market_count": sum(item.disposition == EXCLUDED for item in records),
            "momentum_candidate_count": sum(item.candidate_family == MOMENTUM_CONTINUATION for item in candidates),
            "reversion_watch_count": sum(item.candidate_family == VOLATILITY_REVERSION_WATCH for item in candidates),
            "average_candidate_score": _score_text(average),
            "markets": records,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "trading_recommendations_allowed": False,
            "opportunity_candidates_allowed": True,
            "raw_corpus_mutation_allowed": False,
        }
        return OracleOpportunityCandidateReport(**payload, report_hash=stable_hash(payload))

    def _classify_market(self, feature: OracleCanonicalMarketFeatureRecord, usefulness: Any) -> OracleOpportunityCandidateRecord:
        if usefulness.feature_hash != feature.feature_hash:
            raise OpportunityCandidateInvariantError(f"Feature hash mismatch for market {feature.market_id}.")
        reasons: list[str] = []
        family = NO_CANDIDATE
        direction = NEUTRAL_DIRECTION
        disposition = EXCLUDED
        directional_ratio = _decimal(feature.directional_change_ratio)
        directional_change = _decimal(feature.directional_change_dollars)
        volatility = _decimal(feature.normalized_volatility_ratio)
        efficiency = _decimal(feature.movement_efficiency_ratio)
        usefulness_score = _decimal(usefulness.usefulness_score)
        magnitude = abs(directional_ratio)

        if usefulness.classification != USEFUL:
            reasons.append("market_not_useful")
        elif directional_change > 0:
            direction = YES_DIRECTION
        elif directional_change < 0:
            direction = NO_DIRECTION
        else:
            reasons.append("neutral_direction")

        if usefulness.classification == USEFUL and direction != NEUTRAL_DIRECTION:
            if magnitude >= self._minimum_directional_change_ratio and efficiency >= self._minimum_movement_efficiency:
                disposition = CANDIDATE
                family = MOMENTUM_CONTINUATION
                reasons.append("directional_movement_with_efficiency")
            elif volatility >= self._minimum_reversion_volatility and efficiency < self._minimum_movement_efficiency:
                disposition = CANDIDATE
                family = VOLATILITY_REVERSION_WATCH
                reasons.append("high_volatility_low_efficiency")
            else:
                reasons.append("insufficient_candidate_evidence")

        movement_component = _clamp(magnitude / max(self._minimum_directional_change_ratio, Decimal("0.000001")))
        efficiency_component = _clamp(efficiency / max(self._minimum_movement_efficiency, Decimal("0.000001")))
        volatility_component = _clamp(volatility / max(self._minimum_reversion_volatility, Decimal("0.000001")))
        evidence_component = efficiency_component if family == MOMENTUM_CONTINUATION else volatility_component
        candidate_score = usefulness_score * Decimal("0.55") + movement_component * Decimal("25") + evidence_component * Decimal("20")
        if disposition == EXCLUDED:
            candidate_score = Decimal("0")

        payload = {
            "market_id": feature.market_id,
            "disposition": disposition,
            "candidate_family": family,
            "research_direction": direction,
            "candidate_score": _score_text(candidate_score),
            "usefulness_score": usefulness.usefulness_score,
            "latest_price_dollars": feature.latest_price_dollars,
            "directional_change_dollars": feature.directional_change_dollars,
            "directional_change_ratio": feature.directional_change_ratio,
            "normalized_volatility_ratio": feature.normalized_volatility_ratio,
            "movement_efficiency_ratio": feature.movement_efficiency_ratio,
            "spread_to_price_ratio": feature.spread_to_price_ratio,
            "observation_count": feature.observation_count,
            "reason_codes": tuple(sorted(set(reasons))),
            "feature_hash": feature.feature_hash,
            "usefulness_hash": usefulness.usefulness_hash,
        }
        return OracleOpportunityCandidateRecord(**payload, candidate_hash=stable_hash(payload))


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def resolve_database_url() -> str:
    value = os.getenv("ORACLE_POSTGRESQL_URL") or os.getenv("DATABASE_URL")
    if not value:
        raise OpportunityCandidateConfigurationError("Set ORACLE_POSTGRESQL_URL or DATABASE_URL.")
    return value


def connect_postgresql(database_url: str) -> Any:
    try:
        import psycopg
        return psycopg.connect(database_url)
    except ImportError:
        try:
            import psycopg2
            return psycopg2.connect(database_url)
        except ImportError as exc:
            raise OpportunityCandidateConfigurationError("Install psycopg or psycopg2.") from exc


def format_report(report: OracleOpportunityCandidateReport) -> str:
    lines = [
        "=" * 126,
        "ORACLE OPPORTUNITY CANDIDATE RESEARCH REPORT",
        "=" * 126,
        f"Generated at: {report.generated_at.isoformat()}",
        f"Reviewed: {report.reviewed_market_count} | candidates={report.candidate_market_count} | excluded={report.excluded_market_count}",
        f"Momentum: {report.momentum_candidate_count} | reversion-watch={report.reversion_watch_count} | average candidate score={report.average_candidate_score}",
        "-" * 126,
        f"{'MARKET':30} {'STATE':10} {'FAMILY':28} {'DIR':8} {'SCORE':>7} {'USEFUL':>7} {'PRICE':>8} REASONS",
    ]
    for item in sorted(report.markets, key=lambda row: (row.disposition != CANDIDATE, -float(row.candidate_score), row.market_id)):
        lines.append(
            f"{item.market_id[:30]:30} {item.disposition:10} {item.candidate_family:28} {item.research_direction:8} "
            f"{item.candidate_score:>7} {item.usefulness_score:>7} {str(item.latest_price_dollars):>8} {','.join(item.reason_codes)}"
        )
    if not report.markets:
        lines.append("No quality-approved market feature records were available for candidate review.")
    lines.extend([
        "-" * 126,
        f"Feature report hash:    {report.feature_report_hash}",
        f"Usefulness report hash: {report.usefulness_report_hash}",
        f"Candidate report hash:  {report.report_hash}",
        "READ-ONLY RESEARCH: candidates are not signals, alerts, recommendations, Q Series handoffs, or execution instructions.",
    ])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate read-only Oracle research opportunity candidates.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--stale-after-seconds", type=int, default=300)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--market-limit", type=int, default=1000)
    parser.add_argument("--history-limit-per-market", type=int, default=1000)
    parser.add_argument("--useful-threshold", default="70")
    parser.add_argument("--watchlist-threshold", default="45")
    parser.add_argument("--minimum-directional-change-ratio", default="0.04")
    parser.add_argument("--minimum-movement-efficiency", default="0.35")
    parser.add_argument("--minimum-reversion-volatility", default="0.05")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    _load_env(Path(args.env_file))
    engine = OracleOpportunityCandidateGenerator(
        connection_factory=lambda: connect_postgresql(resolve_database_url()),
        stale_after_seconds=args.stale_after_seconds,
        minimum_observations=args.minimum_observations,
        market_limit=args.market_limit,
        history_limit_per_market=args.history_limit_per_market,
        useful_threshold=args.useful_threshold,
        watchlist_threshold=args.watchlist_threshold,
        minimum_directional_change_ratio=args.minimum_directional_change_ratio,
        minimum_movement_efficiency=args.minimum_movement_efficiency,
        minimum_reversion_volatility=args.minimum_reversion_volatility,
    )
    report = engine.generate()
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
