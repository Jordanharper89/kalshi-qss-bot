"""
OIA-008
Oracle Forward Shadow Evaluation Record Builder

Builds immutable forward-only shadow evaluation records from OIA-007 admitted
research candidates. Records seal the entry state and fixed future evaluation
horizons. No outcomes are measured here, and no signals, alerts, Q Series
handoffs, or execution instructions are created.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence

from .oracle_opportunity_admission_gate import (
    ADMITTED,
    OracleOpportunityAdmissionGate,
    OracleOpportunityAdmissionRecord,
    OracleOpportunityAdmissionReport,
)

SCHEMA_VERSION = "OIA-008"
ENGINE_ID = "OIA-008"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
FORWARD_SHADOW_RECORDS_ALLOWED = True
OUTCOME_MEASUREMENT_ALLOWED = False
RAW_CORPUS_MUTATION_ALLOWED = False

PENDING = "pending"
NOT_ADMITTED = "not_admitted"
DEFAULT_HORIZON_SECONDS = (300, 900, 3600)


class ForwardShadowRecordError(RuntimeError):
    pass


class ForwardShadowRecordConfigurationError(ForwardShadowRecordError):
    pass


class ForwardShadowRecordInvariantError(ForwardShadowRecordError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ForwardShadowRecordInvariantError(f"{name} must be timezone-aware.")
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
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
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


@dataclass(frozen=True)
class OracleForwardShadowHorizon:
    horizon_seconds: int
    due_at: datetime
    status: str
    outcome_price_dollars: Optional[str]
    directional_return: Optional[str]
    outcome_hash: Optional[str]
    horizon_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleForwardShadowEvaluationRecord:
    evaluation_id: str
    market_id: str
    created_at: datetime
    admission_evaluated_at: datetime
    candidate_family: str
    research_direction: str
    admission_score: str
    entry_price_dollars: str
    spread_to_price_ratio: Optional[str]
    observation_count: int
    admission_hash: str
    horizons: tuple[OracleForwardShadowHorizon, ...]
    record_status: str
    reason_codes: tuple[str, ...]
    record_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleForwardShadowEvaluationReport:
    schema_version: str
    engine_id: str
    created_at: datetime
    admission_report_hash: str
    reviewed_market_count: int
    evaluation_record_count: int
    skipped_market_count: int
    horizon_seconds: tuple[int, ...]
    records: tuple[OracleForwardShadowEvaluationRecord, ...]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    forward_shadow_records_allowed: bool
    outcome_measurement_allowed: bool
    raw_corpus_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleForwardShadowEvaluationRecordBuilder:
    read_only = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    forward_shadow_records_allowed = True
    outcome_measurement_allowed = False
    raw_corpus_mutation_allowed = False

    def __init__(
        self,
        *,
        connection_factory: Callable[[], Any],
        horizon_seconds: Sequence[int] = DEFAULT_HORIZON_SECONDS,
        stale_after_seconds: int = 300,
        minimum_observations: int = 3,
        market_limit: int = 1000,
        history_limit_per_market: int = 1000,
        momentum_admission_score: Decimal | str = "75",
        reversion_admission_score: Decimal | str = "72",
        maximum_spread_to_price_ratio: Decimal | str = "0.08",
        minimum_admission_observations: int = 10,
        minimum_price_dollars: Decimal | str = "0.05",
        maximum_price_dollars: Decimal | str = "0.95",
    ) -> None:
        if not callable(connection_factory):
            raise ForwardShadowRecordConfigurationError("connection_factory must be callable.")
        normalized = tuple(sorted({int(value) for value in horizon_seconds}))
        if not normalized or any(value <= 0 for value in normalized):
            raise ForwardShadowRecordConfigurationError("horizon_seconds must contain positive integers.")
        self._connection_factory = connection_factory
        self._horizon_seconds = normalized
        self._gate_kwargs = {
            "stale_after_seconds": stale_after_seconds,
            "minimum_observations": minimum_observations,
            "market_limit": market_limit,
            "history_limit_per_market": history_limit_per_market,
            "momentum_admission_score": momentum_admission_score,
            "reversion_admission_score": reversion_admission_score,
            "maximum_spread_to_price_ratio": maximum_spread_to_price_ratio,
            "minimum_admission_observations": minimum_admission_observations,
            "minimum_price_dollars": minimum_price_dollars,
            "maximum_price_dollars": maximum_price_dollars,
        }

    def build(self, *, created_at: Optional[datetime] = None) -> OracleForwardShadowEvaluationReport:
        anchor = _aware_utc(created_at or datetime.now(timezone.utc), "created_at")
        admission_report = OracleOpportunityAdmissionGate(
            connection_factory=self._connection_factory,
            **self._gate_kwargs,
        ).evaluate(evaluated_at=anchor)
        return self.build_from_admission_report(admission_report=admission_report, created_at=anchor)

    def build_from_admission_report(
        self,
        *,
        admission_report: OracleOpportunityAdmissionReport,
        created_at: Optional[datetime] = None,
    ) -> OracleForwardShadowEvaluationReport:
        anchor = _aware_utc(created_at or admission_report.evaluated_at, "created_at")
        if admission_report.schema_version != "OIA-007" or admission_report.engine_id != "OIA-007":
            raise ForwardShadowRecordInvariantError("Unsupported OIA-007 admission report identity.")
        report_payload = dict(admission_report.to_dict())
        report_digest = report_payload.pop("report_hash")
        if report_digest != stable_hash(report_payload):
            raise ForwardShadowRecordInvariantError("OIA-007 admission report hash verification failed.")
        records = tuple(
            self._build_record(item, admission_report.evaluated_at, anchor)
            for item in admission_report.markets
            if item.admission_status == ADMITTED
        )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "created_at": anchor,
            "admission_report_hash": admission_report.report_hash,
            "reviewed_market_count": admission_report.reviewed_market_count,
            "evaluation_record_count": len(records),
            "skipped_market_count": admission_report.reviewed_market_count - len(records),
            "horizon_seconds": self._horizon_seconds,
            "records": records,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "trading_recommendations_allowed": False,
            "forward_shadow_records_allowed": True,
            "outcome_measurement_allowed": False,
            "raw_corpus_mutation_allowed": False,
        }
        return OracleForwardShadowEvaluationReport(**payload, report_hash=stable_hash(payload))

    def _build_record(
        self,
        admission: OracleOpportunityAdmissionRecord,
        admission_evaluated_at: datetime,
        created_at: datetime,
    ) -> OracleForwardShadowEvaluationRecord:
        admission_payload = dict(admission.to_dict())
        admission_digest = admission_payload.pop("admission_hash")
        if admission_digest != stable_hash(admission_payload):
            raise ForwardShadowRecordInvariantError(
                f"OIA-007 admission hash verification failed for market {admission.market_id}."
            )
        if admission.admission_status != ADMITTED:
            raise ForwardShadowRecordInvariantError("Only admitted records can create shadow evaluations.")
        if admission.latest_price_dollars is None:
            raise ForwardShadowRecordInvariantError(
                f"Admitted market {admission.market_id} has no entry price."
            )
        entry_price = _decimal(admission.latest_price_dollars, "-1")
        if entry_price < Decimal("0") or entry_price > Decimal("1"):
            raise ForwardShadowRecordInvariantError(
                f"Admitted market {admission.market_id} has an invalid entry price."
            )
        evaluated_at = _aware_utc(admission_evaluated_at, "admission_evaluated_at")
        evaluation_identity = {
            "market_id": admission.market_id,
            "admission_hash": admission.admission_hash,
            "admission_evaluated_at": evaluated_at,
            "created_at": created_at,
            "horizon_seconds": self._horizon_seconds,
        }
        evaluation_id = stable_hash(evaluation_identity)
        horizons = tuple(self._build_horizon(created_at, seconds) for seconds in self._horizon_seconds)
        payload = {
            "evaluation_id": evaluation_id,
            "market_id": admission.market_id,
            "created_at": created_at,
            "admission_evaluated_at": evaluated_at,
            "candidate_family": admission.candidate_family,
            "research_direction": admission.research_direction,
            "admission_score": admission.admission_score,
            "entry_price_dollars": format(entry_price, "f"),
            "spread_to_price_ratio": admission.spread_to_price_ratio,
            "observation_count": admission.observation_count,
            "admission_hash": admission.admission_hash,
            "horizons": horizons,
            "record_status": PENDING,
            "reason_codes": ("forward_shadow_evaluation_initialized",),
        }
        return OracleForwardShadowEvaluationRecord(**payload, record_hash=stable_hash(payload))

    @staticmethod
    def _build_horizon(created_at: datetime, seconds: int) -> OracleForwardShadowHorizon:
        payload = {
            "horizon_seconds": seconds,
            "due_at": created_at + timedelta(seconds=seconds),
            "status": PENDING,
            "outcome_price_dollars": None,
            "directional_return": None,
            "outcome_hash": None,
        }
        return OracleForwardShadowHorizon(**payload, horizon_hash=stable_hash(payload))


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
        raise ForwardShadowRecordConfigurationError("Set ORACLE_POSTGRESQL_URL or DATABASE_URL.")
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
            raise ForwardShadowRecordConfigurationError("Install psycopg or psycopg2.") from exc


def format_report(report: OracleForwardShadowEvaluationReport) -> str:
    lines = [
        "=" * 136,
        "ORACLE FORWARD SHADOW EVALUATION RECORD REPORT",
        "=" * 136,
        f"Created at: {report.created_at.isoformat()}",
        f"Reviewed: {report.reviewed_market_count} | initialized={report.evaluation_record_count} | skipped={report.skipped_market_count}",
        f"Horizons: {', '.join(str(value) + 's' for value in report.horizon_seconds)}",
        "-" * 136,
        f"{'MARKET':30} {'EVALUATION ID':18} {'FAMILY':28} {'DIR':8} {'SCORE':>7} {'ENTRY':>8} {'STATUS':10} DUE TIMES",
    ]
    for item in sorted(report.records, key=lambda row: (-float(row.admission_score), row.market_id)):
        due_times = ",".join(horizon.due_at.isoformat() for horizon in item.horizons)
        lines.append(
            f"{item.market_id[:30]:30} {item.evaluation_id[:18]:18} {item.candidate_family:28} "
            f"{item.research_direction:8} {item.admission_score:>7} {item.entry_price_dollars:>8} "
            f"{item.record_status:10} {due_times}"
        )
    if not report.records:
        lines.append("No OIA-007 admitted markets were available for forward shadow initialization.")
    lines.extend([
        "-" * 136,
        f"Admission report hash: {report.admission_report_hash}",
        f"Forward shadow report hash: {report.report_hash}",
        "FORWARD-ONLY SHADOW RECORDS: outcomes are intentionally unset until their fixed deadlines are reached.",
        "NO SIGNALS / ALERTS / Q SERIES HANDOFF / EXECUTION.",
    ])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize immutable forward shadow evaluation records from OIA-007 admissions.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--horizon-seconds", default="300,900,3600")
    parser.add_argument("--stale-after-seconds", type=int, default=300)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--market-limit", type=int, default=1000)
    parser.add_argument("--history-limit-per-market", type=int, default=1000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    horizons = tuple(int(part.strip()) for part in args.horizon_seconds.split(",") if part.strip())
    _load_env(Path(args.env_file))
    builder = OracleForwardShadowEvaluationRecordBuilder(
        connection_factory=lambda: connect_postgresql(resolve_database_url()),
        horizon_seconds=horizons,
        stale_after_seconds=args.stale_after_seconds,
        minimum_observations=args.minimum_observations,
        market_limit=args.market_limit,
        history_limit_per_market=args.history_limit_per_market,
    )
    report = builder.build()
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
