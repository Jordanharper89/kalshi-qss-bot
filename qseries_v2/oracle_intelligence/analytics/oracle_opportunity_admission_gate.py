"""
OIA-007
Oracle Opportunity Admission Gate

Read-only deterministic admission policy over OIA-006 research opportunity
candidates. Admission permits forward shadow evaluation only. It does not create
signals, alerts, recommendations, Q Series handoffs, or execution instructions.
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

from .oracle_opportunity_candidate_generator import (
    CANDIDATE,
    MOMENTUM_CONTINUATION,
    NEUTRAL_DIRECTION,
    VOLATILITY_REVERSION_WATCH,
    OracleOpportunityCandidateGenerator,
    OracleOpportunityCandidateRecord,
    OracleOpportunityCandidateReport,
)

SCHEMA_VERSION = "OIA-007"
ENGINE_ID = "OIA-007"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SHADOW_EVALUATION_ADMISSION_ALLOWED = True
RAW_CORPUS_MUTATION_ALLOWED = False

ADMITTED = "admitted"
DENIED = "denied"
NOT_CANDIDATE = "not_candidate"


class OpportunityAdmissionError(RuntimeError):
    pass


class OpportunityAdmissionConfigurationError(OpportunityAdmissionError):
    pass


class OpportunityAdmissionInvariantError(OpportunityAdmissionError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OpportunityAdmissionInvariantError(f"{name} must be timezone-aware.")
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
    encoded = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
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


def _score_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


@dataclass(frozen=True)
class OracleOpportunityAdmissionRecord:
    market_id: str
    admission_status: str
    candidate_family: str
    research_direction: str
    candidate_score: str
    admission_score: str
    latest_price_dollars: Optional[str]
    spread_to_price_ratio: Optional[str]
    observation_count: int
    reason_codes: tuple[str, ...]
    candidate_hash: str
    admission_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleOpportunityAdmissionReport:
    schema_version: str
    engine_id: str
    evaluated_at: datetime
    candidate_report_hash: str
    reviewed_market_count: int
    admitted_market_count: int
    denied_market_count: int
    not_candidate_market_count: int
    admitted_momentum_count: int
    admitted_reversion_count: int
    average_admitted_score: str
    markets: tuple[OracleOpportunityAdmissionRecord, ...]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    shadow_evaluation_admission_allowed: bool
    raw_corpus_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleOpportunityAdmissionGate:
    read_only = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    shadow_evaluation_admission_allowed = True
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
        momentum_admission_score: Decimal | str = "75",
        reversion_admission_score: Decimal | str = "72",
        maximum_spread_to_price_ratio: Decimal | str = "0.08",
        minimum_admission_observations: int = 10,
        minimum_price_dollars: Decimal | str = "0.05",
        maximum_price_dollars: Decimal | str = "0.95",
    ) -> None:
        if not callable(connection_factory):
            raise OpportunityAdmissionConfigurationError("connection_factory must be callable.")
        self._connection_factory = connection_factory
        self._stale_after_seconds = int(stale_after_seconds)
        self._minimum_observations = int(minimum_observations)
        self._market_limit = int(market_limit)
        self._history_limit_per_market = int(history_limit_per_market)
        self._minimum_admission_observations = int(minimum_admission_observations)
        for name, value in (
            ("stale_after_seconds", self._stale_after_seconds),
            ("minimum_observations", self._minimum_observations),
            ("market_limit", self._market_limit),
            ("history_limit_per_market", self._history_limit_per_market),
            ("minimum_admission_observations", self._minimum_admission_observations),
        ):
            if value <= 0:
                raise OpportunityAdmissionConfigurationError(f"{name} must be positive.")
        self._candidate_kwargs = {
            "useful_threshold": useful_threshold,
            "watchlist_threshold": watchlist_threshold,
            "minimum_directional_change_ratio": minimum_directional_change_ratio,
            "minimum_movement_efficiency": minimum_movement_efficiency,
            "minimum_reversion_volatility": minimum_reversion_volatility,
        }
        self._momentum_admission_score = _decimal(momentum_admission_score)
        self._reversion_admission_score = _decimal(reversion_admission_score)
        self._maximum_spread_to_price_ratio = _decimal(maximum_spread_to_price_ratio)
        self._minimum_price_dollars = _decimal(minimum_price_dollars)
        self._maximum_price_dollars = _decimal(maximum_price_dollars)
        if self._momentum_admission_score < 0 or self._reversion_admission_score < 0:
            raise OpportunityAdmissionConfigurationError("Admission scores cannot be negative.")
        if self._maximum_spread_to_price_ratio < 0:
            raise OpportunityAdmissionConfigurationError("maximum_spread_to_price_ratio cannot be negative.")
        if not Decimal("0") <= self._minimum_price_dollars < self._maximum_price_dollars <= Decimal("1"):
            raise OpportunityAdmissionConfigurationError("Price policy must satisfy 0 <= minimum < maximum <= 1.")

    def evaluate(self, *, evaluated_at: Optional[datetime] = None) -> OracleOpportunityAdmissionReport:
        checked = _aware_utc(evaluated_at or datetime.now(timezone.utc), "evaluated_at")
        candidate_report = OracleOpportunityCandidateGenerator(
            connection_factory=self._connection_factory,
            stale_after_seconds=self._stale_after_seconds,
            minimum_observations=self._minimum_observations,
            market_limit=self._market_limit,
            history_limit_per_market=self._history_limit_per_market,
            **self._candidate_kwargs,
        ).generate(generated_at=checked)
        return self.evaluate_candidate_report(candidate_report=candidate_report, evaluated_at=checked)

    def evaluate_candidate_report(
        self,
        *,
        candidate_report: OracleOpportunityCandidateReport,
        evaluated_at: Optional[datetime] = None,
    ) -> OracleOpportunityAdmissionReport:
        checked = _aware_utc(evaluated_at or candidate_report.generated_at, "evaluated_at")
        if candidate_report.schema_version != "OIA-006" or candidate_report.engine_id != "OIA-006":
            raise OpportunityAdmissionInvariantError("Unsupported OIA-006 candidate report identity.")
        candidate_payload = dict(candidate_report.to_dict())
        candidate_digest = candidate_payload.pop("report_hash")
        if candidate_digest != stable_hash(candidate_payload):
            raise OpportunityAdmissionInvariantError("OIA-006 candidate report hash verification failed.")
        records = tuple(self._evaluate_market(item) for item in candidate_report.markets)
        admitted = tuple(item for item in records if item.admission_status == ADMITTED)
        average = Decimal("0") if not admitted else sum(
            (_decimal(item.admission_score) for item in admitted), Decimal("0")
        ) / Decimal(len(admitted))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": checked,
            "candidate_report_hash": candidate_report.report_hash,
            "reviewed_market_count": len(records),
            "admitted_market_count": len(admitted),
            "denied_market_count": sum(item.admission_status == DENIED for item in records),
            "not_candidate_market_count": sum(item.admission_status == NOT_CANDIDATE for item in records),
            "admitted_momentum_count": sum(
                item.candidate_family == MOMENTUM_CONTINUATION for item in admitted
            ),
            "admitted_reversion_count": sum(
                item.candidate_family == VOLATILITY_REVERSION_WATCH for item in admitted
            ),
            "average_admitted_score": _score_text(average),
            "markets": records,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "trading_recommendations_allowed": False,
            "shadow_evaluation_admission_allowed": True,
            "raw_corpus_mutation_allowed": False,
        }
        return OracleOpportunityAdmissionReport(**payload, report_hash=stable_hash(payload))

    def _evaluate_market(self, candidate: OracleOpportunityCandidateRecord) -> OracleOpportunityAdmissionRecord:
        candidate_payload = dict(candidate.to_dict())
        candidate_digest = candidate_payload.pop("candidate_hash")
        if candidate_digest != stable_hash(candidate_payload):
            raise OpportunityAdmissionInvariantError(
                f"OIA-006 candidate hash verification failed for market {candidate.market_id}."
            )
        reasons: list[str] = []
        status = NOT_CANDIDATE
        candidate_score = _decimal(candidate.candidate_score)
        spread_ratio = _decimal(candidate.spread_to_price_ratio)
        latest_price = _decimal(candidate.latest_price_dollars, "-1")
        threshold = (
            self._momentum_admission_score
            if candidate.candidate_family == MOMENTUM_CONTINUATION
            else self._reversion_admission_score
        )

        if candidate.disposition != CANDIDATE:
            reasons.append("upstream_not_candidate")
        else:
            status = ADMITTED
            if candidate.candidate_family not in {MOMENTUM_CONTINUATION, VOLATILITY_REVERSION_WATCH}:
                status = DENIED
                reasons.append("unsupported_candidate_family")
            if candidate.research_direction == NEUTRAL_DIRECTION:
                status = DENIED
                reasons.append("neutral_research_direction")
            if candidate_score < threshold:
                status = DENIED
                reasons.append("candidate_score_below_admission_threshold")
            if candidate.observation_count < self._minimum_admission_observations:
                status = DENIED
                reasons.append("insufficient_admission_history")
            if candidate.spread_to_price_ratio is None:
                status = DENIED
                reasons.append("missing_spread_ratio")
            elif spread_ratio > self._maximum_spread_to_price_ratio:
                status = DENIED
                reasons.append("spread_too_wide_for_shadow_evaluation")
            if candidate.latest_price_dollars is None:
                status = DENIED
                reasons.append("missing_latest_price")
            elif latest_price < self._minimum_price_dollars or latest_price > self._maximum_price_dollars:
                status = DENIED
                reasons.append("price_outside_shadow_evaluation_band")
            if status == ADMITTED:
                reasons.append("meets_shadow_evaluation_admission_policy")

        admission_score = candidate_score if status == ADMITTED else Decimal("0")
        payload = {
            "market_id": candidate.market_id,
            "admission_status": status,
            "candidate_family": candidate.candidate_family,
            "research_direction": candidate.research_direction,
            "candidate_score": candidate.candidate_score,
            "admission_score": _score_text(admission_score),
            "latest_price_dollars": candidate.latest_price_dollars,
            "spread_to_price_ratio": candidate.spread_to_price_ratio,
            "observation_count": candidate.observation_count,
            "reason_codes": tuple(sorted(set(reasons))),
            "candidate_hash": candidate.candidate_hash,
        }
        return OracleOpportunityAdmissionRecord(**payload, admission_hash=stable_hash(payload))


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
        raise OpportunityAdmissionConfigurationError("Set ORACLE_POSTGRESQL_URL or DATABASE_URL.")
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
            raise OpportunityAdmissionConfigurationError("Install psycopg or psycopg2.") from exc


def format_report(report: OracleOpportunityAdmissionReport) -> str:
    lines = [
        "=" * 132,
        "ORACLE OPPORTUNITY SHADOW-EVALUATION ADMISSION REPORT",
        "=" * 132,
        f"Evaluated at: {report.evaluated_at.isoformat()}",
        f"Reviewed: {report.reviewed_market_count} | admitted={report.admitted_market_count} | denied={report.denied_market_count} | not-candidate={report.not_candidate_market_count}",
        f"Admitted momentum: {report.admitted_momentum_count} | admitted reversion={report.admitted_reversion_count} | average admitted score={report.average_admitted_score}",
        "-" * 132,
        f"{'MARKET':30} {'STATUS':14} {'FAMILY':28} {'DIR':8} {'CAND':>7} {'ADMIT':>7} {'PRICE':>8} {'SPREAD':>8} REASONS",
    ]
    for item in sorted(
        report.markets,
        key=lambda row: (row.admission_status != ADMITTED, -float(row.admission_score), row.market_id),
    ):
        lines.append(
            f"{item.market_id[:30]:30} {item.admission_status:14} {item.candidate_family:28} {item.research_direction:8} "
            f"{item.candidate_score:>7} {item.admission_score:>7} {str(item.latest_price_dollars):>8} "
            f"{str(item.spread_to_price_ratio):>8} {','.join(item.reason_codes)}"
        )
    if not report.markets:
        lines.append("No OIA-006 candidate records were available for admission review.")
    lines.extend([
        "-" * 132,
        f"Candidate report hash: {report.candidate_report_hash}",
        f"Admission report hash: {report.report_hash}",
        "READ-ONLY SHADOW ADMISSION: admitted records are not signals, alerts, recommendations, Q Series handoffs, or execution instructions.",
    ])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Oracle research candidates for read-only shadow tracking admission.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--stale-after-seconds", type=int, default=300)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--market-limit", type=int, default=1000)
    parser.add_argument("--history-limit-per-market", type=int, default=1000)
    parser.add_argument("--momentum-admission-score", default="75")
    parser.add_argument("--reversion-admission-score", default="72")
    parser.add_argument("--maximum-spread-to-price-ratio", default="0.08")
    parser.add_argument("--minimum-admission-observations", type=int, default=10)
    parser.add_argument("--minimum-price-dollars", default="0.05")
    parser.add_argument("--maximum-price-dollars", default="0.95")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    _load_env(Path(args.env_file))
    gate = OracleOpportunityAdmissionGate(
        connection_factory=lambda: connect_postgresql(resolve_database_url()),
        stale_after_seconds=args.stale_after_seconds,
        minimum_observations=args.minimum_observations,
        market_limit=args.market_limit,
        history_limit_per_market=args.history_limit_per_market,
        momentum_admission_score=args.momentum_admission_score,
        reversion_admission_score=args.reversion_admission_score,
        maximum_spread_to_price_ratio=args.maximum_spread_to_price_ratio,
        minimum_admission_observations=args.minimum_admission_observations,
        minimum_price_dollars=args.minimum_price_dollars,
        maximum_price_dollars=args.maximum_price_dollars,
    )
    report = gate.evaluate()
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
