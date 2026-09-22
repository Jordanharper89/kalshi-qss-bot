from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


MODULE_SOURCE = r'''"""
OIA-019
Oracle Qualified Research Work-Item Materialization Engine

Consumes the immutable OIA-018 qualified research queue admission report and
materializes deterministic, immutable research work items.

The engine:

- verifies the complete OIA-018 report and queue-record hash chain;
- preserves OIA-015 eligibility lineage;
- preserves OIA-016 ranking lineage;
- preserves OIA-017 tier lineage;
- preserves OIA-018 queue admission and queue ordering;
- materializes one work item for each queue-admitted research record;
- excludes capacity-deferred records without deleting their evidence;
- creates deterministic work-item identifiers;
- persists immutable, content-addressed work-item artifacts;
- remains permanently separated from signals, alerts, recommendations,
  Q Series handoffs, orders, funds, portfolio mutation, and execution.

OIA-019 creates research work definitions only.
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
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
)
from .oracle_qualified_research_queue_admission_gate import (
    CAPACITY_DEFERRED,
    DEFAULT_QUEUE_DIRECTORY,
    QUEUE_ADMITTED,
    QUEUE_POLICY_ID,
    stable_hash as queue_stable_hash,
)


SCHEMA_VERSION = "OIA-019"
ENGINE_ID = "OIA-019"

WORK_ITEM_POLICY_ID = (
    "oracle.qualified-research-work-item-materialization.v1"
)

READY = "ready"
NOT_MATERIALIZED = "not_materialized"

RESEARCH_OBJECTIVE = (
    "evaluate_qualified_component_with_additional_read_only_evidence"
)

READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
MARKET_ORDER_CREATION_ALLOWED = False
FUNDS_MOVEMENT_ALLOWED = False
PORTFOLIO_MUTATION_ALLOWED = False
WORK_ITEM_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_WORK_ITEM_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_work_items"
)


class QualifiedResearchWorkItemError(RuntimeError):
    """Base OIA-019 error."""


class QualifiedResearchWorkItemInvariantError(
    QualifiedResearchWorkItemError
):
    """Raised when an immutable upstream or local invariant fails."""


def _aware_utc(
    value: datetime,
    field_name: str,
) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise QualifiedResearchWorkItemInvariantError(
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
        return [
            _canonical(item)
            for item in value
        ]

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


def _freeze(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(value)
    )


def _decimal(
    value: Any,
    field_name: str,
) -> Decimal:
    try:
        result = Decimal(str(value))
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise QualifiedResearchWorkItemInvariantError(
            f"{field_name} must be a finite decimal."
        ) from exc

    if not result.is_finite():
        raise QualifiedResearchWorkItemInvariantError(
            f"{field_name} must be a finite decimal."
        )

    return result


def _valid_hash(
    value: Any,
) -> bool:
    if (
        not isinstance(value, str)
        or len(value) != 64
    ):
        return False

    try:
        int(value, 16)
    except ValueError:
        return False

    return True


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


def _work_item_id(
    *,
    source_queue_record_hash: str,
    queue_policy_id: str,
    work_item_policy_id: str,
) -> str:
    digest = stable_hash(
        {
            "source_queue_record_hash": (
                source_queue_record_hash
            ),
            "queue_policy_id": queue_policy_id,
            "work_item_policy_id": work_item_policy_id,
        }
    )

    return f"oia019-{digest[:32]}"


@dataclass(frozen=True)
class OracleQualifiedResearchWorkItem:
    work_item_id: str
    work_item_status: str
    queue_position: int
    source_rank: int
    dimension: str
    key: str
    tier: str
    priority_score: str
    decisive_count: int
    empirical_win_rate: str
    confidence_lower_bound: str
    calibration_quality: str
    reliability_quality: str
    resolution_quality: str
    sample_strength: str
    research_objective: str
    required_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    reason_codes: tuple[str, ...]
    source_eligibility_decision_hash: str
    source_ranking_record_hash: str
    source_tier_record_hash: str
    source_queue_record_hash: str
    work_item_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


@dataclass(frozen=True)
class OracleQualifiedResearchWorkItemReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    queue_directory: str
    work_item_directory: str
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    source_queue_record_count: int
    source_queue_admitted_count: int
    source_capacity_deferred_count: int
    work_item_count: int
    excluded_record_count: int
    tier_1_work_item_count: int
    tier_2_work_item_count: int
    tier_3_work_item_count: int
    work_items: tuple[
        OracleQualifiedResearchWorkItem,
        ...,
    ]
    excluded_queue_record_hashes: tuple[str, ...]
    source_queue_report_hash: str
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    work_item_artifact_persistence_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


class OracleQualifiedResearchWorkItemMaterializationEngine:
    """
    Deterministically materializes OIA-018 queue-admitted research work.

    Materialization policy v1:

    1. Verify the complete OIA-018 report and queue-record chain.
    2. Preserve ascending queue position.
    3. Materialize exactly one work item for each queue-admitted record.
    4. Never materialize capacity-deferred or queue-denied records.
    5. Preserve every upstream lineage hash.
    6. Create stable work-item identifiers from immutable source lineage.
    7. Define read-only research operations only.
    """

    read_only_corpus = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    source_mutation_allowed = False
    market_order_creation_allowed = False
    funds_movement_allowed = False
    portfolio_mutation_allowed = False
    work_item_artifact_persistence_allowed = True

    def __init__(
        self,
        *,
        queue_directory: Path | str = DEFAULT_QUEUE_DIRECTORY,
        work_item_directory: Path | str = (
            DEFAULT_WORK_ITEM_DIRECTORY
        ),
    ) -> None:
        self._queue_directory = Path(
            queue_directory
        )
        self._work_item_directory = Path(
            work_item_directory
        )

    def _load_queue_report(
        self,
    ) -> dict[str, Any]:
        current_path = (
            self._queue_directory
            / "current.json"
        )

        if not current_path.exists():
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 current queue report is missing: "
                f"{current_path}"
            )

        try:
            payload = json.loads(
                current_path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 queue report is not valid JSON: "
                f"{current_path}"
            ) from exc

        if not isinstance(payload, dict):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 queue report must be a JSON object."
            )

        report_hash = payload.pop(
            "report_hash",
            None,
        )

        if payload.get("schema_version") != "OIA-018":
            raise QualifiedResearchWorkItemInvariantError(
                "Unsupported OIA-018 schema version."
            )

        if payload.get("engine_id") != "OIA-018":
            raise QualifiedResearchWorkItemInvariantError(
                "Unsupported OIA-018 engine identity."
            )

        if (
            payload.get("ranking_policy_id")
            != RANKING_POLICY_ID
        ):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 ranking policy identity mismatch."
            )

        if (
            payload.get("tier_policy_id")
            != TIER_POLICY_ID
        ):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 tier policy identity mismatch."
            )

        if (
            payload.get("queue_policy_id")
            != QUEUE_POLICY_ID
        ):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 queue policy identity mismatch."
            )

        if (
            report_hash
            != queue_stable_hash(payload)
        ):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 queue report hash verification failed."
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 read-only corpus invariant failed."
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
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 safety boundary mismatch: "
                    f"{field_name}."
                )

        queue_capacity = int(
            payload.get(
                "queue_capacity",
                -1,
            )
        )

        if queue_capacity < 0:
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 queue capacity must be non-negative."
            )

        records = payload.get("records")

        if not isinstance(records, list):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 records must be a list."
            )

        source_count = int(
            payload.get(
                "source_tier_record_count",
                -1,
            )
        )

        if source_count != len(records):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 source tier count does not match records."
            )

        expected_admitted_count = int(
            payload.get(
                "queue_admitted_count",
                -1,
            )
        )

        expected_deferred_count = int(
            payload.get(
                "capacity_deferred_count",
                -1,
            )
        )

        expected_denied_count = int(
            payload.get(
                "queue_denied_count",
                -1,
            )
        )

        if (
            expected_admitted_count
            + expected_deferred_count
            + expected_denied_count
            != len(records)
        ):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 queue status counts do not match records."
            )

        verified_records: list[
            dict[str, Any]
        ] = []

        seen_source_ranks: set[int] = set()
        seen_queue_positions: set[int] = set()
        seen_identities: set[
            tuple[str, str]
        ] = set()
        seen_queue_hashes: set[str] = set()
        seen_tier_hashes: set[str] = set()
        seen_ranking_hashes: set[str] = set()
        seen_eligibility_hashes: set[str] = set()

        expected_next_queue_position = 1
        previous_source_rank = 0
        previous_priority_score: Decimal | None = None

        calculated_admitted_count = 0
        calculated_deferred_count = 0
        calculated_denied_count = 0

        for index, raw_record in enumerate(
            records,
            start=1,
        ):
            if not isinstance(raw_record, dict):
                raise QualifiedResearchWorkItemInvariantError(
                    f"OIA-018 record {index} must be an object."
                )

            record = dict(raw_record)

            queue_record_hash = record.pop(
                "queue_record_hash",
                None,
            )

            if (
                queue_record_hash
                != queue_stable_hash(record)
            ):
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 queue record hash verification "
                    f"failed at index {index}."
                )

            if not _valid_hash(queue_record_hash):
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 queue record hash is malformed."
                )

            source_rank = int(
                record.get(
                    "source_rank",
                    -1,
                )
            )

            if source_rank <= previous_source_rank:
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 source ranks must be strictly "
                    "ascending."
                )

            if source_rank in seen_source_ranks:
                raise QualifiedResearchWorkItemInvariantError(
                    "Duplicate OIA-018 source rank: "
                    f"{source_rank}"
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

            if not dimension or not key:
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 record identity cannot be empty."
                )

            identity = (
                dimension,
                key,
            )

            if identity in seen_identities:
                raise QualifiedResearchWorkItemInvariantError(
                    "Duplicate OIA-018 record identity: "
                    f"{identity!r}"
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
                raise QualifiedResearchWorkItemInvariantError(
                    f"Unsupported OIA-018 tier: {tier!r}"
                )

            queue_status = str(
                record.get(
                    "queue_status",
                    "",
                )
            )

            if queue_status not in {
                QUEUE_ADMITTED,
                CAPACITY_DEFERRED,
                "queue_denied",
            }:
                raise QualifiedResearchWorkItemInvariantError(
                    "Unsupported OIA-018 queue status: "
                    f"{queue_status!r}"
                )

            queue_position_raw = record.get(
                "queue_position"
            )

            if queue_status == QUEUE_ADMITTED:
                calculated_admitted_count += 1

                if queue_position_raw is None:
                    raise QualifiedResearchWorkItemInvariantError(
                        "Queue-admitted records require a "
                        "queue position."
                    )

                queue_position = int(
                    queue_position_raw
                )

                if (
                    queue_position
                    != expected_next_queue_position
                ):
                    raise QualifiedResearchWorkItemInvariantError(
                        "OIA-018 queue positions must be "
                        "contiguous and ordered from one."
                    )

                if queue_position > queue_capacity:
                    raise QualifiedResearchWorkItemInvariantError(
                        "OIA-018 queue position exceeds queue "
                        "capacity."
                    )

                if queue_position in seen_queue_positions:
                    raise QualifiedResearchWorkItemInvariantError(
                        "Duplicate OIA-018 queue position: "
                        f"{queue_position}"
                    )

                seen_queue_positions.add(
                    queue_position
                )

                expected_next_queue_position += 1

            elif queue_status == CAPACITY_DEFERRED:
                calculated_deferred_count += 1

                if queue_position_raw is not None:
                    raise QualifiedResearchWorkItemInvariantError(
                        "Capacity-deferred records cannot have "
                        "a queue position."
                    )

            else:
                calculated_denied_count += 1

                if queue_position_raw is not None:
                    raise QualifiedResearchWorkItemInvariantError(
                        "Queue-denied records cannot have a "
                        "queue position."
                    )

            if (
                record.get("ranking_policy_id")
                != RANKING_POLICY_ID
            ):
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 record ranking policy mismatch."
                )

            if (
                record.get("tier_policy_id")
                != TIER_POLICY_ID
            ):
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 record tier policy mismatch."
                )

            if (
                record.get("queue_policy_id")
                != QUEUE_POLICY_ID
            ):
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 record queue policy mismatch."
                )

            priority_score = _decimal(
                record.get("priority_score"),
                "priority_score",
            )

            if (
                priority_score < Decimal("0")
                or priority_score > Decimal("100")
            ):
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 priority score must be between "
                    "zero and one hundred."
                )

            if (
                previous_priority_score is not None
                and priority_score
                > previous_priority_score
            ):
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 records are not ordered by "
                    "descending priority score."
                )

            decisive_count = int(
                record.get(
                    "decisive_count",
                    -1,
                )
            )

            if decisive_count < 0:
                raise QualifiedResearchWorkItemInvariantError(
                    "OIA-018 decisive count must be "
                    "non-negative."
                )

            lineage_fields = (
                "source_eligibility_decision_hash",
                "source_ranking_record_hash",
                "source_tier_record_hash",
            )

            for field_name in lineage_fields:
                if not _valid_hash(
                    record.get(field_name)
                ):
                    raise QualifiedResearchWorkItemInvariantError(
                        f"OIA-018 {field_name} is malformed."
                    )

            source_eligibility_hash = str(
                record[
                    "source_eligibility_decision_hash"
                ]
            )

            source_ranking_hash = str(
                record[
                    "source_ranking_record_hash"
                ]
            )

            source_tier_hash = str(
                record[
                    "source_tier_record_hash"
                ]
            )

            if queue_record_hash in seen_queue_hashes:
                raise QualifiedResearchWorkItemInvariantError(
                    "Duplicate OIA-018 queue record hash."
                )

            if source_tier_hash in seen_tier_hashes:
                raise QualifiedResearchWorkItemInvariantError(
                    "Duplicate OIA-018 tier lineage hash."
                )

            if source_ranking_hash in seen_ranking_hashes:
                raise QualifiedResearchWorkItemInvariantError(
                    "Duplicate OIA-018 ranking lineage hash."
                )

            if (
                source_eligibility_hash
                in seen_eligibility_hashes
            ):
                raise QualifiedResearchWorkItemInvariantError(
                    "Duplicate OIA-018 eligibility lineage hash."
                )

            seen_source_ranks.add(
                source_rank
            )
            seen_identities.add(
                identity
            )
            seen_queue_hashes.add(
                queue_record_hash
            )
            seen_tier_hashes.add(
                source_tier_hash
            )
            seen_ranking_hashes.add(
                source_ranking_hash
            )
            seen_eligibility_hashes.add(
                source_eligibility_hash
            )

            previous_source_rank = source_rank
            previous_priority_score = priority_score

            record["queue_record_hash"] = (
                queue_record_hash
            )

            verified_records.append(
                record
            )

        if (
            calculated_admitted_count
            != expected_admitted_count
        ):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 admitted count does not match records."
            )

        if (
            calculated_deferred_count
            != expected_deferred_count
        ):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 deferred count does not match records."
            )

        if (
            calculated_denied_count
            != expected_denied_count
        ):
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 denied count does not match records."
            )

        if calculated_admitted_count > queue_capacity:
            raise QualifiedResearchWorkItemInvariantError(
                "OIA-018 admitted count exceeds queue capacity."
            )

        payload["records"] = verified_records
        payload["report_hash"] = report_hash

        return payload

    @staticmethod
    def _required_operations(
        tier: str,
    ) -> tuple[str, ...]:
        base = (
            "load_verified_source_lineage",
            "read_additional_canonical_market_evidence",
            "compute_deterministic_research_metrics",
            "record_replayable_research_evidence",
            "produce_content_addressed_research_result",
        )

        if tier == TIER_1:
            return base + (
                "apply_highest_priority_research_depth",
            )

        if tier == TIER_2:
            return base + (
                "apply_standard_priority_research_depth",
            )

        return base + (
            "apply_baseline_priority_research_depth",
        )

    @staticmethod
    def _prohibited_operations() -> tuple[str, ...]:
        return (
            "create_trading_signal",
            "create_trading_recommendation",
            "publish_operator_alert",
            "handoff_to_qseries_execution",
            "create_market_order",
            "modify_market_order",
            "cancel_market_order",
            "move_funds",
            "mutate_portfolio",
            "mutate_source_corpus",
        )

    @staticmethod
    def _completion_requirements() -> tuple[str, ...]:
        return (
            "source_lineage_hashes_verified",
            "research_inputs_content_addressed",
            "research_method_policy_identified",
            "research_output_deterministically_hashed",
            "replay_produces_identical_output",
            "no_prohibited_operation_requested",
        )

    @staticmethod
    def _reason_codes(
        tier: str,
    ) -> tuple[str, ...]:
        return (
            "oia_018_queue_record_verified",
            "queue_admission_preserved",
            "queue_position_preserved",
            "upstream_lineage_preserved",
            f"{tier}_research_work_materialized",
            "deterministic_work_item_id_created",
            "research_work_definition_only",
        )

    def materialize(
        self,
        *,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchWorkItemReport:
        generated_at = _aware_utc(
            generated_at
            or datetime.now(timezone.utc),
            "generated_at",
        )

        source_report = self._load_queue_report()

        source_records = source_report[
            "records"
        ]

        admitted_records = [
            record
            for record in source_records
            if (
                record["queue_status"]
                == QUEUE_ADMITTED
            )
        ]

        excluded_records = [
            record
            for record in source_records
            if (
                record["queue_status"]
                != QUEUE_ADMITTED
            )
        ]

        admitted_records.sort(
            key=lambda record: (
                int(record["queue_position"]),
                int(record["source_rank"]),
                str(record["dimension"]),
                str(record["key"]),
            )
        )

        work_items: list[
            OracleQualifiedResearchWorkItem
        ] = []

        seen_work_item_ids: set[str] = set()
        seen_work_item_hashes: set[str] = set()

        for source_record in admitted_records:
            queue_position = int(
                source_record["queue_position"]
            )

            source_queue_record_hash = str(
                source_record[
                    "queue_record_hash"
                ]
            )

            work_item_id = _work_item_id(
                source_queue_record_hash=(
                    source_queue_record_hash
                ),
                queue_policy_id=QUEUE_POLICY_ID,
                work_item_policy_id=(
                    WORK_ITEM_POLICY_ID
                ),
            )

            if work_item_id in seen_work_item_ids:
                raise QualifiedResearchWorkItemInvariantError(
                    "Duplicate deterministic work-item ID."
                )

            tier = str(
                source_record["tier"]
            )

            body = {
                "work_item_id": work_item_id,
                "work_item_status": READY,
                "queue_position": queue_position,
                "source_rank": int(
                    source_record["source_rank"]
                ),
                "dimension": str(
                    source_record["dimension"]
                ),
                "key": str(
                    source_record["key"]
                ),
                "tier": tier,
                "priority_score": str(
                    source_record["priority_score"]
                ),
                "decisive_count": int(
                    source_record["decisive_count"]
                ),
                "empirical_win_rate": str(
                    source_record[
                        "empirical_win_rate"
                    ]
                ),
                "confidence_lower_bound": str(
                    source_record[
                        "confidence_lower_bound"
                    ]
                ),
                "calibration_quality": str(
                    source_record[
                        "calibration_quality"
                    ]
                ),
                "reliability_quality": str(
                    source_record[
                        "reliability_quality"
                    ]
                ),
                "resolution_quality": str(
                    source_record[
                        "resolution_quality"
                    ]
                ),
                "sample_strength": str(
                    source_record[
                        "sample_strength"
                    ]
                ),
                "research_objective": (
                    RESEARCH_OBJECTIVE
                ),
                "required_operations": (
                    self._required_operations(tier)
                ),
                "prohibited_operations": (
                    self._prohibited_operations()
                ),
                "completion_requirements": (
                    self._completion_requirements()
                ),
                "ranking_policy_id": str(
                    source_record[
                        "ranking_policy_id"
                    ]
                ),
                "tier_policy_id": str(
                    source_record[
                        "tier_policy_id"
                    ]
                ),
                "queue_policy_id": str(
                    source_record[
                        "queue_policy_id"
                    ]
                ),
                "work_item_policy_id": (
                    WORK_ITEM_POLICY_ID
                ),
                "reason_codes": (
                    self._reason_codes(tier)
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
                    source_record[
                        "source_tier_record_hash"
                    ]
                ),
                "source_queue_record_hash": (
                    source_queue_record_hash
                ),
            }

            work_item_hash = stable_hash(
                body
            )

            if work_item_hash in seen_work_item_hashes:
                raise QualifiedResearchWorkItemInvariantError(
                    "Duplicate deterministic work-item hash."
                )

            work_items.append(
                OracleQualifiedResearchWorkItem(
                    **body,
                    work_item_hash=work_item_hash,
                )
            )

            seen_work_item_ids.add(
                work_item_id
            )
            seen_work_item_hashes.add(
                work_item_hash
            )

        excluded_queue_record_hashes = tuple(
            sorted(
                str(record["queue_record_hash"])
                for record in excluded_records
            )
        )

        tier_1_work_item_count = sum(
            item.tier == TIER_1
            for item in work_items
        )

        tier_2_work_item_count = sum(
            item.tier == TIER_2
            for item in work_items
        )

        tier_3_work_item_count = sum(
            item.tier == TIER_3
            for item in work_items
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "queue_directory": str(
                self._queue_directory
            ),
            "work_item_directory": str(
                self._work_item_directory
            ),
            "ranking_policy_id": (
                RANKING_POLICY_ID
            ),
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": (
                WORK_ITEM_POLICY_ID
            ),
            "source_queue_record_count": len(
                source_records
            ),
            "source_queue_admitted_count": len(
                admitted_records
            ),
            "source_capacity_deferred_count": sum(
                record["queue_status"]
                == CAPACITY_DEFERRED
                for record in source_records
            ),
            "work_item_count": len(
                work_items
            ),
            "excluded_record_count": len(
                excluded_records
            ),
            "tier_1_work_item_count": (
                tier_1_work_item_count
            ),
            "tier_2_work_item_count": (
                tier_2_work_item_count
            ),
            "tier_3_work_item_count": (
                tier_3_work_item_count
            ),
            "work_items": tuple(
                work_items
            ),
            "excluded_queue_record_hashes": (
                excluded_queue_record_hashes
            ),
            "source_queue_report_hash": str(
                source_report["report_hash"]
            ),
            "read_only_corpus": (
                READ_ONLY_CORPUS
            ),
            "execution_allowed": (
                EXECUTION_ALLOWED
            ),
            "alerts_allowed": (
                ALERTS_ALLOWED
            ),
            "qseries_handoff_allowed": (
                QSERIES_HANDOFF_ALLOWED
            ),
            "signals_allowed": (
                SIGNALS_ALLOWED
            ),
            "trading_recommendations_allowed": (
                TRADING_RECOMMENDATIONS_ALLOWED
            ),
            "source_mutation_allowed": (
                SOURCE_MUTATION_ALLOWED
            ),
            "market_order_creation_allowed": (
                MARKET_ORDER_CREATION_ALLOWED
            ),
            "funds_movement_allowed": (
                FUNDS_MOVEMENT_ALLOWED
            ),
            "portfolio_mutation_allowed": (
                PORTFOLIO_MUTATION_ALLOWED
            ),
            "work_item_artifact_persistence_allowed": (
                WORK_ITEM_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }

        report = (
            OracleQualifiedResearchWorkItemReport(
                **body,
                report_hash=stable_hash(body),
            )
        )

        if persist:
            report_payload = dict(
                report.to_dict()
            )

            _atomic_write(
                self._work_item_directory
                / "current.json",
                report_payload,
            )

            _atomic_write(
                self._work_item_directory
                / "reports"
                / (
                    "work-item-report-"
                    f"{report.report_hash}.json"
                ),
                report_payload,
            )

            for work_item in report.work_items:
                _atomic_write(
                    self._work_item_directory
                    / "items"
                    / (
                        f"{work_item.work_item_id}.json"
                    ),
                    dict(work_item.to_dict()),
                )

        return report


def format_report(
    report: OracleQualifiedResearchWorkItemReport,
) -> str:
    lines = [
        "=" * 158,
        (
            "ORACLE QUALIFIED RESEARCH "
            "WORK-ITEM MATERIALIZATION"
        ),
        "=" * 158,
        (
            "Generated at:      "
            f"{report.generated_at.isoformat()}"
        ),
        (
            "Ranking policy:    "
            f"{report.ranking_policy_id}"
        ),
        (
            "Tier policy:       "
            f"{report.tier_policy_id}"
        ),
        (
            "Queue policy:      "
            f"{report.queue_policy_id}"
        ),
        (
            "Work-item policy:  "
            f"{report.work_item_policy_id}"
        ),
        (
            "Source records: "
            f"{report.source_queue_record_count} | "
            "queue admitted="
            f"{report.source_queue_admitted_count} | "
            "capacity deferred="
            f"{report.source_capacity_deferred_count} | "
            "materialized="
            f"{report.work_item_count} | "
            "excluded="
            f"{report.excluded_record_count}"
        ),
        (
            "Work items by tier: "
            f"tier_1={report.tier_1_work_item_count} | "
            f"tier_2={report.tier_2_work_item_count} | "
            f"tier_3={report.tier_3_work_item_count}"
        ),
        "-" * 158,
        (
            f"{'QUEUE':>5}  "
            f"{'RANK':>5}  "
            f"{'TIER':10} "
            f"{'STATUS':8} "
            f"{'DIMENSION':34} "
            f"{'KEY':34} "
            f"{'N':>7} "
            f"{'SCORE':>12} "
            f"{'WORK ITEM ID':40}"
        ),
    ]

    for item in report.work_items:
        lines.append(
            f"{item.queue_position:>5}  "
            f"{item.source_rank:>5}  "
            f"{item.tier:10} "
            f"{item.work_item_status:8} "
            f"{item.dimension[:34]:34} "
            f"{item.key[:34]:34} "
            f"{item.decisive_count:>7} "
            f"{item.priority_score:>12} "
            f"{item.work_item_id:40}"
        )

    if not report.work_items:
        lines.append(
            "No OIA-018 queue-admitted records were "
            "available for work-item materialization."
        )

    lines.extend(
        [
            "-" * 158,
            f"Report hash: {report.report_hash}",
            (
                "RESEARCH WORK DEFINITIONS ONLY — "
                "NO SIGNALS, ALERTS, RECOMMENDATIONS, "
                "QSERIES HANDOFFS, ORDERS, FUNDS MOVEMENT, "
                "PORTFOLIO MUTATION, OR EXECUTION"
            ),
        ]
    )

    return "\n".join(lines)


def main(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "OIA-019 qualified research work-item "
            "materialization engine"
        )
    )

    parser.add_argument(
        "--queue-directory",
        default=str(
            DEFAULT_QUEUE_DIRECTORY
        ),
    )

    parser.add_argument(
        "--work-item-directory",
        default=str(
            DEFAULT_WORK_ITEM_DIRECTORY
        ),
    )

    parser.add_argument(
        "--no-persist",
        action="store_true",
    )

    args = parser.parse_args(
        argv
    )

    report = (
        OracleQualifiedResearchWorkItemMaterializationEngine(
            queue_directory=(
                args.queue_directory
            ),
            work_item_directory=(
                args.work_item_directory
            ),
        ).materialize(
            persist=not args.no_persist,
        )
    )

    print(
        format_report(report)
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
'''


TEST_SOURCE = r'''from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import (
    RANKING_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import (
    ADMITTED,
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import (
    CAPACITY_DEFERRED,
    QUEUE_ADMITTED,
    QUEUE_POLICY_ID,
    stable_hash as queue_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_work_item_materialization_engine import (
    ENGINE_ID,
    READY,
    RESEARCH_OBJECTIVE,
    SCHEMA_VERSION,
    WORK_ITEM_POLICY_ID,
    OracleQualifiedResearchWorkItemMaterializationEngine,
    QualifiedResearchWorkItemInvariantError,
    format_report,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    7,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_queue_record(
    *,
    source_rank: int,
    queue_position: int | None,
    key: str,
    tier: str,
    score: str,
    queue_status: str,
    decisive_count: int,
) -> dict:
    body = {
        "source_rank": source_rank,
        "queue_position": queue_position,
        "dimension": (
            "candidate_family_horizon"
        ),
        "key": key,
        "tier": tier,
        "tier_status": ADMITTED,
        "queue_status": queue_status,
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
        "queue_policy_id": QUEUE_POLICY_ID,
        "reason_codes": [
            "oia_017_tier_record_verified",
            "source_rank_preserved",
            "source_tier_preserved",
            "deterministic_queue_policy_applied",
            "research_scheduling_only",
        ],
        "source_eligibility_decision_hash": (
            f"{source_rank:064x}"[-64:]
        ),
        "source_ranking_record_hash": (
            f"{source_rank + 100:064x}"[-64:]
        ),
        "source_tier_record_hash": (
            f"{source_rank + 200:064x}"[-64:]
        ),
    }

    return {
        **body,
        "queue_record_hash": queue_hash(body),
    }


def write_queue_report(
    directory: Path,
    records: list[dict],
    *,
    queue_capacity: int,
) -> dict:
    admitted_count = sum(
        record["queue_status"]
        == QUEUE_ADMITTED
        for record in records
    )

    deferred_count = sum(
        record["queue_status"]
        == CAPACITY_DEFERRED
        for record in records
    )

    body = {
        "schema_version": "OIA-018",
        "engine_id": "OIA-018",
        "generated_at": NOW,
        "tier_directory": "tiers",
        "queue_directory": str(directory),
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "queue_capacity": queue_capacity,
        "source_tier_record_count": len(records),
        "queue_admitted_count": admitted_count,
        "capacity_deferred_count": deferred_count,
        "queue_denied_count": 0,
        "tier_1_admitted_count": sum(
            record["queue_status"]
            == QUEUE_ADMITTED
            and record["tier"] == TIER_1
            for record in records
        ),
        "tier_2_admitted_count": sum(
            record["queue_status"]
            == QUEUE_ADMITTED
            and record["tier"] == TIER_2
            for record in records
        ),
        "tier_3_admitted_count": sum(
            record["queue_status"]
            == QUEUE_ADMITTED
            and record["tier"] == TIER_3
            for record in records
        ),
        "records": records,
        "source_tier_report_hash": "f" * 64,
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "queue_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "report_hash": queue_hash(body),
    }

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        directory
        / "current.json"
    ).write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            default=lambda value: (
                value.isoformat()
            ),
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def run_test() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)

        queue_directory = (
            root
            / "queue"
        )

        work_item_directory = (
            root
            / "work-items"
        )

        source_records = [
            make_queue_record(
                source_rank=1,
                queue_position=1,
                key="momentum|300",
                tier=TIER_1,
                score="82.50000000",
                queue_status=QUEUE_ADMITTED,
                decisive_count=700,
            ),
            make_queue_record(
                source_rank=2,
                queue_position=2,
                key="reversion|900",
                tier=TIER_2,
                score="63.25000000",
                queue_status=QUEUE_ADMITTED,
                decisive_count=500,
            ),
            make_queue_record(
                source_rank=3,
                queue_position=None,
                key="momentum|3600",
                tier=TIER_3,
                score="49.75000000",
                queue_status=CAPACITY_DEFERRED,
                decisive_count=350,
            ),
        ]

        source_report = write_queue_report(
            queue_directory,
            source_records,
            queue_capacity=2,
        )

        engine = (
            OracleQualifiedResearchWorkItemMaterializationEngine(
                queue_directory=(
                    queue_directory
                ),
                work_item_directory=(
                    work_item_directory
                ),
            )
        )

        report = engine.materialize(
            generated_at=NOW,
            persist=True,
        )

        assert (
            report.schema_version
            == SCHEMA_VERSION
            == "OIA-019"
        )

        assert (
            report.engine_id
            == ENGINE_ID
            == "OIA-019"
        )

        assert (
            report.ranking_policy_id
            == RANKING_POLICY_ID
        )

        assert (
            report.tier_policy_id
            == TIER_POLICY_ID
        )

        assert (
            report.queue_policy_id
            == QUEUE_POLICY_ID
        )

        assert (
            report.work_item_policy_id
            == WORK_ITEM_POLICY_ID
        )

        assert (
            report.source_queue_record_count
            == 3
        )

        assert (
            report.source_queue_admitted_count
            == 2
        )

        assert (
            report.source_capacity_deferred_count
            == 1
        )

        assert (
            report.work_item_count
            == 2
        )

        assert (
            report.excluded_record_count
            == 1
        )

        assert (
            report.tier_1_work_item_count
            == 1
        )

        assert (
            report.tier_2_work_item_count
            == 1
        )

        assert (
            report.tier_3_work_item_count
            == 0
        )

        first = report.work_items[0]
        second = report.work_items[1]

        assert first.queue_position == 1
        assert first.source_rank == 1
        assert first.tier == TIER_1
        assert first.key == "momentum|300"
        assert first.work_item_status == READY

        assert second.queue_position == 2
        assert second.source_rank == 2
        assert second.tier == TIER_2
        assert second.key == "reversion|900"
        assert second.work_item_status == READY

        assert first.research_objective == (
            RESEARCH_OBJECTIVE
        )

        assert (
            first.source_queue_record_hash
            == source_records[0][
                "queue_record_hash"
            ]
        )

        assert (
            second.source_queue_record_hash
            == source_records[1][
                "queue_record_hash"
            ]
        )

        assert (
            source_records[2][
                "queue_record_hash"
            ]
            in report.excluded_queue_record_hashes
        )

        assert (
            len(
                report.excluded_queue_record_hashes
            )
            == 1
        )

        assert (
            report.source_queue_report_hash
            == source_report["report_hash"]
        )

        for work_item in report.work_items:
            payload = dict(
                work_item.to_dict()
            )

            digest = payload.pop(
                "work_item_hash"
            )

            assert digest == stable_hash(
                payload
            )

            assert work_item.work_item_id.startswith(
                "oia019-"
            )

            assert (
                "oia_018_queue_record_verified"
                in work_item.reason_codes
            )

            assert (
                "queue_position_preserved"
                in work_item.reason_codes
            )

            assert (
                "create_market_order"
                in work_item.prohibited_operations
            )

            assert (
                "handoff_to_qseries_execution"
                in work_item.prohibited_operations
            )

            assert (
                "research_output_deterministically_hashed"
                in work_item.completion_requirements
            )

        report_payload = dict(
            report.to_dict()
        )

        report_digest = report_payload.pop(
            "report_hash"
        )

        assert report_digest == stable_hash(
            report_payload
        )

        assert report.read_only_corpus
        assert not report.execution_allowed
        assert not report.alerts_allowed
        assert not report.qseries_handoff_allowed
        assert not report.signals_allowed
        assert (
            not report.trading_recommendations_allowed
        )
        assert not report.source_mutation_allowed
        assert (
            not report.market_order_creation_allowed
        )
        assert not report.funds_movement_allowed
        assert (
            not report.portfolio_mutation_allowed
        )
        assert (
            report.work_item_artifact_persistence_allowed
        )

        current_path = (
            work_item_directory
            / "current.json"
        )

        immutable_report_path = (
            work_item_directory
            / "reports"
            / (
                "work-item-report-"
                f"{report.report_hash}.json"
            )
        )

        first_item_path = (
            work_item_directory
            / "items"
            / f"{first.work_item_id}.json"
        )

        second_item_path = (
            work_item_directory
            / "items"
            / f"{second.work_item_id}.json"
        )

        assert current_path.exists()
        assert immutable_report_path.exists()
        assert first_item_path.exists()
        assert second_item_path.exists()

        first_current_bytes = (
            current_path.read_bytes()
        )

        first_report_bytes = (
            immutable_report_path.read_bytes()
        )

        first_item_bytes = (
            first_item_path.read_bytes()
        )

        replay = engine.materialize(
            generated_at=NOW,
            persist=True,
        )

        assert (
            replay.report_hash
            == report.report_hash
        )

        assert (
            replay.work_items[0].work_item_id
            == first.work_item_id
        )

        assert (
            replay.work_items[0].work_item_hash
            == first.work_item_hash
        )

        assert (
            current_path.read_bytes()
            == first_current_bytes
        )

        assert (
            immutable_report_path.read_bytes()
            == first_report_bytes
        )

        assert (
            first_item_path.read_bytes()
            == first_item_bytes
        )

        rendered = format_report(
            report
        )

        assert (
            "ORACLE QUALIFIED RESEARCH "
            "WORK-ITEM MATERIALIZATION"
            in rendered
        )

        assert "momentum|300" in rendered
        assert "oia019-" in rendered
        assert "NO SIGNALS" in rendered

        tampered = json.loads(
            (
                queue_directory
                / "current.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        tampered["records"][0][
            "priority_score"
        ] = "1.00000000"

        (
            queue_directory
            / "current.json"
        ).write_text(
            json.dumps(
                tampered,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        try:
            engine.materialize(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchWorkItemInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-018 queue report "
                "was not rejected."
            )

        write_queue_report(
            queue_directory,
            [
                make_queue_record(
                    source_rank=1,
                    queue_position=2,
                    key="invalid-position",
                    tier=TIER_1,
                    score="80.00000000",
                    queue_status=QUEUE_ADMITTED,
                    decisive_count=500,
                ),
            ],
            queue_capacity=2,
        )

        try:
            engine.materialize(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchWorkItemInvariantError:
            pass
        else:
            raise AssertionError(
                "Non-contiguous OIA-018 queue position "
                "was not rejected."
            )

    print(
        "[PASS] OIA-019 Oracle Qualified Research "
        "Work-Item Materialization Engine"
    )


if __name__ == "__main__":
    run_test()
'''


INIT_IMPORT_BLOCK = r'''
from .oracle_qualified_research_work_item_materialization_engine import (
    NOT_MATERIALIZED,
    READY,
    RESEARCH_OBJECTIVE,
    WORK_ITEM_POLICY_ID,
    OracleQualifiedResearchWorkItem,
    OracleQualifiedResearchWorkItemMaterializationEngine,
    OracleQualifiedResearchWorkItemReport,
)
'''


INIT_EXPORTS = (
    "NOT_MATERIALIZED",
    "READY",
    "RESEARCH_OBJECTIVE",
    "WORK_ITEM_POLICY_ID",
    "OracleQualifiedResearchWorkItem",
    "OracleQualifiedResearchWorkItemMaterializationEngine",
    "OracleQualifiedResearchWorkItemReport",
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


def verify_oia_018_contract(
    path: Path,
) -> None:
    if not path.exists():
        raise SystemExit(
            "[FAIL] OIA-018 production module is missing. "
            "Install and pass OIA-018 first."
        )

    text = path.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        'SCHEMA_VERSION = "OIA-018"',
        'ENGINE_ID = "OIA-018"',
        (
            'QUEUE_POLICY_ID = '
            '"oracle.qualified-research-queue-admission.v1"'
        ),
        'QUEUE_ADMITTED = "queue_admitted"',
        (
            'CAPACITY_DEFERRED = '
            '"capacity_deferred"'
        ),
        "DEFAULT_QUEUE_DIRECTORY",
        (
            "class "
            "OracleQualifiedResearchQueueAdmissionRecord:"
        ),
        (
            "class "
            "OracleQualifiedResearchQueueAdmissionReport:"
        ),
        (
            "class "
            "OracleQualifiedResearchQueueAdmissionGate:"
        ),
        "source_eligibility_decision_hash",
        "source_ranking_record_hash",
        "source_tier_record_hash",
        "queue_record_hash",
        "report_hash",
        "queue_position",
        "queue_status",
        "queue_artifact_persistence_allowed",
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
            "[FAIL] Actual OIA-018 production "
            f"contract mismatch: {missing}"
        )


def update_package_initializer(
    path: Path,
) -> None:
    if not path.exists():
        raise SystemExit(
            "[FAIL] Analytics package initializer "
            f"is missing: {path}"
        )

    original = path.read_text(
        encoding="utf-8"
    )

    updated = original

    import_marker = (
        "from "
        ".oracle_qualified_research_work_item_"
        "materialization_engine import"
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
        / "oracle_qualified_research_queue_admission_gate.py"
    )

    production_path = (
        analytics_directory
        / (
            "oracle_qualified_research_work_item_"
            "materialization_engine.py"
        )
    )

    test_path = (
        root
        / (
            "test_oia_019_oracle_qualified_research_"
            "work_item_materialization_engine.py"
        )
    )

    initializer_path = (
        analytics_directory
        / "__init__.py"
    )

    print("========================================")
    print(" OIA-019 INSTALLER")
    print(" QUALIFIED RESEARCH WORK ITEMS")
    print(" DETERMINISTIC MATERIALIZATION ENGINE")
    print("========================================")

    verify_oia_018_contract(
        dependency_path
    )

    print(
        "[OK] Actual OIA-018 queue admission "
        "contract verified"
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
        "[OK] OIA-019 production, package, "
        "and test syntax verified"
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
        "[OK] OIA-019 test executed successfully"
    )

    print(
        "[DONE] OIA-019 Oracle Qualified Research "
        "Work-Item Materialization Engine installed"
    )

    print()

    print(
        "Materialize current qualified research "
        "work items with:"
    )

    print(
        "python -m "
        "qseries_v2.oracle_intelligence.analytics."
        "oracle_qualified_research_work_item_"
        "materialization_engine"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )