"""
OIA-009
Oracle Forward Shadow Evaluation Ledger

Persists OIA-008 forward-shadow evaluation records as immutable research
artifacts so fixed-horizon outcomes can be measured later without regenerating
entry state or introducing hindsight. This ledger never mutates the canonical
PostgreSQL corpus and never creates signals, alerts, Q Series handoffs, orders,
or portfolio changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence

from .oracle_forward_shadow_evaluation_record_builder import (
    OracleForwardShadowEvaluationRecord,
    OracleForwardShadowEvaluationRecordBuilder,
    OracleForwardShadowEvaluationReport,
    stable_hash as upstream_stable_hash,
)

SCHEMA_VERSION = "OIA-009"
ENGINE_ID = "OIA-009"
READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
ANALYTICS_ARTIFACT_PERSISTENCE_ALLOWED = True
RAW_CORPUS_MUTATION_ALLOWED = False
DEFAULT_LEDGER_DIRECTORY = Path("runtime") / "oracle_intelligence" / "forward_shadow_evaluations"


class ForwardShadowLedgerError(RuntimeError):
    pass


class ForwardShadowLedgerConfigurationError(ForwardShadowLedgerError):
    pass


class ForwardShadowLedgerInvariantError(ForwardShadowLedgerError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ForwardShadowLedgerInvariantError(f"{name} must be timezone-aware.")
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
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _parse_datetime(value: Any, name: str) -> datetime:
    if isinstance(value, datetime):
        return _aware_utc(value, name)
    if not isinstance(value, str) or not value.strip():
        raise ForwardShadowLedgerInvariantError(f"{name} must be an ISO-8601 datetime.")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ForwardShadowLedgerInvariantError(f"{name} must be an ISO-8601 datetime.") from exc
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


@dataclass(frozen=True)
class OracleForwardShadowLedgerEntry:
    schema_version: str
    engine_id: str
    persisted_at: datetime
    source_report_hash: str
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
    horizons: tuple[Mapping[str, Any], ...]
    record_status: str
    reason_codes: tuple[str, ...]
    upstream_record_hash: str
    entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleForwardShadowLedgerReport:
    schema_version: str
    engine_id: str
    persisted_at: datetime
    ledger_directory: str
    source_report_hash: str
    source_record_count: int
    inserted_count: int
    existing_count: int
    conflict_count: int
    total_ledger_count: int
    inserted_evaluation_ids: tuple[str, ...]
    existing_evaluation_ids: tuple[str, ...]
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    analytics_artifact_persistence_allowed: bool
    raw_corpus_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleForwardShadowEvaluationLedger:
    read_only_corpus = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    analytics_artifact_persistence_allowed = True
    raw_corpus_mutation_allowed = False

    def __init__(self, *, ledger_directory: Path | str = DEFAULT_LEDGER_DIRECTORY) -> None:
        self._ledger_directory = Path(ledger_directory)
        if not str(self._ledger_directory).strip():
            raise ForwardShadowLedgerConfigurationError("ledger_directory cannot be empty.")

    @property
    def ledger_directory(self) -> Path:
        return self._ledger_directory

    def persist(
        self,
        *,
        evaluation_report: OracleForwardShadowEvaluationReport,
        persisted_at: Optional[datetime] = None,
    ) -> OracleForwardShadowLedgerReport:
        anchor = _aware_utc(persisted_at or datetime.now(timezone.utc), "persisted_at")
        self._verify_report(evaluation_report)
        entries_directory = self._ledger_directory / "entries"
        inserted: list[str] = []
        existing: list[str] = []
        conflicts: list[str] = []

        for record in evaluation_report.records:
            entry = self._entry_from_record(record, evaluation_report.report_hash, anchor)
            path = entries_directory / f"{entry.evaluation_id}.json"
            if path.exists():
                current = self._read_json(path)
                current_hash = current.get("entry_hash")
                if current_hash != entry.entry_hash:
                    conflicts.append(entry.evaluation_id)
                    continue
                existing.append(entry.evaluation_id)
                continue
            _atomic_json_write(path, entry.to_dict())
            inserted.append(entry.evaluation_id)

        if conflicts:
            raise ForwardShadowLedgerInvariantError(
                "Immutable ledger conflict for evaluation IDs: " + ", ".join(sorted(conflicts))
            )

        all_ids = tuple(sorted(path.stem for path in entries_directory.glob("*.json"))) if entries_directory.exists() else ()
        index_payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "updated_at": anchor,
            "entry_count": len(all_ids),
            "evaluation_ids": all_ids,
        }
        _atomic_json_write(self._ledger_directory / "current.json", {
            **index_payload, "index_hash": stable_hash(index_payload),
        })

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "persisted_at": anchor,
            "ledger_directory": str(self._ledger_directory),
            "source_report_hash": evaluation_report.report_hash,
            "source_record_count": len(evaluation_report.records),
            "inserted_count": len(inserted),
            "existing_count": len(existing),
            "conflict_count": 0,
            "total_ledger_count": len(all_ids),
            "inserted_evaluation_ids": tuple(sorted(inserted)),
            "existing_evaluation_ids": tuple(sorted(existing)),
            "read_only_corpus": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "trading_recommendations_allowed": False,
            "analytics_artifact_persistence_allowed": True,
            "raw_corpus_mutation_allowed": False,
        }
        report = OracleForwardShadowLedgerReport(**payload, report_hash=stable_hash(payload))
        _atomic_json_write(self._ledger_directory / "last_persistence_report.json", report.to_dict())
        return report

    def load_entries(self) -> tuple[OracleForwardShadowLedgerEntry, ...]:
        directory = self._ledger_directory / "entries"
        if not directory.exists():
            return ()
        entries = [self._entry_from_payload(self._read_json(path)) for path in sorted(directory.glob("*.json"))]
        return tuple(entries)

    @staticmethod
    def _verify_report(report: OracleForwardShadowEvaluationReport) -> None:
        if report.schema_version != "OIA-008" or report.engine_id != "OIA-008":
            raise ForwardShadowLedgerInvariantError("Unsupported OIA-008 evaluation report identity.")
        payload = dict(report.to_dict())
        digest = payload.pop("report_hash", None)
        if digest != upstream_stable_hash(payload):
            raise ForwardShadowLedgerInvariantError("OIA-008 evaluation report hash verification failed.")
        if report.outcome_measurement_allowed:
            raise ForwardShadowLedgerInvariantError("OIA-008 source must not contain measured outcomes.")

    @staticmethod
    def _entry_from_record(
        record: OracleForwardShadowEvaluationRecord,
        source_report_hash: str,
        persisted_at: datetime,
    ) -> OracleForwardShadowLedgerEntry:
        source = dict(record.to_dict())
        digest = source.pop("record_hash", None)
        if digest != upstream_stable_hash(source):
            raise ForwardShadowLedgerInvariantError(
                f"OIA-008 record hash verification failed for {record.evaluation_id}."
            )
        horizons = tuple(dict(item.to_dict()) for item in record.horizons)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "persisted_at": persisted_at,
            "source_report_hash": source_report_hash,
            "evaluation_id": record.evaluation_id,
            "market_id": record.market_id,
            "created_at": record.created_at,
            "admission_evaluated_at": record.admission_evaluated_at,
            "candidate_family": record.candidate_family,
            "research_direction": record.research_direction,
            "admission_score": record.admission_score,
            "entry_price_dollars": record.entry_price_dollars,
            "spread_to_price_ratio": record.spread_to_price_ratio,
            "observation_count": record.observation_count,
            "admission_hash": record.admission_hash,
            "horizons": horizons,
            "record_status": record.record_status,
            "reason_codes": record.reason_codes,
            "upstream_record_hash": record.record_hash,
        }
        return OracleForwardShadowLedgerEntry(**payload, entry_hash=stable_hash(payload))

    @staticmethod
    def _read_json(path: Path) -> Mapping[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ForwardShadowLedgerInvariantError(f"Unable to read ledger artifact: {path}") from exc
        if not isinstance(value, dict):
            raise ForwardShadowLedgerInvariantError(f"Ledger artifact is not a JSON object: {path}")
        return value

    @staticmethod
    def _entry_from_payload(payload: Mapping[str, Any]) -> OracleForwardShadowLedgerEntry:
        mutable = dict(payload)
        digest = mutable.pop("entry_hash", None)
        if digest != stable_hash(mutable):
            raise ForwardShadowLedgerInvariantError("Stored OIA-009 ledger entry hash verification failed.")
        mutable["persisted_at"] = _parse_datetime(mutable["persisted_at"], "persisted_at")
        mutable["created_at"] = _parse_datetime(mutable["created_at"], "created_at")
        mutable["admission_evaluated_at"] = _parse_datetime(
            mutable["admission_evaluated_at"], "admission_evaluated_at"
        )
        mutable["horizons"] = tuple(dict(item) for item in mutable["horizons"])
        mutable["reason_codes"] = tuple(mutable["reason_codes"])
        return OracleForwardShadowLedgerEntry(**mutable, entry_hash=digest)


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
        raise ForwardShadowLedgerConfigurationError("Set ORACLE_POSTGRESQL_URL or DATABASE_URL.")
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
            raise ForwardShadowLedgerConfigurationError("Install psycopg or psycopg2.") from exc


def format_report(report: OracleForwardShadowLedgerReport) -> str:
    return "\n".join([
        "=" * 110,
        "ORACLE FORWARD SHADOW EVALUATION LEDGER REPORT",
        "=" * 110,
        f"Persisted at: {report.persisted_at.isoformat()}",
        f"Ledger directory: {report.ledger_directory}",
        f"Source records: {report.source_record_count}",
        f"Inserted: {report.inserted_count} | existing: {report.existing_count} | total: {report.total_ledger_count}",
        f"Source OIA-008 report hash: {report.source_report_hash}",
        f"OIA-009 report hash: {report.report_hash}",
        "IMMUTABLE RESEARCH ARTIFACTS ONLY — CANONICAL CORPUS REMAINS READ-ONLY.",
        "NO SIGNALS / ALERTS / Q SERIES HANDOFF / EXECUTION.",
    ])


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Persist immutable OIA-008 forward-shadow records.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--ledger-directory", default=str(DEFAULT_LEDGER_DIRECTORY))
    parser.add_argument("--horizon-seconds", default="300,900,3600")
    parser.add_argument("--stale-after-seconds", type=int, default=300)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--market-limit", type=int, default=1000)
    parser.add_argument("--history-limit-per-market", type=int, default=1000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    horizons = tuple(int(part.strip()) for part in args.horizon_seconds.split(",") if part.strip())
    _load_env(Path(args.env_file))
    connection_factory: Callable[[], Any] = lambda: connect_postgresql(resolve_database_url())
    source_report = OracleForwardShadowEvaluationRecordBuilder(
        connection_factory=connection_factory,
        horizon_seconds=horizons,
        stale_after_seconds=args.stale_after_seconds,
        minimum_observations=args.minimum_observations,
        market_limit=args.market_limit,
        history_limit_per_market=args.history_limit_per_market,
    ).build()
    report = OracleForwardShadowEvaluationLedger(
        ledger_directory=Path(args.ledger_directory)
    ).persist(evaluation_report=source_report)
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
