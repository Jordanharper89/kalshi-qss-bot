from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


MODULE_SOURCE = r'''"""
OIA-020
Oracle Qualified Research Dispatch Manifest Builder

Consumes the immutable OIA-019 qualified research work-item report and creates
a deterministic dispatch manifest for future read-only research workers.

The builder:

- verifies the complete OIA-019 report and work-item hash chain;
- preserves OIA-015 eligibility lineage;
- preserves OIA-016 ranking lineage;
- preserves OIA-017 tier lineage;
- preserves OIA-018 queue lineage;
- preserves OIA-019 work-item identity and ordering;
- creates deterministic dispatch batches;
- records every dispatched work item in exact queue order;
- emits immutable, content-addressed dispatch artifacts;
- does not execute research;
- does not create signals, alerts, recommendations, Q Series handoffs,
  market orders, funds movement, portfolio mutation, or source mutation.

OIA-020 defines a research dispatch manifest only.
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
    QUEUE_POLICY_ID,
)
from .oracle_qualified_research_work_item_materialization_engine import (
    DEFAULT_WORK_ITEM_DIRECTORY,
    READY,
    RESEARCH_OBJECTIVE,
    WORK_ITEM_POLICY_ID,
    stable_hash as work_item_stable_hash,
)


SCHEMA_VERSION = "OIA-020"
ENGINE_ID = "OIA-020"

DISPATCH_POLICY_ID = (
    "oracle.qualified-research-dispatch-manifest.v1"
)

MANIFEST_READY = "manifest_ready"
DISPATCH_READY = "dispatch_ready"

DEFAULT_BATCH_SIZE = 25

READ_ONLY_CORPUS = True
RESEARCH_EXECUTION_ALLOWED = False
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
MARKET_ORDER_CREATION_ALLOWED = False
FUNDS_MOVEMENT_ALLOWED = False
PORTFOLIO_MUTATION_ALLOWED = False
DISPATCH_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_DISPATCH_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_dispatch"
)


class QualifiedResearchDispatchManifestError(RuntimeError):
    """Base OIA-020 error."""


class QualifiedResearchDispatchManifestInvariantError(
    QualifiedResearchDispatchManifestError
):
    """Raised when an upstream or local immutable invariant fails."""


def _aware_utc(
    value: datetime,
    field_name: str,
) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise QualifiedResearchDispatchManifestInvariantError(
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
        raise QualifiedResearchDispatchManifestInvariantError(
            f"{field_name} must be a finite decimal."
        ) from exc

    if not result.is_finite():
        raise QualifiedResearchDispatchManifestInvariantError(
            f"{field_name} must be a finite decimal."
        )

    return result


def _valid_hash(value: Any) -> bool:
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


def _dispatch_manifest_id(
    *,
    source_work_item_report_hash: str,
    batch_size: int,
) -> str:
    digest = stable_hash(
        {
            "source_work_item_report_hash": (
                source_work_item_report_hash
            ),
            "batch_size": batch_size,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
        }
    )

    return f"oia020-manifest-{digest[:32]}"


def _dispatch_batch_id(
    *,
    manifest_id: str,
    batch_number: int,
    work_item_hashes: tuple[str, ...],
) -> str:
    digest = stable_hash(
        {
            "manifest_id": manifest_id,
            "batch_number": batch_number,
            "work_item_hashes": work_item_hashes,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
        }
    )

    return f"oia020-batch-{digest[:32]}"


@dataclass(frozen=True)
class OracleQualifiedResearchDispatchEntry:
    dispatch_sequence: int
    batch_number: int
    batch_position: int
    work_item_id: str
    work_item_status: str
    queue_position: int
    source_rank: int
    dimension: str
    key: str
    tier: str
    priority_score: str
    research_objective: str
    required_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    dispatch_status: str
    reason_codes: tuple[str, ...]
    source_eligibility_decision_hash: str
    source_ranking_record_hash: str
    source_tier_record_hash: str
    source_queue_record_hash: str
    source_work_item_hash: str
    dispatch_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


@dataclass(frozen=True)
class OracleQualifiedResearchDispatchBatch:
    manifest_id: str
    batch_id: str
    batch_number: int
    batch_size_limit: int
    entry_count: int
    first_dispatch_sequence: int
    last_dispatch_sequence: int
    first_queue_position: int
    last_queue_position: int
    dispatch_entry_hashes: tuple[str, ...]
    source_work_item_hashes: tuple[str, ...]
    batch_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


@dataclass(frozen=True)
class OracleQualifiedResearchDispatchManifest:
    schema_version: str
    engine_id: str
    generated_at: datetime
    manifest_id: str
    manifest_status: str
    work_item_directory: str
    dispatch_directory: str
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    batch_size: int
    source_work_item_count: int
    dispatch_entry_count: int
    dispatch_batch_count: int
    tier_1_dispatch_count: int
    tier_2_dispatch_count: int
    tier_3_dispatch_count: int
    entries: tuple[
        OracleQualifiedResearchDispatchEntry,
        ...,
    ]
    batches: tuple[
        OracleQualifiedResearchDispatchBatch,
        ...,
    ]
    source_work_item_report_hash: str
    read_only_corpus: bool
    research_execution_allowed: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    dispatch_artifact_persistence_allowed: bool
    manifest_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


class OracleQualifiedResearchDispatchManifestBuilder:
    """
    Creates deterministic dispatch batches from verified OIA-019 work items.

    Dispatch policy v1:

    1. Verify the complete OIA-019 report.
    2. Verify every OIA-019 work-item hash.
    3. Preserve ascending queue position.
    4. Preserve all upstream lineage.
    5. Assign contiguous dispatch sequence numbers.
    6. Partition entries into deterministic fixed-size batches.
    7. Create stable manifest and batch identifiers.
    8. Do not execute any research operation.
    """

    read_only_corpus = True
    research_execution_allowed = False
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    source_mutation_allowed = False
    market_order_creation_allowed = False
    funds_movement_allowed = False
    portfolio_mutation_allowed = False
    dispatch_artifact_persistence_allowed = True

    def __init__(
        self,
        *,
        work_item_directory: Path | str = (
            DEFAULT_WORK_ITEM_DIRECTORY
        ),
        dispatch_directory: Path | str = (
            DEFAULT_DISPATCH_DIRECTORY
        ),
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self._work_item_directory = Path(
            work_item_directory
        )

        self._dispatch_directory = Path(
            dispatch_directory
        )

        if isinstance(batch_size, bool):
            raise QualifiedResearchDispatchManifestInvariantError(
                "batch_size must be an integer."
            )

        try:
            normalized_batch_size = int(
                batch_size
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise QualifiedResearchDispatchManifestInvariantError(
                "batch_size must be an integer."
            ) from exc

        if normalized_batch_size <= 0:
            raise QualifiedResearchDispatchManifestInvariantError(
                "batch_size must be greater than zero."
            )

        self._batch_size = normalized_batch_size

    def _load_work_item_report(
        self,
    ) -> dict[str, Any]:
        current_path = (
            self._work_item_directory
            / "current.json"
        )

        if not current_path.exists():
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 current work-item report is missing: "
                f"{current_path}"
            )

        try:
            payload = json.loads(
                current_path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 work-item report is not valid JSON: "
                f"{current_path}"
            ) from exc

        if not isinstance(payload, dict):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 work-item report must be a JSON object."
            )

        report_hash = payload.pop(
            "report_hash",
            None,
        )

        if payload.get("schema_version") != "OIA-019":
            raise QualifiedResearchDispatchManifestInvariantError(
                "Unsupported OIA-019 schema version."
            )

        if payload.get("engine_id") != "OIA-019":
            raise QualifiedResearchDispatchManifestInvariantError(
                "Unsupported OIA-019 engine identity."
            )

        if (
            payload.get("ranking_policy_id")
            != RANKING_POLICY_ID
        ):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 ranking policy identity mismatch."
            )

        if (
            payload.get("tier_policy_id")
            != TIER_POLICY_ID
        ):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 tier policy identity mismatch."
            )

        if (
            payload.get("queue_policy_id")
            != QUEUE_POLICY_ID
        ):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 queue policy identity mismatch."
            )

        if (
            payload.get("work_item_policy_id")
            != WORK_ITEM_POLICY_ID
        ):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 work-item policy identity mismatch."
            )

        if (
            report_hash
            != work_item_stable_hash(payload)
        ):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 report hash verification failed."
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 read-only corpus invariant failed."
            )

        forbidden_true_fields = (
            "execution_allowed",
            "alerts_allowed",
            "qseries_handoff_allowed",
            "signals_allowed",
            "trading_recommendations_allowed",
            "source_mutation_allowed",
            "market_order_creation_allowed",
            "funds_movement_allowed",
            "portfolio_mutation_allowed",
        )

        for field_name in forbidden_true_fields:
            if payload.get(field_name) is not False:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 safety boundary mismatch: "
                    f"{field_name}."
                )

        work_items = payload.get(
            "work_items"
        )

        if not isinstance(work_items, list):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 work_items must be a list."
            )

        expected_work_item_count = int(
            payload.get(
                "work_item_count",
                -1,
            )
        )

        expected_admitted_count = int(
            payload.get(
                "source_queue_admitted_count",
                -1,
            )
        )

        if expected_work_item_count != len(work_items):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 work-item count does not match records."
            )

        if expected_admitted_count != len(work_items):
            raise QualifiedResearchDispatchManifestInvariantError(
                "Every OIA-019 admitted queue record must have "
                "exactly one work item."
            )

        verified_work_items: list[
            dict[str, Any]
        ] = []

        seen_work_item_ids: set[str] = set()
        seen_work_item_hashes: set[str] = set()
        seen_queue_positions: set[int] = set()
        seen_source_ranks: set[int] = set()
        seen_identities: set[
            tuple[str, str]
        ] = set()
        seen_queue_hashes: set[str] = set()
        seen_tier_hashes: set[str] = set()
        seen_ranking_hashes: set[str] = set()
        seen_eligibility_hashes: set[str] = set()

        previous_priority_score: Decimal | None = None

        for index, raw_work_item in enumerate(
            work_items,
            start=1,
        ):
            if not isinstance(raw_work_item, dict):
                raise QualifiedResearchDispatchManifestInvariantError(
                    f"OIA-019 work item {index} must be an object."
                )

            work_item = dict(
                raw_work_item
            )

            work_item_hash = work_item.pop(
                "work_item_hash",
                None,
            )

            if (
                work_item_hash
                != work_item_stable_hash(work_item)
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 work-item hash verification failed "
                    f"at index {index}."
                )

            if not _valid_hash(
                work_item_hash
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 work-item hash is malformed."
                )

            work_item_id = str(
                work_item.get(
                    "work_item_id",
                    "",
                )
            )

            if not work_item_id.startswith(
                "oia019-"
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 work-item ID is malformed."
                )

            if work_item_id in seen_work_item_ids:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 work-item ID."
                )

            if work_item_hash in seen_work_item_hashes:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 work-item hash."
                )

            if (
                work_item.get("work_item_status")
                != READY
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Only READY OIA-019 work items may enter "
                    "the dispatch manifest."
                )

            queue_position = int(
                work_item.get(
                    "queue_position",
                    -1,
                )
            )

            if queue_position != index:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 queue positions must be contiguous "
                    "and ordered from one."
                )

            if queue_position in seen_queue_positions:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 queue position."
                )

            source_rank = int(
                work_item.get(
                    "source_rank",
                    -1,
                )
            )

            if source_rank <= 0:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 source rank must be positive."
                )

            if source_rank in seen_source_ranks:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 source rank."
                )

            dimension = str(
                work_item.get(
                    "dimension",
                    "",
                )
            )

            key = str(
                work_item.get(
                    "key",
                    "",
                )
            )

            if not dimension or not key:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 work-item identity cannot be empty."
                )

            identity = (
                dimension,
                key,
            )

            if identity in seen_identities:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 work-item identity."
                )

            tier = str(
                work_item.get(
                    "tier",
                    "",
                )
            )

            if tier not in {
                TIER_1,
                TIER_2,
                TIER_3,
            }:
                raise QualifiedResearchDispatchManifestInvariantError(
                    f"Unsupported OIA-019 tier: {tier!r}"
                )

            priority_score = _decimal(
                work_item.get(
                    "priority_score"
                ),
                "priority_score",
            )

            if (
                priority_score < Decimal("0")
                or priority_score > Decimal("100")
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 priority score must be between "
                    "zero and one hundred."
                )

            if (
                previous_priority_score is not None
                and priority_score
                > previous_priority_score
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 work items are not ordered by "
                    "descending priority score."
                )

            if (
                work_item.get("research_objective")
                != RESEARCH_OBJECTIVE
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 research objective mismatch."
                )

            for sequence_field in (
                "required_operations",
                "prohibited_operations",
                "completion_requirements",
                "reason_codes",
            ):
                value = work_item.get(
                    sequence_field
                )

                if not isinstance(value, list):
                    raise QualifiedResearchDispatchManifestInvariantError(
                        f"OIA-019 {sequence_field} must be a list."
                    )

                if not value:
                    raise QualifiedResearchDispatchManifestInvariantError(
                        f"OIA-019 {sequence_field} cannot be empty."
                    )

            prohibited_operations = set(
                str(item)
                for item in work_item[
                    "prohibited_operations"
                ]
            )

            required_prohibitions = {
                "create_trading_signal",
                "create_trading_recommendation",
                "publish_operator_alert",
                "handoff_to_qseries_execution",
                "create_market_order",
                "move_funds",
                "mutate_portfolio",
                "mutate_source_corpus",
            }

            if not required_prohibitions.issubset(
                prohibited_operations
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 prohibited-operation boundary "
                    "is incomplete."
                )

            if (
                work_item.get("ranking_policy_id")
                != RANKING_POLICY_ID
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 ranking policy mismatch."
                )

            if (
                work_item.get("tier_policy_id")
                != TIER_POLICY_ID
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 tier policy mismatch."
                )

            if (
                work_item.get("queue_policy_id")
                != QUEUE_POLICY_ID
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 queue policy mismatch."
                )

            if (
                work_item.get("work_item_policy_id")
                != WORK_ITEM_POLICY_ID
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "OIA-019 work-item policy mismatch."
                )

            lineage_fields = (
                "source_eligibility_decision_hash",
                "source_ranking_record_hash",
                "source_tier_record_hash",
                "source_queue_record_hash",
            )

            for field_name in lineage_fields:
                if not _valid_hash(
                    work_item.get(field_name)
                ):
                    raise QualifiedResearchDispatchManifestInvariantError(
                        f"OIA-019 {field_name} is malformed."
                    )

            source_eligibility_hash = str(
                work_item[
                    "source_eligibility_decision_hash"
                ]
            )

            source_ranking_hash = str(
                work_item[
                    "source_ranking_record_hash"
                ]
            )

            source_tier_hash = str(
                work_item[
                    "source_tier_record_hash"
                ]
            )

            source_queue_hash = str(
                work_item[
                    "source_queue_record_hash"
                ]
            )

            if (
                source_eligibility_hash
                in seen_eligibility_hashes
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 eligibility lineage."
                )

            if (
                source_ranking_hash
                in seen_ranking_hashes
            ):
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 ranking lineage."
                )

            if source_tier_hash in seen_tier_hashes:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 tier lineage."
                )

            if source_queue_hash in seen_queue_hashes:
                raise QualifiedResearchDispatchManifestInvariantError(
                    "Duplicate OIA-019 queue lineage."
                )

            seen_work_item_ids.add(
                work_item_id
            )
            seen_work_item_hashes.add(
                work_item_hash
            )
            seen_queue_positions.add(
                queue_position
            )
            seen_source_ranks.add(
                source_rank
            )
            seen_identities.add(
                identity
            )
            seen_eligibility_hashes.add(
                source_eligibility_hash
            )
            seen_ranking_hashes.add(
                source_ranking_hash
            )
            seen_tier_hashes.add(
                source_tier_hash
            )
            seen_queue_hashes.add(
                source_queue_hash
            )

            previous_priority_score = (
                priority_score
            )

            work_item["work_item_hash"] = (
                work_item_hash
            )

            verified_work_items.append(
                work_item
            )

        calculated_tier_1_count = sum(
            item["tier"] == TIER_1
            for item in verified_work_items
        )

        calculated_tier_2_count = sum(
            item["tier"] == TIER_2
            for item in verified_work_items
        )

        calculated_tier_3_count = sum(
            item["tier"] == TIER_3
            for item in verified_work_items
        )

        if calculated_tier_1_count != int(
            payload.get(
                "tier_1_work_item_count",
                -1,
            )
        ):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 Tier 1 count does not match work items."
            )

        if calculated_tier_2_count != int(
            payload.get(
                "tier_2_work_item_count",
                -1,
            )
        ):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 Tier 2 count does not match work items."
            )

        if calculated_tier_3_count != int(
            payload.get(
                "tier_3_work_item_count",
                -1,
            )
        ):
            raise QualifiedResearchDispatchManifestInvariantError(
                "OIA-019 Tier 3 count does not match work items."
            )

        payload["work_items"] = (
            verified_work_items
        )
        payload["report_hash"] = (
            report_hash
        )

        return payload

    @staticmethod
    def _reason_codes(
        tier: str,
    ) -> tuple[str, ...]:
        return (
            "oia_019_work_item_verified",
            "work_item_identity_preserved",
            "queue_position_preserved",
            "upstream_lineage_preserved",
            f"{tier}_dispatch_entry_created",
            "deterministic_dispatch_sequence_assigned",
            "research_dispatch_definition_only",
        )

    def build(
        self,
        *,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchDispatchManifest:
        generated_at = _aware_utc(
            generated_at
            or datetime.now(timezone.utc),
            "generated_at",
        )

        source_report = (
            self._load_work_item_report()
        )

        source_work_items = list(
            source_report["work_items"]
        )

        source_work_items.sort(
            key=lambda item: (
                int(item["queue_position"]),
                int(item["source_rank"]),
                str(item["dimension"]),
                str(item["key"]),
            )
        )

        manifest_id = _dispatch_manifest_id(
            source_work_item_report_hash=str(
                source_report["report_hash"]
            ),
            batch_size=self._batch_size,
        )

        entries: list[
            OracleQualifiedResearchDispatchEntry
        ] = []

        for dispatch_sequence, item in enumerate(
            source_work_items,
            start=1,
        ):
            batch_number = (
                (dispatch_sequence - 1)
                // self._batch_size
            ) + 1

            batch_position = (
                (dispatch_sequence - 1)
                % self._batch_size
            ) + 1

            tier = str(
                item["tier"]
            )

            body = {
                "dispatch_sequence": (
                    dispatch_sequence
                ),
                "batch_number": batch_number,
                "batch_position": batch_position,
                "work_item_id": str(
                    item["work_item_id"]
                ),
                "work_item_status": str(
                    item["work_item_status"]
                ),
                "queue_position": int(
                    item["queue_position"]
                ),
                "source_rank": int(
                    item["source_rank"]
                ),
                "dimension": str(
                    item["dimension"]
                ),
                "key": str(
                    item["key"]
                ),
                "tier": tier,
                "priority_score": str(
                    item["priority_score"]
                ),
                "research_objective": str(
                    item["research_objective"]
                ),
                "required_operations": tuple(
                    str(value)
                    for value in item[
                        "required_operations"
                    ]
                ),
                "prohibited_operations": tuple(
                    str(value)
                    for value in item[
                        "prohibited_operations"
                    ]
                ),
                "completion_requirements": tuple(
                    str(value)
                    for value in item[
                        "completion_requirements"
                    ]
                ),
                "ranking_policy_id": str(
                    item["ranking_policy_id"]
                ),
                "tier_policy_id": str(
                    item["tier_policy_id"]
                ),
                "queue_policy_id": str(
                    item["queue_policy_id"]
                ),
                "work_item_policy_id": str(
                    item["work_item_policy_id"]
                ),
                "dispatch_policy_id": (
                    DISPATCH_POLICY_ID
                ),
                "dispatch_status": (
                    DISPATCH_READY
                ),
                "reason_codes": (
                    self._reason_codes(tier)
                ),
                "source_eligibility_decision_hash": str(
                    item[
                        "source_eligibility_decision_hash"
                    ]
                ),
                "source_ranking_record_hash": str(
                    item[
                        "source_ranking_record_hash"
                    ]
                ),
                "source_tier_record_hash": str(
                    item[
                        "source_tier_record_hash"
                    ]
                ),
                "source_queue_record_hash": str(
                    item[
                        "source_queue_record_hash"
                    ]
                ),
                "source_work_item_hash": str(
                    item["work_item_hash"]
                ),
            }

            entries.append(
                OracleQualifiedResearchDispatchEntry(
                    **body,
                    dispatch_entry_hash=stable_hash(
                        body
                    ),
                )
            )

        batches: list[
            OracleQualifiedResearchDispatchBatch
        ] = []

        if entries:
            highest_batch_number = max(
                entry.batch_number
                for entry in entries
            )
        else:
            highest_batch_number = 0

        for batch_number in range(
            1,
            highest_batch_number + 1,
        ):
            batch_entries = [
                entry
                for entry in entries
                if entry.batch_number == batch_number
            ]

            dispatch_entry_hashes = tuple(
                entry.dispatch_entry_hash
                for entry in batch_entries
            )

            source_work_item_hashes = tuple(
                entry.source_work_item_hash
                for entry in batch_entries
            )

            batch_id = _dispatch_batch_id(
                manifest_id=manifest_id,
                batch_number=batch_number,
                work_item_hashes=(
                    source_work_item_hashes
                ),
            )

            body = {
                "manifest_id": manifest_id,
                "batch_id": batch_id,
                "batch_number": batch_number,
                "batch_size_limit": (
                    self._batch_size
                ),
                "entry_count": len(
                    batch_entries
                ),
                "first_dispatch_sequence": (
                    batch_entries[
                        0
                    ].dispatch_sequence
                ),
                "last_dispatch_sequence": (
                    batch_entries[
                        -1
                    ].dispatch_sequence
                ),
                "first_queue_position": (
                    batch_entries[
                        0
                    ].queue_position
                ),
                "last_queue_position": (
                    batch_entries[
                        -1
                    ].queue_position
                ),
                "dispatch_entry_hashes": (
                    dispatch_entry_hashes
                ),
                "source_work_item_hashes": (
                    source_work_item_hashes
                ),
            }

            batches.append(
                OracleQualifiedResearchDispatchBatch(
                    **body,
                    batch_hash=stable_hash(body),
                )
            )

        tier_1_dispatch_count = sum(
            entry.tier == TIER_1
            for entry in entries
        )

        tier_2_dispatch_count = sum(
            entry.tier == TIER_2
            for entry in entries
        )

        tier_3_dispatch_count = sum(
            entry.tier == TIER_3
            for entry in entries
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "manifest_id": manifest_id,
            "manifest_status": MANIFEST_READY,
            "work_item_directory": str(
                self._work_item_directory
            ),
            "dispatch_directory": str(
                self._dispatch_directory
            ),
            "ranking_policy_id": (
                RANKING_POLICY_ID
            ),
            "tier_policy_id": (
                TIER_POLICY_ID
            ),
            "queue_policy_id": (
                QUEUE_POLICY_ID
            ),
            "work_item_policy_id": (
                WORK_ITEM_POLICY_ID
            ),
            "dispatch_policy_id": (
                DISPATCH_POLICY_ID
            ),
            "batch_size": (
                self._batch_size
            ),
            "source_work_item_count": len(
                source_work_items
            ),
            "dispatch_entry_count": len(
                entries
            ),
            "dispatch_batch_count": len(
                batches
            ),
            "tier_1_dispatch_count": (
                tier_1_dispatch_count
            ),
            "tier_2_dispatch_count": (
                tier_2_dispatch_count
            ),
            "tier_3_dispatch_count": (
                tier_3_dispatch_count
            ),
            "entries": tuple(entries),
            "batches": tuple(batches),
            "source_work_item_report_hash": str(
                source_report["report_hash"]
            ),
            "read_only_corpus": (
                READ_ONLY_CORPUS
            ),
            "research_execution_allowed": (
                RESEARCH_EXECUTION_ALLOWED
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
            "dispatch_artifact_persistence_allowed": (
                DISPATCH_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }

        manifest = (
            OracleQualifiedResearchDispatchManifest(
                **body,
                manifest_hash=stable_hash(body),
            )
        )

        if persist:
            manifest_payload = dict(
                manifest.to_dict()
            )

            _atomic_write(
                self._dispatch_directory
                / "current.json",
                manifest_payload,
            )

            _atomic_write(
                self._dispatch_directory
                / "manifests"
                / (
                    f"{manifest.manifest_id}-"
                    f"{manifest.manifest_hash}.json"
                ),
                manifest_payload,
            )

            for batch in manifest.batches:
                batch_entries = tuple(
                    entry
                    for entry in manifest.entries
                    if (
                        entry.batch_number
                        == batch.batch_number
                    )
                )

                batch_payload = {
                    "schema_version": (
                        SCHEMA_VERSION
                    ),
                    "engine_id": ENGINE_ID,
                    "manifest_id": (
                        manifest.manifest_id
                    ),
                    "manifest_hash": (
                        manifest.manifest_hash
                    ),
                    "batch": dict(
                        batch.to_dict()
                    ),
                    "entries": [
                        dict(entry.to_dict())
                        for entry in batch_entries
                    ],
                }

                _atomic_write(
                    self._dispatch_directory
                    / "batches"
                    / f"{batch.batch_id}.json",
                    batch_payload,
                )

        return manifest


def format_manifest(
    manifest: OracleQualifiedResearchDispatchManifest,
) -> str:
    lines = [
        "=" * 164,
        (
            "ORACLE QUALIFIED RESEARCH "
            "DISPATCH MANIFEST"
        ),
        "=" * 164,
        (
            "Generated at:     "
            f"{manifest.generated_at.isoformat()}"
        ),
        (
            "Manifest ID:      "
            f"{manifest.manifest_id}"
        ),
        (
            "Manifest status:  "
            f"{manifest.manifest_status}"
        ),
        (
            "Dispatch policy:  "
            f"{manifest.dispatch_policy_id}"
        ),
        (
            "Batch size:       "
            f"{manifest.batch_size}"
        ),
        (
            "Work items: "
            f"{manifest.source_work_item_count} | "
            "dispatch entries="
            f"{manifest.dispatch_entry_count} | "
            "batches="
            f"{manifest.dispatch_batch_count}"
        ),
        (
            "Dispatch by tier: "
            f"tier_1={manifest.tier_1_dispatch_count} | "
            f"tier_2={manifest.tier_2_dispatch_count} | "
            f"tier_3={manifest.tier_3_dispatch_count}"
        ),
        "-" * 164,
        (
            f"{'SEQ':>5}  "
            f"{'BATCH':>5}  "
            f"{'POS':>4}  "
            f"{'QUEUE':>5}  "
            f"{'RANK':>5}  "
            f"{'TIER':10} "
            f"{'STATUS':14} "
            f"{'DIMENSION':32} "
            f"{'KEY':32} "
            f"{'SCORE':>12} "
            f"{'WORK ITEM ID':40}"
        ),
    ]

    for entry in manifest.entries:
        lines.append(
            f"{entry.dispatch_sequence:>5}  "
            f"{entry.batch_number:>5}  "
            f"{entry.batch_position:>4}  "
            f"{entry.queue_position:>5}  "
            f"{entry.source_rank:>5}  "
            f"{entry.tier:10} "
            f"{entry.dispatch_status:14} "
            f"{entry.dimension[:32]:32} "
            f"{entry.key[:32]:32} "
            f"{entry.priority_score:>12} "
            f"{entry.work_item_id:40}"
        )

    if not manifest.entries:
        lines.append(
            "No verified OIA-019 work items were "
            "available for dispatch materialization."
        )

    lines.extend(
        [
            "-" * 164,
            (
                "Manifest hash: "
                f"{manifest.manifest_hash}"
            ),
            (
                "RESEARCH DISPATCH DEFINITION ONLY — "
                "NO RESEARCH EXECUTION, SIGNALS, ALERTS, "
                "RECOMMENDATIONS, QSERIES HANDOFFS, ORDERS, "
                "FUNDS MOVEMENT, PORTFOLIO MUTATION, "
                "OR SOURCE MUTATION"
            ),
        ]
    )

    return "\n".join(lines)


def main(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "OIA-020 qualified research dispatch "
            "manifest builder"
        )
    )

    parser.add_argument(
        "--work-item-directory",
        default=str(
            DEFAULT_WORK_ITEM_DIRECTORY
        ),
    )

    parser.add_argument(
        "--dispatch-directory",
        default=str(
            DEFAULT_DISPATCH_DIRECTORY
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
    )

    parser.add_argument(
        "--no-persist",
        action="store_true",
    )

    args = parser.parse_args(
        argv
    )

    manifest = (
        OracleQualifiedResearchDispatchManifestBuilder(
            work_item_directory=(
                args.work_item_directory
            ),
            dispatch_directory=(
                args.dispatch_directory
            ),
            batch_size=args.batch_size,
        ).build(
            persist=not args.no_persist,
        )
    )

    print(
        format_manifest(manifest)
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
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import (
    QUEUE_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_work_item_materialization_engine import (
    READY,
    RESEARCH_OBJECTIVE,
    WORK_ITEM_POLICY_ID,
    stable_hash as work_item_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_manifest_builder import (
    DISPATCH_POLICY_ID,
    DISPATCH_READY,
    ENGINE_ID,
    MANIFEST_READY,
    SCHEMA_VERSION,
    OracleQualifiedResearchDispatchManifestBuilder,
    QualifiedResearchDispatchManifestInvariantError,
    format_manifest,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    8,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_work_item(
    *,
    index: int,
    tier: str,
    score: str,
    key: str,
) -> dict:
    body = {
        "work_item_id": (
            f"oia019-{index:032x}"
        ),
        "work_item_status": READY,
        "queue_position": index,
        "source_rank": index,
        "dimension": (
            "candidate_family_horizon"
        ),
        "key": key,
        "tier": tier,
        "priority_score": score,
        "decisive_count": (
            800 - index
        ),
        "empirical_win_rate": (
            "0.65000000"
        ),
        "confidence_lower_bound": (
            "0.59000000"
        ),
        "calibration_quality": (
            "0.80000000"
        ),
        "reliability_quality": (
            "0.80000000"
        ),
        "resolution_quality": (
            "0.40000000"
        ),
        "sample_strength": (
            "1.00000000"
        ),
        "research_objective": (
            RESEARCH_OBJECTIVE
        ),
        "required_operations": [
            "load_verified_source_lineage",
            "read_additional_canonical_market_evidence",
            "compute_deterministic_research_metrics",
            "record_replayable_research_evidence",
            "produce_content_addressed_research_result",
        ],
        "prohibited_operations": [
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
        ],
        "completion_requirements": [
            "source_lineage_hashes_verified",
            "research_inputs_content_addressed",
            "research_method_policy_identified",
            "research_output_deterministically_hashed",
            "replay_produces_identical_output",
            "no_prohibited_operation_requested",
        ],
        "ranking_policy_id": (
            RANKING_POLICY_ID
        ),
        "tier_policy_id": (
            TIER_POLICY_ID
        ),
        "queue_policy_id": (
            QUEUE_POLICY_ID
        ),
        "work_item_policy_id": (
            WORK_ITEM_POLICY_ID
        ),
        "reason_codes": [
            "oia_018_queue_record_verified",
            "queue_admission_preserved",
            "queue_position_preserved",
            "upstream_lineage_preserved",
            "deterministic_work_item_id_created",
            "research_work_definition_only",
        ],
        "source_eligibility_decision_hash": (
            f"{index:064x}"[-64:]
        ),
        "source_ranking_record_hash": (
            f"{index + 100:064x}"[-64:]
        ),
        "source_tier_record_hash": (
            f"{index + 200:064x}"[-64:]
        ),
        "source_queue_record_hash": (
            f"{index + 300:064x}"[-64:]
        ),
    }

    return {
        **body,
        "work_item_hash": (
            work_item_hash(body)
        ),
    }


def write_work_item_report(
    directory: Path,
    work_items: list[dict],
) -> dict:
    body = {
        "schema_version": "OIA-019",
        "engine_id": "OIA-019",
        "generated_at": NOW,
        "queue_directory": "queue",
        "work_item_directory": str(
            directory
        ),
        "ranking_policy_id": (
            RANKING_POLICY_ID
        ),
        "tier_policy_id": (
            TIER_POLICY_ID
        ),
        "queue_policy_id": (
            QUEUE_POLICY_ID
        ),
        "work_item_policy_id": (
            WORK_ITEM_POLICY_ID
        ),
        "source_queue_record_count": len(
            work_items
        ),
        "source_queue_admitted_count": len(
            work_items
        ),
        "source_capacity_deferred_count": 0,
        "work_item_count": len(
            work_items
        ),
        "excluded_record_count": 0,
        "tier_1_work_item_count": sum(
            item["tier"] == TIER_1
            for item in work_items
        ),
        "tier_2_work_item_count": sum(
            item["tier"] == TIER_2
            for item in work_items
        ),
        "tier_3_work_item_count": sum(
            item["tier"] == TIER_3
            for item in work_items
        ),
        "work_items": work_items,
        "excluded_queue_record_hashes": [],
        "source_queue_report_hash": (
            "f" * 64
        ),
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "work_item_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "report_hash": (
            work_item_hash(body)
        ),
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

        work_item_directory = (
            root
            / "work-items"
        )

        dispatch_directory = (
            root
            / "dispatch"
        )

        source_work_items = [
            make_work_item(
                index=1,
                tier=TIER_1,
                score="84.00000000",
                key="momentum|300",
            ),
            make_work_item(
                index=2,
                tier=TIER_1,
                score="76.00000000",
                key="reversion|300",
            ),
            make_work_item(
                index=3,
                tier=TIER_2,
                score="64.00000000",
                key="momentum|900",
            ),
            make_work_item(
                index=4,
                tier=TIER_2,
                score="55.00000000",
                key="reversion|900",
            ),
            make_work_item(
                index=5,
                tier=TIER_3,
                score="43.00000000",
                key="momentum|3600",
            ),
        ]

        source_report = (
            write_work_item_report(
                work_item_directory,
                source_work_items,
            )
        )

        builder = (
            OracleQualifiedResearchDispatchManifestBuilder(
                work_item_directory=(
                    work_item_directory
                ),
                dispatch_directory=(
                    dispatch_directory
                ),
                batch_size=2,
            )
        )

        manifest = builder.build(
            generated_at=NOW,
            persist=True,
        )

        assert (
            manifest.schema_version
            == SCHEMA_VERSION
            == "OIA-020"
        )

        assert (
            manifest.engine_id
            == ENGINE_ID
            == "OIA-020"
        )

        assert (
            manifest.manifest_status
            == MANIFEST_READY
        )

        assert (
            manifest.dispatch_policy_id
            == DISPATCH_POLICY_ID
        )

        assert manifest.batch_size == 2
        assert manifest.source_work_item_count == 5
        assert manifest.dispatch_entry_count == 5
        assert manifest.dispatch_batch_count == 3

        assert manifest.tier_1_dispatch_count == 2
        assert manifest.tier_2_dispatch_count == 2
        assert manifest.tier_3_dispatch_count == 1

        assert [
            entry.dispatch_sequence
            for entry in manifest.entries
        ] == [
            1,
            2,
            3,
            4,
            5,
        ]

        assert [
            entry.queue_position
            for entry in manifest.entries
        ] == [
            1,
            2,
            3,
            4,
            5,
        ]

        assert [
            entry.batch_number
            for entry in manifest.entries
        ] == [
            1,
            1,
            2,
            2,
            3,
        ]

        assert [
            entry.batch_position
            for entry in manifest.entries
        ] == [
            1,
            2,
            1,
            2,
            1,
        ]

        assert all(
            entry.dispatch_status
            == DISPATCH_READY
            for entry in manifest.entries
        )

        assert [
            entry.source_work_item_hash
            for entry in manifest.entries
        ] == [
            item["work_item_hash"]
            for item in source_work_items
        ]

        assert (
            manifest.source_work_item_report_hash
            == source_report["report_hash"]
        )

        assert len(manifest.batches) == 3

        assert manifest.batches[0].batch_number == 1
        assert manifest.batches[0].entry_count == 2
        assert (
            manifest.batches[0].first_dispatch_sequence
            == 1
        )
        assert (
            manifest.batches[0].last_dispatch_sequence
            == 2
        )

        assert manifest.batches[1].batch_number == 2
        assert manifest.batches[1].entry_count == 2

        assert manifest.batches[2].batch_number == 3
        assert manifest.batches[2].entry_count == 1

        for entry in manifest.entries:
            payload = dict(
                entry.to_dict()
            )

            digest = payload.pop(
                "dispatch_entry_hash"
            )

            assert digest == stable_hash(
                payload
            )

            assert (
                "oia_019_work_item_verified"
                in entry.reason_codes
            )

            assert (
                "queue_position_preserved"
                in entry.reason_codes
            )

            assert (
                "research_dispatch_definition_only"
                in entry.reason_codes
            )

            assert (
                "handoff_to_qseries_execution"
                in entry.prohibited_operations
            )

            assert (
                "create_market_order"
                in entry.prohibited_operations
            )

        for batch in manifest.batches:
            payload = dict(
                batch.to_dict()
            )

            digest = payload.pop(
                "batch_hash"
            )

            assert digest == stable_hash(
                payload
            )

            assert batch.batch_id.startswith(
                "oia020-batch-"
            )

        manifest_payload = dict(
            manifest.to_dict()
        )

        manifest_digest = (
            manifest_payload.pop(
                "manifest_hash"
            )
        )

        assert manifest_digest == stable_hash(
            manifest_payload
        )

        assert manifest.manifest_id.startswith(
            "oia020-manifest-"
        )

        assert manifest.read_only_corpus
        assert not manifest.research_execution_allowed
        assert not manifest.execution_allowed
        assert not manifest.alerts_allowed
        assert not manifest.qseries_handoff_allowed
        assert not manifest.signals_allowed
        assert (
            not manifest.trading_recommendations_allowed
        )
        assert not manifest.source_mutation_allowed
        assert (
            not manifest.market_order_creation_allowed
        )
        assert not manifest.funds_movement_allowed
        assert (
            not manifest.portfolio_mutation_allowed
        )
        assert (
            manifest.dispatch_artifact_persistence_allowed
        )

        current_path = (
            dispatch_directory
            / "current.json"
        )

        immutable_manifest_path = (
            dispatch_directory
            / "manifests"
            / (
                f"{manifest.manifest_id}-"
                f"{manifest.manifest_hash}.json"
            )
        )

        batch_paths = [
            (
                dispatch_directory
                / "batches"
                / f"{batch.batch_id}.json"
            )
            for batch in manifest.batches
        ]

        assert current_path.exists()
        assert immutable_manifest_path.exists()

        for path in batch_paths:
            assert path.exists()

        current_bytes = (
            current_path.read_bytes()
        )

        manifest_bytes = (
            immutable_manifest_path.read_bytes()
        )

        first_batch_bytes = (
            batch_paths[0].read_bytes()
        )

        replay = builder.build(
            generated_at=NOW,
            persist=True,
        )

        assert (
            replay.manifest_id
            == manifest.manifest_id
        )

        assert (
            replay.manifest_hash
            == manifest.manifest_hash
        )

        assert (
            replay.batches[0].batch_id
            == manifest.batches[0].batch_id
        )

        assert (
            current_path.read_bytes()
            == current_bytes
        )

        assert (
            immutable_manifest_path.read_bytes()
            == manifest_bytes
        )

        assert (
            batch_paths[0].read_bytes()
            == first_batch_bytes
        )

        rendered = format_manifest(
            manifest
        )

        assert (
            "ORACLE QUALIFIED RESEARCH "
            "DISPATCH MANIFEST"
            in rendered
        )

        assert "momentum|300" in rendered
        assert "oia020-manifest-" in rendered
        assert "NO RESEARCH EXECUTION" in rendered

        tampered = json.loads(
            (
                work_item_directory
                / "current.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        tampered["work_items"][0][
            "priority_score"
        ] = "1.00000000"

        (
            work_item_directory
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
            builder.build(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchManifestInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-019 report was not rejected."
            )

        invalid_items = [
            make_work_item(
                index=1,
                tier=TIER_1,
                score="80.00000000",
                key="first",
            ),
            make_work_item(
                index=2,
                tier=TIER_1,
                score="90.00000000",
                key="second",
            ),
        ]

        write_work_item_report(
            work_item_directory,
            invalid_items,
        )

        try:
            builder.build(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchManifestInvariantError:
            pass
        else:
            raise AssertionError(
                "Out-of-order OIA-019 priority scores "
                "were not rejected."
            )

    print(
        "[PASS] OIA-020 Oracle Qualified Research "
        "Dispatch Manifest Builder"
    )


if __name__ == "__main__":
    run_test()
'''


INIT_IMPORT_BLOCK = r'''
from .oracle_qualified_research_dispatch_manifest_builder import (
    DISPATCH_POLICY_ID,
    DISPATCH_READY,
    MANIFEST_READY,
    OracleQualifiedResearchDispatchBatch,
    OracleQualifiedResearchDispatchEntry,
    OracleQualifiedResearchDispatchManifest,
    OracleQualifiedResearchDispatchManifestBuilder,
)
'''


INIT_EXPORTS = (
    "DISPATCH_POLICY_ID",
    "DISPATCH_READY",
    "MANIFEST_READY",
    "OracleQualifiedResearchDispatchBatch",
    "OracleQualifiedResearchDispatchEntry",
    "OracleQualifiedResearchDispatchManifest",
    "OracleQualifiedResearchDispatchManifestBuilder",
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


def verify_oia_019_contract(
    path: Path,
) -> None:
    if not path.exists():
        raise SystemExit(
            "[FAIL] OIA-019 production module is missing. "
            "Install and pass OIA-019 first."
        )

    text = path.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        'SCHEMA_VERSION = "OIA-019"',
        'ENGINE_ID = "OIA-019"',
        "WORK_ITEM_POLICY_ID",
        "oracle.qualified-research-work-item-materialization.v1",
        'READY = "ready"',
        "RESEARCH_OBJECTIVE",
        "evaluate_qualified_component_with_additional_read_only_evidence",
        "DEFAULT_WORK_ITEM_DIRECTORY",
        (
            "class "
            "OracleQualifiedResearchWorkItem:"
        ),
        (
            "class "
            "OracleQualifiedResearchWorkItemReport:"
        ),
        (
            "class "
            "OracleQualifiedResearchWorkItemMaterializationEngine:"
        ),
        "work_item_id",
        "work_item_status",
        "required_operations",
        "prohibited_operations",
        "completion_requirements",
        "source_eligibility_decision_hash",
        "source_ranking_record_hash",
        "source_tier_record_hash",
        "source_queue_record_hash",
        "work_item_hash",
        "report_hash",
        "work_item_artifact_persistence_allowed",
        "market_order_creation_allowed",
        "funds_movement_allowed",
        "portfolio_mutation_allowed",
    )

    missing = [
        token
        for token in required_tokens
        if token not in text
    ]

    if missing:
        raise SystemExit(
            "[FAIL] Actual OIA-019 production "
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
        ".oracle_qualified_research_dispatch_"
        "manifest_builder import"
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
        / (
            "oracle_qualified_research_work_item_"
            "materialization_engine.py"
        )
    )

    production_path = (
        analytics_directory
        / (
            "oracle_qualified_research_dispatch_"
            "manifest_builder.py"
        )
    )

    test_path = (
        root
        / (
            "test_oia_020_oracle_qualified_research_"
            "dispatch_manifest_builder.py"
        )
    )

    initializer_path = (
        analytics_directory
        / "__init__.py"
    )

    print("========================================")
    print(" OIA-020 INSTALLER")
    print(" QUALIFIED RESEARCH DISPATCH")
    print(" DETERMINISTIC MANIFEST BUILDER")
    print("========================================")

    verify_oia_019_contract(
        dependency_path
    )

    print(
        "[OK] Actual OIA-019 work-item "
        "materialization contract verified"
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
        "[OK] OIA-020 production, package, "
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
        "[OK] OIA-020 test executed successfully"
    )

    print(
        "[DONE] OIA-020 Oracle Qualified Research "
        "Dispatch Manifest Builder installed"
    )

    print()

    print(
        "Build the current research dispatch "
        "manifest with:"
    )

    print(
        "python -m "
        "qseries_v2.oracle_intelligence.analytics."
        "oracle_qualified_research_dispatch_"
        "manifest_builder"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )