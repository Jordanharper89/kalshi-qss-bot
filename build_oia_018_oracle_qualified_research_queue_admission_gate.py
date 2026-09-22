from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


MODULE_SOURCE = r'''"""
OIA-018
Oracle Qualified Research Queue Admission Gate

Consumes the immutable OIA-017 qualified research priority tier report and
creates a deterministic research-only queue admission report.

The gate:

- verifies the complete OIA-017 report and tier-record hash chain;
- preserves OIA-016 rank and OIA-017 tier lineage;
- admits verified tiered research records according to fixed queue capacity;
- defers excess records deterministically without discarding evidence;
- assigns stable queue positions;
- emits immutable, content-addressed queue admission artifacts;
- remains permanently separated from trading signals, alerts,
  recommendations, Q Series handoffs, orders, funds, and execution.

OIA-018 is a research scheduling admission boundary only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .oracle_qualified_research_priority_ranking_engine import (
    RANKING_POLICY_ID,
)
from .oracle_qualified_research_priority_tier_assignment_gate import (
    ADMITTED as TIER_ADMITTED,
    DEFAULT_TIER_DIRECTORY,
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
    stable_hash as tier_stable_hash,
)


SCHEMA_VERSION = "OIA-018"
ENGINE_ID = "OIA-018"

QUEUE_POLICY_ID = "oracle.qualified-research-queue-admission.v1"

QUEUE_ADMITTED = "queue_admitted"
CAPACITY_DEFERRED = "capacity_deferred"
QUEUE_DENIED = "queue_denied"

DEFAULT_QUEUE_CAPACITY = 100

READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
QUEUE_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_QUEUE_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_queue"
)


class QualifiedResearchQueueAdmissionError(RuntimeError):
    """Base OIA-018 error."""


class QualifiedResearchQueueAdmissionInvariantError(
    QualifiedResearchQueueAdmissionError
):
    """Raised when an immutable upstream or local invariant fails."""


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise QualifiedResearchQueueAdmissionInvariantError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]

    if isinstance(value, datetime):
        return _aware_utc(
            value,
            "datetime",
        ).isoformat()

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


def _decimal(value: Any, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise QualifiedResearchQueueAdmissionInvariantError(
            f"{field_name} must be a finite decimal."
        ) from exc

    if not result.is_finite():
        raise QualifiedResearchQueueAdmissionInvariantError(
            f"{field_name} must be a finite decimal."
        )

    return result


def _atomic_write(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rendered = (
        json.dumps(
            _canonical(payload),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )

    temporary_path = Path(handle.name)

    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(
            temporary_path,
            path,
        )
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@dataclass(frozen=True)
class OracleQualifiedResearchQueueAdmissionRecord:
    source_rank: int
    queue_position: int | None
    dimension: str
    key: str
    tier: str
    tier_status: str
    queue_status: str
    priority_score: str
    decisive_count: int
    empirical_win_rate: str
    confidence_lower_bound: str
    calibration_quality: str
    reliability_quality: str
    resolution_quality: str
    sample_strength: str
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    reason_codes: tuple[str, ...]
    source_eligibility_decision_hash: str
    source_ranking_record_hash: str
    source_tier_record_hash: str
    queue_record_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


@dataclass(frozen=True)
class OracleQualifiedResearchQueueAdmissionReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    tier_directory: str
    queue_directory: str
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    queue_capacity: int
    source_tier_record_count: int
    queue_admitted_count: int
    capacity_deferred_count: int
    queue_denied_count: int
    tier_1_admitted_count: int
    tier_2_admitted_count: int
    tier_3_admitted_count: int
    records: tuple[
        OracleQualifiedResearchQueueAdmissionRecord,
        ...,
    ]
    source_tier_report_hash: str
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    queue_artifact_persistence_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


class OracleQualifiedResearchQueueAdmissionGate:
    """
    Deterministic queue admission over verified OIA-017 tier records.

    Queue policy v1:

    1. Preserve ascending OIA-016 source rank.
    2. Preserve OIA-017 tier assignment.
    3. Admit the first ``queue_capacity`` valid tier records.
    4. Mark remaining valid records as capacity deferred.
    5. Never discard or mutate deferred evidence.
    6. Never create trading, alert, recommendation, or execution authority.
    """

    read_only_corpus = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    source_mutation_allowed = False
    queue_artifact_persistence_allowed = True

    def __init__(
        self,
        *,
        tier_directory: Path | str = DEFAULT_TIER_DIRECTORY,
        queue_directory: Path | str = DEFAULT_QUEUE_DIRECTORY,
        queue_capacity: int = DEFAULT_QUEUE_CAPACITY,
    ) -> None:
        self._tier_directory = Path(tier_directory)
        self._queue_directory = Path(queue_directory)

        if isinstance(queue_capacity, bool):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "queue_capacity must be an integer."
            )

        try:
            normalized_capacity = int(queue_capacity)
        except (TypeError, ValueError) as exc:
            raise QualifiedResearchQueueAdmissionInvariantError(
                "queue_capacity must be an integer."
            ) from exc

        if normalized_capacity < 0:
            raise QualifiedResearchQueueAdmissionInvariantError(
                "queue_capacity must be non-negative."
            )

        self._queue_capacity = normalized_capacity

    def _load_tier_report(self) -> dict[str, Any]:
        current_path = self._tier_directory / "current.json"

        if not current_path.exists():
            raise QualifiedResearchQueueAdmissionInvariantError(
                f"OIA-017 current tier report is missing: {current_path}"
            )

        try:
            payload = json.loads(
                current_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise QualifiedResearchQueueAdmissionInvariantError(
                f"OIA-017 tier report is not valid JSON: {current_path}"
            ) from exc

        if not isinstance(payload, dict):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 tier report must be a JSON object."
            )

        report_hash = payload.pop(
            "report_hash",
            None,
        )

        if payload.get("schema_version") != "OIA-017":
            raise QualifiedResearchQueueAdmissionInvariantError(
                "Unsupported OIA-017 schema version."
            )

        if payload.get("engine_id") != "OIA-017":
            raise QualifiedResearchQueueAdmissionInvariantError(
                "Unsupported OIA-017 engine identity."
            )

        if payload.get("ranking_policy_id") != RANKING_POLICY_ID:
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 ranking policy identity mismatch."
            )

        if payload.get("tier_policy_id") != TIER_POLICY_ID:
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 tier policy identity mismatch."
            )

        if report_hash != tier_stable_hash(payload):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 tier report hash verification failed."
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 read-only corpus invariant failed."
            )

        forbidden_true_fields = (
            "execution_allowed",
            "alerts_allowed",
            "qseries_handoff_allowed",
            "signals_allowed",
            "trading_recommendations_allowed",
            "source_mutation_allowed",
        )

        for field_name in forbidden_true_fields:
            if payload.get(field_name) is not False:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    f"OIA-017 safety boundary mismatch: {field_name}."
                )

        records = payload.get("records")

        if not isinstance(records, list):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 records must be a list."
            )

        expected_count = int(
            payload.get(
                "source_ranking_count",
                -1,
            )
        )

        if expected_count != len(records):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 source ranking count does not match records."
            )

        admitted_count = int(
            payload.get(
                "admitted_count",
                -1,
            )
        )

        denied_count = int(
            payload.get(
                "denied_count",
                -1,
            )
        )

        if admitted_count + denied_count != len(records):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 admission counts do not match records."
            )

        verified_records: list[dict[str, Any]] = []

        seen_ranks: set[int] = set()
        seen_identities: set[tuple[str, str]] = set()
        seen_tier_hashes: set[str] = set()
        seen_ranking_hashes: set[str] = set()

        previous_score: Decimal | None = None

        for index, raw_record in enumerate(
            records,
            start=1,
        ):
            if not isinstance(raw_record, dict):
                raise QualifiedResearchQueueAdmissionInvariantError(
                    f"OIA-017 record {index} must be an object."
                )

            record = dict(raw_record)

            tier_record_hash = record.pop(
                "tier_record_hash",
                None,
            )

            if tier_record_hash != tier_stable_hash(record):
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "OIA-017 tier record hash verification failed "
                    f"at index {index}."
                )

            rank = int(
                record.get(
                    "rank",
                    -1,
                )
            )

            if rank != index:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "OIA-017 ranks must be contiguous and ordered "
                    "starting at one."
                )

            if rank in seen_ranks:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    f"Duplicate OIA-017 rank: {rank}"
                )

            dimension = str(
                record.get(
                    "dimension",
                    "",
                )
            )
            key = str(
                record.get(
                    "key",
                    "",
                )
            )

            identity = (
                dimension,
                key,
            )

            if not dimension or not key:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "OIA-017 record identity cannot be empty."
                )

            if identity in seen_identities:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    f"Duplicate OIA-017 record identity: {identity!r}"
                )

            tier = str(
                record.get(
                    "tier",
                    "",
                )
            )

            if tier not in {
                TIER_1,
                TIER_2,
                TIER_3,
            }:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    f"Unsupported OIA-017 tier: {tier!r}"
                )

            if record.get("tier_status") != TIER_ADMITTED:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "Only OIA-017 admitted tier records may enter "
                    "the OIA-018 queue admission boundary."
                )

            if record.get("ranking_policy_id") != RANKING_POLICY_ID:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "OIA-017 record ranking policy mismatch."
                )

            if record.get("tier_policy_id") != TIER_POLICY_ID:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "OIA-017 record tier policy mismatch."
                )

            priority_score = _decimal(
                record.get("priority_score"),
                "priority_score",
            )

            if (
                priority_score < Decimal("0")
                or priority_score > Decimal("100")
            ):
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "OIA-017 priority score must be between 0 and 100."
                )

            if (
                previous_score is not None
                and priority_score > previous_score
            ):
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "OIA-017 records are not ordered by descending "
                    "priority score."
                )

            decisive_count = int(
                record.get(
                    "decisive_count",
                    -1,
                )
            )

            if decisive_count < 0:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "OIA-017 decisive count must be non-negative."
                )

            source_eligibility_hash = record.get(
                "source_eligibility_decision_hash"
            )
            source_ranking_hash = record.get(
                "source_ranking_record_hash"
            )

            for field_name, hash_value in (
                (
                    "source_eligibility_decision_hash",
                    source_eligibility_hash,
                ),
                (
                    "source_ranking_record_hash",
                    source_ranking_hash,
                ),
                (
                    "tier_record_hash",
                    tier_record_hash,
                ),
            ):
                if (
                    not isinstance(hash_value, str)
                    or len(hash_value) != 64
                ):
                    raise QualifiedResearchQueueAdmissionInvariantError(
                        f"OIA-017 {field_name} is malformed."
                    )

            if tier_record_hash in seen_tier_hashes:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    f"Duplicate OIA-017 tier hash: {tier_record_hash}"
                )

            if source_ranking_hash in seen_ranking_hashes:
                raise QualifiedResearchQueueAdmissionInvariantError(
                    "Duplicate OIA-017 source ranking hash: "
                    f"{source_ranking_hash}"
                )

            seen_ranks.add(rank)
            seen_identities.add(identity)
            seen_tier_hashes.add(tier_record_hash)
            seen_ranking_hashes.add(source_ranking_hash)

            previous_score = priority_score

            record["tier_record_hash"] = tier_record_hash
            verified_records.append(record)

        calculated_tier_1_count = sum(
            record["tier"] == TIER_1
            for record in verified_records
        )
        calculated_tier_2_count = sum(
            record["tier"] == TIER_2
            for record in verified_records
        )
        calculated_tier_3_count = sum(
            record["tier"] == TIER_3
            for record in verified_records
        )

        if calculated_tier_1_count != int(
            payload.get(
                "tier_1_count",
                -1,
            )
        ):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 Tier 1 count does not match records."
            )

        if calculated_tier_2_count != int(
            payload.get(
                "tier_2_count",
                -1,
            )
        ):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 Tier 2 count does not match records."
            )

        if calculated_tier_3_count != int(
            payload.get(
                "tier_3_count",
                -1,
            )
        ):
            raise QualifiedResearchQueueAdmissionInvariantError(
                "OIA-017 Tier 3 count does not match records."
            )

        payload["records"] = verified_records
        payload["report_hash"] = report_hash

        return payload

    @staticmethod
    def _reason_codes(
        *,
        queue_status: str,
        tier: str,
    ) -> tuple[str, ...]:
        common = (
            "oia_017_tier_record_verified",
            "source_rank_preserved",
            "source_tier_preserved",
            "deterministic_queue_policy_applied",
            "research_scheduling_only",
        )

        if queue_status == QUEUE_ADMITTED:
            return common + (
                f"{tier}_research_admitted",
                "queue_capacity_available",
            )

        if queue_status == CAPACITY_DEFERRED:
            return common + (
                f"{tier}_research_capacity_deferred",
                "queue_capacity_exhausted",
                "research_evidence_preserved",
            )

        return common + (
            "queue_admission_denied",
        )

    def evaluate(
        self,
        *,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchQueueAdmissionReport:
        generated_at = _aware_utc(
            generated_at or datetime.now(timezone.utc),
            "generated_at",
        )

        source_report = self._load_tier_report()
        source_records = source_report["records"]

        output_records: list[
            OracleQualifiedResearchQueueAdmissionRecord
        ] = []

        next_queue_position = 1

        for source_record in source_records:
            if next_queue_position <= self._queue_capacity:
                queue_status = QUEUE_ADMITTED
                queue_position: int | None = next_queue_position
                next_queue_position += 1
            else:
                queue_status = CAPACITY_DEFERRED
                queue_position = None

            tier = str(source_record["tier"])

            body = {
                "source_rank": int(
                    source_record["rank"]
                ),
                "queue_position": queue_position,
                "dimension": str(
                    source_record["dimension"]
                ),
                "key": str(
                    source_record["key"]
                ),
                "tier": tier,
                "tier_status": str(
                    source_record["tier_status"]
                ),
                "queue_status": queue_status,
                "priority_score": str(
                    source_record["priority_score"]
                ),
                "decisive_count": int(
                    source_record["decisive_count"]
                ),
                "empirical_win_rate": str(
                    source_record["empirical_win_rate"]
                ),
                "confidence_lower_bound": str(
                    source_record["confidence_lower_bound"]
                ),
                "calibration_quality": str(
                    source_record["calibration_quality"]
                ),
                "reliability_quality": str(
                    source_record["reliability_quality"]
                ),
                "resolution_quality": str(
                    source_record["resolution_quality"]
                ),
                "sample_strength": str(
                    source_record["sample_strength"]
                ),
                "ranking_policy_id": str(
                    source_record["ranking_policy_id"]
                ),
                "tier_policy_id": str(
                    source_record["tier_policy_id"]
                ),
                "queue_policy_id": QUEUE_POLICY_ID,
                "reason_codes": self._reason_codes(
                    queue_status=queue_status,
                    tier=tier,
                ),
                "source_eligibility_decision_hash": str(
                    source_record[
                        "source_eligibility_decision_hash"
                    ]
                ),
                "source_ranking_record_hash": str(
                    source_record[
                        "source_ranking_record_hash"
                    ]
                ),
                "source_tier_record_hash": str(
                    source_record["tier_record_hash"]
                ),
            }

            output_records.append(
                OracleQualifiedResearchQueueAdmissionRecord(
                    **body,
                    queue_record_hash=stable_hash(body),
                )
            )

        queue_admitted_count = sum(
            record.queue_status == QUEUE_ADMITTED
            for record in output_records
        )

        capacity_deferred_count = sum(
            record.queue_status == CAPACITY_DEFERRED
            for record in output_records
        )

        queue_denied_count = sum(
            record.queue_status == QUEUE_DENIED
            for record in output_records
        )

        tier_1_admitted_count = sum(
            record.queue_status == QUEUE_ADMITTED
            and record.tier == TIER_1
            for record in output_records
        )

        tier_2_admitted_count = sum(
            record.queue_status == QUEUE_ADMITTED
            and record.tier == TIER_2
            for record in output_records
        )

        tier_3_admitted_count = sum(
            record.queue_status == QUEUE_ADMITTED
            and record.tier == TIER_3
            for record in output_records
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "tier_directory": str(self._tier_directory),
            "queue_directory": str(self._queue_directory),
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "queue_capacity": self._queue_capacity,
            "source_tier_record_count": len(source_records),
            "queue_admitted_count": queue_admitted_count,
            "capacity_deferred_count": capacity_deferred_count,
            "queue_denied_count": queue_denied_count,
            "tier_1_admitted_count": tier_1_admitted_count,
            "tier_2_admitted_count": tier_2_admitted_count,
            "tier_3_admitted_count": tier_3_admitted_count,
            "records": tuple(output_records),
            "source_tier_report_hash": str(
                source_report["report_hash"]
            ),
            "read_only_corpus": READ_ONLY_CORPUS,
            "execution_allowed": EXECUTION_ALLOWED,
            "alerts_allowed": ALERTS_ALLOWED,
            "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,
            "signals_allowed": SIGNALS_ALLOWED,
            "trading_recommendations_allowed": (
                TRADING_RECOMMENDATIONS_ALLOWED
            ),
            "source_mutation_allowed": SOURCE_MUTATION_ALLOWED,
            "queue_artifact_persistence_allowed": (
                QUEUE_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }

        report = OracleQualifiedResearchQueueAdmissionReport(
            **body,
            report_hash=stable_hash(body),
        )

        if persist:
            payload = dict(report.to_dict())

            _atomic_write(
                self._queue_directory / "current.json",
                payload,
            )

            _atomic_write(
                self._queue_directory
                / "reports"
                / f"queue-report-{report.report_hash}.json",
                payload,
            )

        return report


def format_report(
    report: OracleQualifiedResearchQueueAdmissionReport,
) -> str:
    lines = [
        "=" * 150,
        "ORACLE QUALIFIED RESEARCH QUEUE ADMISSION",
        "=" * 150,
        f"Generated at:    {report.generated_at.isoformat()}",
        f"Ranking policy:  {report.ranking_policy_id}",
        f"Tier policy:     {report.tier_policy_id}",
        f"Queue policy:    {report.queue_policy_id}",
        f"Queue capacity:  {report.queue_capacity}",
        (
            "Records: "
            f"{report.source_tier_record_count} | "
            f"admitted={report.queue_admitted_count} | "
            f"deferred={report.capacity_deferred_count} | "
            f"denied={report.queue_denied_count}"
        ),
        (
            "Admitted by tier: "
            f"tier_1={report.tier_1_admitted_count} | "
            f"tier_2={report.tier_2_admitted_count} | "
            f"tier_3={report.tier_3_admitted_count}"
        ),
        "-" * 150,
        (
            f"{'RANK':>4}  "
            f"{'QUEUE':>5}  "
            f"{'STATUS':18} "
            f"{'TIER':10} "
            f"{'DIMENSION':34} "
            f"{'KEY':34} "
            f"{'N':>7} "
            f"{'SCORE':>12}"
        ),
    ]

    for record in report.records:
        queue_position = (
            str(record.queue_position)
            if record.queue_position is not None
            else "-"
        )

        lines.append(
            f"{record.source_rank:>4}  "
            f"{queue_position:>5}  "
            f"{record.queue_status:18} "
            f"{record.tier:10} "
            f"{record.dimension[:34]:34} "
            f"{record.key[:34]:34} "
            f"{record.decisive_count:>7} "
            f"{record.priority_score:>12}"
        )

    if not report.records:
        lines.append(
            "No verified OIA-017 tier records are currently available."
        )

    lines.extend(
        [
            "-" * 150,
            f"Report hash: {report.report_hash}",
            (
                "RESEARCH QUEUE ADMISSION ONLY — "
                "NO SIGNALS, ALERTS, RECOMMENDATIONS, HANDOFFS, "
                "ORDERS, FUNDS MOVEMENT, PORTFOLIO MUTATION, "
                "OR EXECUTION"
            ),
        ]
    )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "OIA-018 qualified research queue admission gate"
        )
    )

    parser.add_argument(
        "--tier-directory",
        default=str(DEFAULT_TIER_DIRECTORY),
    )

    parser.add_argument(
        "--queue-directory",
        default=str(DEFAULT_QUEUE_DIRECTORY),
    )

    parser.add_argument(
        "--queue-capacity",
        type=int,
        default=DEFAULT_QUEUE_CAPACITY,
    )

    parser.add_argument(
        "--no-persist",
        action="store_true",
    )

    args = parser.parse_args(argv)

    report = OracleQualifiedResearchQueueAdmissionGate(
        tier_directory=args.tier_directory,
        queue_directory=args.queue_directory,
        queue_capacity=args.queue_capacity,
    ).evaluate(
        persist=not args.no_persist,
    )

    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


TEST_SOURCE = r'''from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import (
    QUALIFIED,
    RANKING_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import (
    ADMITTED,
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
    stable_hash as tier_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import (
    CAPACITY_DEFERRED,
    ENGINE_ID,
    QUEUE_ADMITTED,
    QUEUE_POLICY_ID,
    SCHEMA_VERSION,
    OracleQualifiedResearchQueueAdmissionGate,
    QualifiedResearchQueueAdmissionInvariantError,
    format_report,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    6,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_tier_record(
    *,
    rank: int,
    key: str,
    score: str,
    tier: str,
    decisive_count: int,
) -> dict:
    body = {
        "rank": rank,
        "dimension": "candidate_family_horizon",
        "key": key,
        "qualification_status": QUALIFIED,
        "tier_status": ADMITTED,
        "tier": tier,
        "priority_score": score,
        "decisive_count": decisive_count,
        "empirical_win_rate": "0.65000000",
        "confidence_lower_bound": "0.59000000",
        "calibration_quality": "0.80000000",
        "reliability_quality": "0.80000000",
        "resolution_quality": "0.40000000",
        "sample_strength": "1.00000000",
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "reason_codes": [
            "oia_016_qualified_ranking_verified",
            "source_rank_preserved",
            "deterministic_tier_policy_applied",
            "research_classification_only",
        ],
        "source_eligibility_decision_hash": (
            f"{rank:064x}"[-64:]
        ),
        "source_ranking_record_hash": (
            f"{rank + 100:064x}"[-64:]
        ),
    }

    return {
        **body,
        "tier_record_hash": tier_hash(body),
    }


def write_tier_report(
    directory: Path,
    records: list[dict],
) -> dict:
    body = {
        "schema_version": "OIA-017",
        "engine_id": "OIA-017",
        "generated_at": NOW,
        "ranking_directory": "ranking",
        "tier_directory": str(directory),
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "source_ranking_count": len(records),
        "admitted_count": len(records),
        "denied_count": 0,
        "tier_1_count": sum(
            record["tier"] == TIER_1
            for record in records
        ),
        "tier_2_count": sum(
            record["tier"] == TIER_2
            for record in records
        ),
        "tier_3_count": sum(
            record["tier"] == TIER_3
            for record in records
        ),
        "records": records,
        "source_ranking_report_hash": "f" * 64,
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "tier_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "report_hash": tier_hash(body),
    }

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (directory / "current.json").write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            default=lambda value: value.isoformat(),
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def run_test() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)

        tier_directory = root / "tiers"
        queue_directory = root / "queue"

        source_records = [
            make_tier_record(
                rank=1,
                key="momentum|300",
                score="82.50000000",
                tier=TIER_1,
                decisive_count=700,
            ),
            make_tier_record(
                rank=2,
                key="reversion|900",
                score="63.25000000",
                tier=TIER_2,
                decisive_count=500,
            ),
            make_tier_record(
                rank=3,
                key="momentum|3600",
                score="49.75000000",
                tier=TIER_3,
                decisive_count=350,
            ),
        ]

        source_report = write_tier_report(
            tier_directory,
            source_records,
        )

        gate = OracleQualifiedResearchQueueAdmissionGate(
            tier_directory=tier_directory,
            queue_directory=queue_directory,
            queue_capacity=2,
        )

        report = gate.evaluate(
            generated_at=NOW,
            persist=True,
        )

        assert report.schema_version == SCHEMA_VERSION == "OIA-018"
        assert report.engine_id == ENGINE_ID == "OIA-018"
        assert report.ranking_policy_id == RANKING_POLICY_ID
        assert report.tier_policy_id == TIER_POLICY_ID
        assert report.queue_policy_id == QUEUE_POLICY_ID

        assert report.queue_capacity == 2
        assert report.source_tier_record_count == 3
        assert report.queue_admitted_count == 2
        assert report.capacity_deferred_count == 1
        assert report.queue_denied_count == 0

        assert report.tier_1_admitted_count == 1
        assert report.tier_2_admitted_count == 1
        assert report.tier_3_admitted_count == 0

        assert report.records[0].source_rank == 1
        assert report.records[0].queue_position == 1
        assert report.records[0].queue_status == QUEUE_ADMITTED
        assert report.records[0].tier == TIER_1
        assert report.records[0].key == "momentum|300"

        assert report.records[1].source_rank == 2
        assert report.records[1].queue_position == 2
        assert report.records[1].queue_status == QUEUE_ADMITTED
        assert report.records[1].tier == TIER_2
        assert report.records[1].key == "reversion|900"

        assert report.records[2].source_rank == 3
        assert report.records[2].queue_position is None
        assert (
            report.records[2].queue_status
            == CAPACITY_DEFERRED
        )
        assert report.records[2].tier == TIER_3
        assert report.records[2].key == "momentum|3600"

        assert [
            record.source_tier_record_hash
            for record in report.records
        ] == [
            record["tier_record_hash"]
            for record in source_records
        ]

        assert [
            record.source_ranking_record_hash
            for record in report.records
        ] == [
            record["source_ranking_record_hash"]
            for record in source_records
        ]

        assert [
            record.source_eligibility_decision_hash
            for record in report.records
        ] == [
            record["source_eligibility_decision_hash"]
            for record in source_records
        ]

        assert (
            report.source_tier_report_hash
            == source_report["report_hash"]
        )

        for record in report.records:
            payload = dict(record.to_dict())
            digest = payload.pop("queue_record_hash")

            assert digest == stable_hash(payload)
            assert (
                "oia_017_tier_record_verified"
                in record.reason_codes
            )
            assert (
                "source_rank_preserved"
                in record.reason_codes
            )
            assert (
                "source_tier_preserved"
                in record.reason_codes
            )
            assert (
                "research_scheduling_only"
                in record.reason_codes
            )

        report_payload = dict(report.to_dict())
        report_digest = report_payload.pop("report_hash")

        assert report_digest == stable_hash(report_payload)

        assert report.read_only_corpus
        assert not report.execution_allowed
        assert not report.alerts_allowed
        assert not report.qseries_handoff_allowed
        assert not report.signals_allowed
        assert not report.trading_recommendations_allowed
        assert not report.source_mutation_allowed
        assert report.queue_artifact_persistence_allowed

        current_path = queue_directory / "current.json"

        immutable_path = (
            queue_directory
            / "reports"
            / f"queue-report-{report.report_hash}.json"
        )

        assert current_path.exists()
        assert immutable_path.exists()

        first_current_bytes = current_path.read_bytes()
        first_immutable_bytes = immutable_path.read_bytes()

        replay = gate.evaluate(
            generated_at=NOW,
            persist=True,
        )

        assert replay.report_hash == report.report_hash
        assert current_path.read_bytes() == first_current_bytes
        assert immutable_path.read_bytes() == first_immutable_bytes

        rendered = format_report(report)

        assert (
            "ORACLE QUALIFIED RESEARCH QUEUE ADMISSION"
            in rendered
        )
        assert "momentum|300" in rendered
        assert "capacity_deferred" in rendered
        assert "NO SIGNALS" in rendered

        zero_capacity_gate = (
            OracleQualifiedResearchQueueAdmissionGate(
                tier_directory=tier_directory,
                queue_directory=root / "zero-capacity",
                queue_capacity=0,
            )
        )

        zero_capacity_report = zero_capacity_gate.evaluate(
            generated_at=NOW,
            persist=False,
        )

        assert zero_capacity_report.queue_admitted_count == 0
        assert zero_capacity_report.capacity_deferred_count == 3

        tampered = json.loads(
            (tier_directory / "current.json").read_text(
                encoding="utf-8"
            )
        )

        tampered["records"][0]["priority_score"] = "1.00000000"

        (tier_directory / "current.json").write_text(
            json.dumps(
                tampered,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        try:
            gate.evaluate(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchQueueAdmissionInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-017 tier report was not rejected."
            )

        write_tier_report(
            tier_directory,
            [
                make_tier_record(
                    rank=1,
                    key="first",
                    score="60.00000000",
                    tier=TIER_2,
                    decisive_count=400,
                ),
                make_tier_record(
                    rank=2,
                    key="second",
                    score="80.00000000",
                    tier=TIER_1,
                    decisive_count=500,
                ),
            ],
        )

        try:
            gate.evaluate(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchQueueAdmissionInvariantError:
            pass
        else:
            raise AssertionError(
                "Out-of-order OIA-017 records were not rejected."
            )

    print(
        "[PASS] OIA-018 Oracle Qualified Research "
        "Queue Admission Gate"
    )


if __name__ == "__main__":
    run_test()
'''


INIT_IMPORT_BLOCK = r'''
from .oracle_qualified_research_queue_admission_gate import (
    CAPACITY_DEFERRED,
    QUEUE_ADMITTED,
    QUEUE_DENIED,
    QUEUE_POLICY_ID,
    OracleQualifiedResearchQueueAdmissionGate,
    OracleQualifiedResearchQueueAdmissionRecord,
    OracleQualifiedResearchQueueAdmissionReport,
)
'''


INIT_EXPORTS = (
    "CAPACITY_DEFERRED",
    "QUEUE_ADMITTED",
    "QUEUE_DENIED",
    "QUEUE_POLICY_ID",
    "OracleQualifiedResearchQueueAdmissionGate",
    "OracleQualifiedResearchQueueAdmissionRecord",
    "OracleQualifiedResearchQueueAdmissionReport",
)


def write_full_replacement(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] FULL REPLACEMENT: {path.resolve()}"
    )


def verify_oia_017_contract(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            "[FAIL] OIA-017 production module is missing. "
            "Install and pass OIA-017 first."
        )

    text = path.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        'SCHEMA_VERSION = "OIA-017"',
        'ENGINE_ID = "OIA-017"',
        (
            'TIER_POLICY_ID = '
            '"oracle.qualified-research-priority-tier.v1"'
        ),
        'TIER_1 = "tier_1"',
        'TIER_2 = "tier_2"',
        'TIER_3 = "tier_3"',
        'ADMITTED = "admitted"',
        "DEFAULT_TIER_DIRECTORY",
        (
            "class "
            "OracleQualifiedResearchPriorityTierRecord:"
        ),
        (
            "class "
            "OracleQualifiedResearchPriorityTierReport:"
        ),
        (
            "class "
            "OracleQualifiedResearchPriorityTierAssignmentGate:"
        ),
        "source_eligibility_decision_hash",
        "source_ranking_record_hash",
        "tier_record_hash",
        "report_hash",
        "tier_artifact_persistence_allowed",
        "execution_allowed",
        "alerts_allowed",
        "qseries_handoff_allowed",
    )

    missing = [
        token
        for token in required_tokens
        if token not in text
    ]

    if missing:
        raise SystemExit(
            "[FAIL] Actual OIA-017 production contract mismatch: "
            f"{missing}"
        )


def update_package_initializer(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            f"[FAIL] Analytics package initializer is missing: {path}"
        )

    original = path.read_text(
        encoding="utf-8"
    )

    updated = original

    import_marker = (
        "from "
        ".oracle_qualified_research_queue_admission_gate "
        "import"
    )

    if import_marker not in updated:
        updated = (
            updated.rstrip()
            + "\n\n"
            + INIT_IMPORT_BLOCK.strip()
            + "\n"
        )

    if "__all__" in updated:
        missing_exports = [
            name
            for name in INIT_EXPORTS
            if (
                f'"{name}"' not in updated
                and f"'{name}'" not in updated
            )
        ]

        if missing_exports:
            export_lines = "\n".join(
                f'    "{name}",'
                for name in missing_exports
            )

            updated = (
                updated.rstrip()
                + "\n\n__all__ = [\n"
                + export_lines
                + "\n] + __all__\n"
            )

    if updated == original:
        print(
            "[OK] PACKAGE EXPORTS ALREADY PRESENT: "
            f"{path.resolve()}"
        )
        return

    path.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] PACKAGE EXPORT UPDATE: {path.resolve()}"
    )


def main() -> int:
    root = Path.cwd()

    analytics_directory = (
        root
        / "qseries_v2"
        / "oracle_intelligence"
        / "analytics"
    )

    dependency_path = (
        analytics_directory
        / "oracle_qualified_research_priority_tier_assignment_gate.py"
    )

    production_path = (
        analytics_directory
        / "oracle_qualified_research_queue_admission_gate.py"
    )

    test_path = (
        root
        / "test_oia_018_oracle_qualified_research_queue_admission_gate.py"
    )

    initializer_path = (
        analytics_directory
        / "__init__.py"
    )

    print("========================================")
    print(" OIA-018 INSTALLER")
    print(" QUALIFIED RESEARCH QUEUE")
    print(" DETERMINISTIC ADMISSION GATE")
    print("========================================")

    verify_oia_017_contract(
        dependency_path
    )

    print(
        "[OK] Actual OIA-017 tier assignment contract verified"
    )

    write_full_replacement(
        production_path,
        MODULE_SOURCE,
    )

    write_full_replacement(
        test_path,
        TEST_SOURCE,
    )

    update_package_initializer(
        initializer_path
    )

    ast.parse(
        MODULE_SOURCE,
        filename=str(production_path),
    )

    ast.parse(
        TEST_SOURCE,
        filename=str(test_path),
    )

    ast.parse(
        initializer_path.read_text(
            encoding="utf-8"
        ),
        filename=str(initializer_path),
    )

    print(
        "[OK] OIA-018 production, package, and test syntax verified"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(test_path),
        ],
        cwd=root,
        check=False,
    )

    if completed.returncode != 0:
        raise SystemExit(
            completed.returncode
        )

    print(
        "[OK] OIA-018 test executed successfully"
    )

    print(
        "[DONE] OIA-018 Oracle Qualified Research "
        "Queue Admission Gate installed"
    )

    print()

    print(
        "Run the current research queue admission with:"
    )

    print(
        "python -m "
        "qseries_v2.oracle_intelligence.analytics."
        "oracle_qualified_research_queue_admission_gate"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())