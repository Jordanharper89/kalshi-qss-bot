"""
OIA-010
Oracle Forward Shadow Outcome Evaluator

Evaluates matured horizons from the immutable OIA-009 forward-shadow ledger
against canonical PostgreSQL market observations. Outcome artifacts are written
separately and immutably. Canonical observations and OIA-009 entry records are
never modified. No signal, alert, recommendation, Q Series handoff, order, or
portfolio action is produced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional

from .oracle_forward_shadow_evaluation_ledger import (
    DEFAULT_LEDGER_DIRECTORY,
    OracleForwardShadowEvaluationLedger,
    OracleForwardShadowLedgerEntry,
    stable_hash as ledger_stable_hash,
)

SCHEMA_VERSION = "OIA-010"
ENGINE_ID = "OIA-010"
READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
OUTCOME_ARTIFACT_PERSISTENCE_ALLOWED = True
RAW_CORPUS_MUTATION_ALLOWED = False
LEDGER_ENTRY_MUTATION_ALLOWED = False
DEFAULT_OUTCOME_DIRECTORY = Path("runtime") / "oracle_intelligence" / "forward_shadow_outcomes"
DEFAULT_MAX_OBSERVATION_DELAY_SECONDS = 300
PENDING = "pending"
MATURED_NO_OBSERVATION = "matured_no_observation"
GRADED = "graded"
WIN = "win"
LOSS = "loss"
FLAT = "flat"


class ForwardShadowOutcomeError(RuntimeError):
    pass


class ForwardShadowOutcomeConfigurationError(ForwardShadowOutcomeError):
    pass


class ForwardShadowOutcomeInvariantError(ForwardShadowOutcomeError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ForwardShadowOutcomeInvariantError(f"{name} must be timezone-aware.")
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


def _decimal(value: Any, name: str) -> Decimal:
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise ForwardShadowOutcomeInvariantError(f"{name} must be a finite decimal.") from exc
    if not result.is_finite():
        raise ForwardShadowOutcomeInvariantError(f"{name} must be a finite decimal.")
    return result


def _parse_datetime(value: Any, name: str) -> datetime:
    if isinstance(value, datetime):
        return _aware_utc(value, name)
    if not isinstance(value, str) or not value.strip():
        raise ForwardShadowOutcomeInvariantError(f"{name} must be an ISO-8601 datetime.")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ForwardShadowOutcomeInvariantError(f"{name} must be an ISO-8601 datetime.") from exc
    return _aware_utc(parsed, name)


def _atomic_json_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(_canonical(payload), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", delete=False,
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp",
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


OUTCOME_OBSERVATION_SQL = """
/* oia010:first_observation_at_or_after_horizon */
WITH normalized AS (
    SELECT sequence_number, observed_at, persisted_at, observation_id, content_hash,
           COALESCE(canonical_observation_json->'raw_observation'->'payload',
                    canonical_observation_json->'payload', '{}'::jsonb) AS payload
    FROM oracle_canonical_observations
    WHERE observation_type = 'market_snapshot'
), identified AS (
    SELECT *, COALESCE(NULLIF(payload->>'source_market_id',''),
                       NULLIF(payload->>'market_id',''),
                       NULLIF(payload->>'source_symbol','')) AS market_id
    FROM normalized
)
SELECT sequence_number, observed_at, persisted_at, observation_id, content_hash,
       COALESCE(NULLIF(payload->>'last_price_dollars',''),
                NULLIF(payload->>'yes_mid_dollars',''),
                CASE
                    WHEN NULLIF(payload->>'yes_bid_dollars','') IS NOT NULL
                     AND NULLIF(payload->>'yes_ask_dollars','') IS NOT NULL
                    THEN ((payload->>'yes_bid_dollars')::numeric +
                          (payload->>'yes_ask_dollars')::numeric) / 2
                    ELSE NULL
                END::text) AS outcome_price_dollars
FROM identified
WHERE market_id = %s
  AND observed_at >= %s
  AND observed_at <= %s
ORDER BY observed_at ASC, sequence_number ASC
LIMIT 1
"""


@dataclass(frozen=True)
class OracleForwardShadowHorizonOutcome:
    schema_version: str
    engine_id: str
    evaluated_at: datetime
    evaluation_id: str
    market_id: str
    candidate_family: str
    research_direction: str
    horizon_seconds: int
    due_at: datetime
    entry_price_dollars: str
    status: str
    grade: Optional[str]
    outcome_price_dollars: Optional[str]
    directional_return: Optional[str]
    absolute_return: Optional[str]
    observation_sequence_number: Optional[int]
    observation_id: Optional[str]
    observation_content_hash: Optional[str]
    observation_observed_at: Optional[datetime]
    observation_persisted_at: Optional[datetime]
    observation_delay_seconds: Optional[str]
    ledger_entry_hash: str
    reason_codes: tuple[str, ...]
    outcome_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleForwardShadowOutcomeEvaluationReport:
    schema_version: str
    engine_id: str
    evaluated_at: datetime
    ledger_directory: str
    outcome_directory: str
    ledger_entry_count: int
    horizon_count: int
    pending_horizon_count: int
    matured_no_observation_count: int
    newly_graded_count: int
    existing_graded_count: int
    win_count: int
    loss_count: int
    flat_count: int
    outcomes: tuple[OracleForwardShadowHorizonOutcome, ...]
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    outcome_artifact_persistence_allowed: bool
    raw_corpus_mutation_allowed: bool
    ledger_entry_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleForwardShadowOutcomeEvaluator:
    read_only_corpus = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    outcome_artifact_persistence_allowed = True
    raw_corpus_mutation_allowed = False
    ledger_entry_mutation_allowed = False

    def __init__(
        self,
        *,
        connection_factory: Callable[[], Any],
        ledger_directory: Path | str = DEFAULT_LEDGER_DIRECTORY,
        outcome_directory: Path | str = DEFAULT_OUTCOME_DIRECTORY,
        max_observation_delay_seconds: int = DEFAULT_MAX_OBSERVATION_DELAY_SECONDS,
    ) -> None:
        if not callable(connection_factory):
            raise ForwardShadowOutcomeConfigurationError("connection_factory must be callable.")
        if int(max_observation_delay_seconds) <= 0:
            raise ForwardShadowOutcomeConfigurationError("max_observation_delay_seconds must be positive.")
        self._connection_factory = connection_factory
        self._ledger_directory = Path(ledger_directory)
        self._outcome_directory = Path(outcome_directory)
        self._max_delay = int(max_observation_delay_seconds)

    def evaluate(self, *, evaluated_at: Optional[datetime] = None) -> OracleForwardShadowOutcomeEvaluationReport:
        anchor = _aware_utc(evaluated_at or datetime.now(timezone.utc), "evaluated_at")
        entries = OracleForwardShadowEvaluationLedger(
            ledger_directory=self._ledger_directory
        ).load_entries()
        connection = self._connection_factory()
        outcomes: list[OracleForwardShadowHorizonOutcome] = []
        newly_graded = 0
        existing_graded = 0
        try:
            for entry in entries:
                self._verify_entry(entry)
                for horizon in entry.horizons:
                    outcome, was_existing = self._evaluate_horizon(
                        connection=connection, entry=entry, horizon=horizon, evaluated_at=anchor
                    )
                    outcomes.append(outcome)
                    if outcome.status == GRADED:
                        if was_existing:
                            existing_graded += 1
                        else:
                            newly_graded += 1
        finally:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

        outcomes.sort(key=lambda item: (item.evaluation_id, item.horizon_seconds))
        pending = sum(item.status == PENDING for item in outcomes)
        missing = sum(item.status == MATURED_NO_OBSERVATION for item in outcomes)
        wins = sum(item.grade == WIN for item in outcomes)
        losses = sum(item.grade == LOSS for item in outcomes)
        flats = sum(item.grade == FLAT for item in outcomes)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": anchor,
            "ledger_directory": str(self._ledger_directory),
            "outcome_directory": str(self._outcome_directory),
            "ledger_entry_count": len(entries),
            "horizon_count": len(outcomes),
            "pending_horizon_count": pending,
            "matured_no_observation_count": missing,
            "newly_graded_count": newly_graded,
            "existing_graded_count": existing_graded,
            "win_count": wins,
            "loss_count": losses,
            "flat_count": flats,
            "outcomes": tuple(outcomes),
            "read_only_corpus": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "trading_recommendations_allowed": False,
            "outcome_artifact_persistence_allowed": True,
            "raw_corpus_mutation_allowed": False,
            "ledger_entry_mutation_allowed": False,
        }
        report = OracleForwardShadowOutcomeEvaluationReport(**payload, report_hash=stable_hash(payload))
        _atomic_json_write(self._outcome_directory / "last_evaluation_report.json", report.to_dict())
        return report

    def _evaluate_horizon(
        self, *, connection: Any, entry: OracleForwardShadowLedgerEntry,
        horizon: Mapping[str, Any], evaluated_at: datetime,
    ) -> tuple[OracleForwardShadowHorizonOutcome, bool]:
        seconds = int(horizon["horizon_seconds"])
        due_at = _parse_datetime(horizon["due_at"], "horizon.due_at")
        path = self._outcome_directory / "outcomes" / entry.evaluation_id / f"{seconds}.json"
        if path.exists():
            existing = self._outcome_from_payload(json.loads(path.read_text(encoding="utf-8")))
            return existing, True
        if evaluated_at < due_at:
            return self._build_ungraded(entry, seconds, due_at, evaluated_at, PENDING, ("horizon_not_due",)), False

        row = self._fetch_outcome_observation(connection, entry.market_id, due_at)
        if row is None:
            return self._build_ungraded(
                entry, seconds, due_at, evaluated_at, MATURED_NO_OBSERVATION,
                ("horizon_due", "no_canonical_observation_within_delay_policy"),
            ), False

        sequence_number, observed_at, persisted_at, observation_id, content_hash, price_value = row
        observed_at = _aware_utc(observed_at, "observation.observed_at")
        persisted_at = _aware_utc(persisted_at, "observation.persisted_at")
        entry_price = _decimal(entry.entry_price_dollars, "entry_price_dollars")
        outcome_price = _decimal(price_value, "outcome_price_dollars")
        direction = entry.research_direction.strip().lower()
        if direction in {"yes", "long", "up"}:
            directional = outcome_price - entry_price
        elif direction in {"no", "short", "down"}:
            directional = entry_price - outcome_price
        else:
            raise ForwardShadowOutcomeInvariantError(
                f"Unsupported research direction for {entry.evaluation_id}: {entry.research_direction}"
            )
        grade = WIN if directional > 0 else LOSS if directional < 0 else FLAT
        delay = Decimal(str((observed_at - due_at).total_seconds()))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at,
            "evaluation_id": entry.evaluation_id,
            "market_id": entry.market_id,
            "candidate_family": entry.candidate_family,
            "research_direction": entry.research_direction,
            "horizon_seconds": seconds,
            "due_at": due_at,
            "entry_price_dollars": format(entry_price, "f"),
            "status": GRADED,
            "grade": grade,
            "outcome_price_dollars": format(outcome_price, "f"),
            "directional_return": format(directional, "f"),
            "absolute_return": format(abs(outcome_price - entry_price), "f"),
            "observation_sequence_number": int(sequence_number),
            "observation_id": str(observation_id),
            "observation_content_hash": str(content_hash),
            "observation_observed_at": observed_at,
            "observation_persisted_at": persisted_at,
            "observation_delay_seconds": format(delay, "f"),
            "ledger_entry_hash": entry.entry_hash,
            "reason_codes": ("horizon_due", "canonical_outcome_observation_found", f"graded_{grade}"),
        }
        outcome = OracleForwardShadowHorizonOutcome(**payload, outcome_hash=stable_hash(payload))
        _atomic_json_write(path, outcome.to_dict())
        return outcome, False

    def _fetch_outcome_observation(self, connection: Any, market_id: str, due_at: datetime) -> Optional[tuple[Any, ...]]:
        cursor = connection.cursor()
        try:
            cursor.execute(
                OUTCOME_OBSERVATION_SQL,
                (market_id, due_at, due_at + timedelta(seconds=self._max_delay)),
            )
            return cursor.fetchone()
        finally:
            close = getattr(cursor, "close", None)
            if callable(close):
                close()

    @staticmethod
    def _build_ungraded(
        entry: OracleForwardShadowLedgerEntry, seconds: int, due_at: datetime,
        evaluated_at: datetime, status: str, reasons: tuple[str, ...],
    ) -> OracleForwardShadowHorizonOutcome:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at,
            "evaluation_id": entry.evaluation_id,
            "market_id": entry.market_id,
            "candidate_family": entry.candidate_family,
            "research_direction": entry.research_direction,
            "horizon_seconds": seconds,
            "due_at": due_at,
            "entry_price_dollars": entry.entry_price_dollars,
            "status": status,
            "grade": None,
            "outcome_price_dollars": None,
            "directional_return": None,
            "absolute_return": None,
            "observation_sequence_number": None,
            "observation_id": None,
            "observation_content_hash": None,
            "observation_observed_at": None,
            "observation_persisted_at": None,
            "observation_delay_seconds": None,
            "ledger_entry_hash": entry.entry_hash,
            "reason_codes": reasons,
        }
        return OracleForwardShadowHorizonOutcome(**payload, outcome_hash=stable_hash(payload))

    @staticmethod
    def _verify_entry(entry: OracleForwardShadowLedgerEntry) -> None:
        if entry.schema_version != "OIA-009" or entry.engine_id != "OIA-009":
            raise ForwardShadowOutcomeInvariantError("Ledger entry is not an OIA-009 artifact.")
        payload = dict(entry.to_dict())
        digest = payload.pop("entry_hash")
        if digest != ledger_stable_hash(payload):
            raise ForwardShadowOutcomeInvariantError(f"Ledger entry hash mismatch: {entry.evaluation_id}")
        if entry.record_status != "pending":
            raise ForwardShadowOutcomeInvariantError("OIA-009 entry record_status must remain pending.")

    @staticmethod
    def _outcome_from_payload(payload: Mapping[str, Any]) -> OracleForwardShadowHorizonOutcome:
        values = dict(payload)
        values["evaluated_at"] = _parse_datetime(values["evaluated_at"], "evaluated_at")
        values["due_at"] = _parse_datetime(values["due_at"], "due_at")
        if values.get("observation_observed_at") is not None:
            values["observation_observed_at"] = _parse_datetime(values["observation_observed_at"], "observation_observed_at")
        if values.get("observation_persisted_at") is not None:
            values["observation_persisted_at"] = _parse_datetime(values["observation_persisted_at"], "observation_persisted_at")
        values["reason_codes"] = tuple(values.get("reason_codes", ()))
        outcome = OracleForwardShadowHorizonOutcome(**values)
        check = dict(outcome.to_dict())
        digest = check.pop("outcome_hash")
        if digest != stable_hash(check):
            raise ForwardShadowOutcomeInvariantError("Existing outcome hash mismatch.")
        return outcome


def resolve_database_url() -> str:
    from .oracle_live_corpus_inspector import load_environment_file, resolve_database_url as resolve
    load_environment_file(Path.cwd() / ".env")
    return resolve()


def connect_postgresql(database_url: str) -> Any:
    try:
        import psycopg
        return psycopg.connect(database_url)
    except ImportError:
        try:
            import psycopg2
            return psycopg2.connect(database_url)
        except ImportError as exc:
            raise ForwardShadowOutcomeConfigurationError("Install psycopg or psycopg2.") from exc


def format_report(report: OracleForwardShadowOutcomeEvaluationReport) -> str:
    lines = [
        "========================================",
        " OIA-010 FORWARD SHADOW OUTCOMES",
        "========================================",
        f"Evaluated at: {report.evaluated_at.isoformat()}",
        f"Ledger entries: {report.ledger_entry_count}",
        f"Horizons reviewed: {report.horizon_count}",
        f"Newly graded: {report.newly_graded_count}",
        f"Previously graded: {report.existing_graded_count}",
        f"Pending: {report.pending_horizon_count}",
        f"Matured without observation: {report.matured_no_observation_count}",
        f"Wins / losses / flat: {report.win_count} / {report.loss_count} / {report.flat_count}",
        f"Report hash: {report.report_hash}",
    ]
    for item in report.outcomes:
        lines.append(
            f"- {item.market_id} | {item.horizon_seconds}s | {item.status} | "
            f"grade={item.grade or '-'} | return={item.directional_return or '-'}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate matured OIA-009 forward-shadow horizons.")
    parser.add_argument("--ledger-directory", default=str(DEFAULT_LEDGER_DIRECTORY))
    parser.add_argument("--outcome-directory", default=str(DEFAULT_OUTCOME_DIRECTORY))
    parser.add_argument("--max-observation-delay-seconds", type=int, default=DEFAULT_MAX_OBSERVATION_DELAY_SECONDS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    evaluator = OracleForwardShadowOutcomeEvaluator(
        connection_factory=lambda: connect_postgresql(resolve_database_url()),
        ledger_directory=Path(args.ledger_directory),
        outcome_directory=Path(args.outcome_directory),
        max_observation_delay_seconds=args.max_observation_delay_seconds,
    )
    report = evaluator.evaluate()
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
