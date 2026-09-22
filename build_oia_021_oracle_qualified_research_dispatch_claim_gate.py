from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


MODULE_SOURCE = r'''"""
OIA-021
Oracle Qualified Research Dispatch Claim Gate

Consumes the immutable OIA-020 qualified research dispatch manifest and
creates a deterministic claim for one verified dispatch batch.

The gate:

- verifies the complete OIA-020 manifest;
- verifies every OIA-020 dispatch-entry hash;
- verifies every OIA-020 dispatch-batch hash;
- preserves all upstream OIA-015 through OIA-020 lineage;
- claims exactly one existing, non-empty dispatch batch;
- binds the claim to an explicit read-only worker identity;
- creates a deterministic claim identifier and claim hash;
- persists immutable, content-addressed claim artifacts;
- does not execute research;
- does not create signals, alerts, recommendations, Q Series handoffs,
  market orders, funds movement, portfolio mutation, or source mutation.

OIA-021 authorizes dispatch consumption only.
It does not authorize research execution or trading execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
    READY,
    RESEARCH_OBJECTIVE,
    WORK_ITEM_POLICY_ID,
)
from .oracle_qualified_research_dispatch_manifest_builder import (
    DEFAULT_DISPATCH_DIRECTORY,
    DISPATCH_POLICY_ID,
    DISPATCH_READY,
    MANIFEST_READY,
    stable_hash as dispatch_stable_hash,
)


SCHEMA_VERSION = "OIA-021"
ENGINE_ID = "OIA-021"

CLAIM_POLICY_ID = (
    "oracle.qualified-research-dispatch-claim.v1"
)

CLAIM_READY = "claim_ready"
CLAIMED = "claimed"

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
CLAIM_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_CLAIM_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_dispatch_claims"
)

_WORKER_ID_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._:-]{2,127}$"
)


class QualifiedResearchDispatchClaimError(RuntimeError):
    """Base OIA-021 error."""


class QualifiedResearchDispatchClaimInvariantError(
    QualifiedResearchDispatchClaimError
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
        raise QualifiedResearchDispatchClaimInvariantError(
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
        raise QualifiedResearchDispatchClaimInvariantError(
            f"{field_name} must be a finite decimal."
        ) from exc

    if not result.is_finite():
        raise QualifiedResearchDispatchClaimInvariantError(
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


def _normalize_worker_id(
    worker_id: str,
) -> str:
    normalized = str(worker_id).strip().lower()

    if not _WORKER_ID_PATTERN.fullmatch(
        normalized
    ):
        raise QualifiedResearchDispatchClaimInvariantError(
            "worker_id must contain 3-128 lowercase letters, "
            "numbers, periods, underscores, colons, or hyphens "
            "and must begin with a letter or number."
        )

    return normalized


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


def _claim_id(
    *,
    manifest_hash: str,
    batch_hash: str,
    worker_id: str,
) -> str:
    digest = stable_hash(
        {
            "manifest_hash": manifest_hash,
            "batch_hash": batch_hash,
            "worker_id": worker_id,
            "claim_policy_id": CLAIM_POLICY_ID,
        }
    )

    return f"oia021-claim-{digest[:32]}"


@dataclass(frozen=True)
class OracleQualifiedResearchDispatchClaimEntry:
    claim_sequence: int
    dispatch_sequence: int
    batch_number: int
    batch_position: int
    work_item_id: str
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
    claim_status: str
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    claim_policy_id: str
    source_eligibility_decision_hash: str
    source_ranking_record_hash: str
    source_tier_record_hash: str
    source_queue_record_hash: str
    source_work_item_hash: str
    source_dispatch_entry_hash: str
    claim_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


@dataclass(frozen=True)
class OracleQualifiedResearchDispatchClaim:
    schema_version: str
    engine_id: str
    generated_at: datetime
    claim_id: str
    claim_status: str
    worker_id: str
    dispatch_directory: str
    claim_directory: str
    manifest_id: str
    selected_batch_id: str
    selected_batch_number: int
    selected_batch_entry_count: int
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    claim_policy_id: str
    entries: tuple[
        OracleQualifiedResearchDispatchClaimEntry,
        ...,
    ]
    source_manifest_hash: str
    source_batch_hash: str
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
    claim_artifact_persistence_allowed: bool
    claim_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(
            _canonical(asdict(self))
        )


class OracleQualifiedResearchDispatchClaimGate:
    """
    Creates a deterministic claim for one verified OIA-020 dispatch batch.

    Claim policy v1:

    1. Verify the full OIA-020 manifest.
    2. Verify all dispatch entries and all dispatch batches.
    3. Require an explicit valid worker identity.
    4. Require one existing, non-empty batch.
    5. Preserve exact dispatch and batch order.
    6. Preserve all upstream hashes.
    7. Create one deterministic claim record.
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
    claim_artifact_persistence_allowed = True

    def __init__(
        self,
        *,
        dispatch_directory: Path | str = (
            DEFAULT_DISPATCH_DIRECTORY
        ),
        claim_directory: Path | str = (
            DEFAULT_CLAIM_DIRECTORY
        ),
    ) -> None:
        self._dispatch_directory = Path(
            dispatch_directory
        )

        self._claim_directory = Path(
            claim_directory
        )

    def _load_manifest(
        self,
    ) -> dict[str, Any]:
        current_path = (
            self._dispatch_directory
            / "current.json"
        )

        if not current_path.exists():
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 current dispatch manifest is missing: "
                f"{current_path}"
            )

        try:
            payload = json.loads(
                current_path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 dispatch manifest is not valid JSON: "
                f"{current_path}"
            ) from exc

        if not isinstance(payload, dict):
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 dispatch manifest must be a JSON object."
            )

        manifest_hash = payload.pop(
            "manifest_hash",
            None,
        )

        if payload.get("schema_version") != "OIA-020":
            raise QualifiedResearchDispatchClaimInvariantError(
                "Unsupported OIA-020 schema version."
            )

        if payload.get("engine_id") != "OIA-020":
            raise QualifiedResearchDispatchClaimInvariantError(
                "Unsupported OIA-020 engine identity."
            )

        if payload.get("manifest_status") != MANIFEST_READY:
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 manifest is not ready."
            )

        policy_expectations = {
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
        }

        for field_name, expected in policy_expectations.items():
            if payload.get(field_name) != expected:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 policy identity mismatch: "
                    f"{field_name}."
                )

        if (
            manifest_hash
            != dispatch_stable_hash(payload)
        ):
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 manifest hash verification failed."
            )

        if not _valid_hash(manifest_hash):
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 manifest hash is malformed."
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 read-only corpus invariant failed."
            )

        forbidden_true_fields = (
            "research_execution_allowed",
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
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 safety boundary mismatch: "
                    f"{field_name}."
                )

        entries = payload.get("entries")
        batches = payload.get("batches")

        if not isinstance(entries, list):
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 entries must be a list."
            )

        if not isinstance(batches, list):
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 batches must be a list."
            )

        if int(
            payload.get(
                "dispatch_entry_count",
                -1,
            )
        ) != len(entries):
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 dispatch entry count mismatch."
            )

        if int(
            payload.get(
                "dispatch_batch_count",
                -1,
            )
        ) != len(batches):
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 dispatch batch count mismatch."
            )

        verified_entries: list[
            dict[str, Any]
        ] = []

        entry_by_hash: dict[
            str,
            dict[str, Any]
        ] = {}

        seen_dispatch_sequences: set[int] = set()
        seen_queue_positions: set[int] = set()
        seen_work_item_ids: set[str] = set()
        seen_entry_hashes: set[str] = set()

        previous_priority_score: Decimal | None = None

        for index, raw_entry in enumerate(
            entries,
            start=1,
        ):
            if not isinstance(raw_entry, dict):
                raise QualifiedResearchDispatchClaimInvariantError(
                    f"OIA-020 dispatch entry {index} must be an object."
                )

            entry = dict(raw_entry)

            entry_hash = entry.pop(
                "dispatch_entry_hash",
                None,
            )

            if (
                entry_hash
                != dispatch_stable_hash(entry)
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 dispatch-entry hash verification "
                    f"failed at index {index}."
                )

            if not _valid_hash(entry_hash):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 dispatch-entry hash is malformed."
                )

            dispatch_sequence = int(
                entry.get(
                    "dispatch_sequence",
                    -1,
                )
            )

            if dispatch_sequence != index:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 dispatch sequences must be "
                    "contiguous and ordered from one."
                )

            if dispatch_sequence in seen_dispatch_sequences:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "Duplicate OIA-020 dispatch sequence."
                )

            queue_position = int(
                entry.get(
                    "queue_position",
                    -1,
                )
            )

            if queue_position != index:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 queue positions must remain "
                    "contiguous and ordered from one."
                )

            if queue_position in seen_queue_positions:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "Duplicate OIA-020 queue position."
                )

            work_item_id = str(
                entry.get(
                    "work_item_id",
                    "",
                )
            )

            if not work_item_id.startswith("oia019-"):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 work-item ID is malformed."
                )

            if work_item_id in seen_work_item_ids:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "Duplicate OIA-020 work-item ID."
                )

            if entry.get("work_item_status") != READY:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 entry references a non-ready work item."
                )

            if entry.get("dispatch_status") != DISPATCH_READY:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 entry is not dispatch ready."
                )

            tier = str(
                entry.get(
                    "tier",
                    "",
                )
            )

            if tier not in {
                TIER_1,
                TIER_2,
                TIER_3,
            }:
                raise QualifiedResearchDispatchClaimInvariantError(
                    f"Unsupported OIA-020 tier: {tier!r}"
                )

            priority_score = _decimal(
                entry.get("priority_score"),
                "priority_score",
            )

            if (
                priority_score < Decimal("0")
                or priority_score > Decimal("100")
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 priority score must be between "
                    "zero and one hundred."
                )

            if (
                previous_priority_score is not None
                and priority_score > previous_priority_score
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 entries are not ordered by "
                    "descending priority score."
                )

            if (
                entry.get("research_objective")
                != RESEARCH_OBJECTIVE
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 research objective mismatch."
                )

            for sequence_field in (
                "required_operations",
                "prohibited_operations",
                "completion_requirements",
                "reason_codes",
            ):
                field_value = entry.get(
                    sequence_field
                )

                if (
                    not isinstance(field_value, list)
                    or not field_value
                ):
                    raise QualifiedResearchDispatchClaimInvariantError(
                        f"OIA-020 {sequence_field} must be "
                        "a non-empty list."
                    )

            prohibited = set(
                str(value)
                for value in entry[
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
                prohibited
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 prohibited-operation boundary "
                    "is incomplete."
                )

            for field_name, expected in (
                (
                    "ranking_policy_id",
                    RANKING_POLICY_ID,
                ),
                (
                    "tier_policy_id",
                    TIER_POLICY_ID,
                ),
                (
                    "queue_policy_id",
                    QUEUE_POLICY_ID,
                ),
                (
                    "work_item_policy_id",
                    WORK_ITEM_POLICY_ID,
                ),
                (
                    "dispatch_policy_id",
                    DISPATCH_POLICY_ID,
                ),
            ):
                if entry.get(field_name) != expected:
                    raise QualifiedResearchDispatchClaimInvariantError(
                        "OIA-020 dispatch entry policy mismatch: "
                        f"{field_name}."
                    )

            for field_name in (
                "source_eligibility_decision_hash",
                "source_ranking_record_hash",
                "source_tier_record_hash",
                "source_queue_record_hash",
                "source_work_item_hash",
            ):
                if not _valid_hash(
                    entry.get(field_name)
                ):
                    raise QualifiedResearchDispatchClaimInvariantError(
                        f"OIA-020 {field_name} is malformed."
                    )

            if entry_hash in seen_entry_hashes:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "Duplicate OIA-020 dispatch-entry hash."
                )

            entry["dispatch_entry_hash"] = entry_hash

            seen_dispatch_sequences.add(
                dispatch_sequence
            )
            seen_queue_positions.add(
                queue_position
            )
            seen_work_item_ids.add(
                work_item_id
            )
            seen_entry_hashes.add(
                entry_hash
            )

            previous_priority_score = priority_score

            verified_entries.append(
                entry
            )

            entry_by_hash[
                entry_hash
            ] = entry

        verified_batches: list[
            dict[str, Any]
        ] = []

        seen_batch_numbers: set[int] = set()
        seen_batch_ids: set[str] = set()
        seen_batch_hashes: set[str] = set()
        referenced_entry_hashes: list[str] = []

        for index, raw_batch in enumerate(
            batches,
            start=1,
        ):
            if not isinstance(raw_batch, dict):
                raise QualifiedResearchDispatchClaimInvariantError(
                    f"OIA-020 batch {index} must be an object."
                )

            batch = dict(raw_batch)

            batch_hash = batch.pop(
                "batch_hash",
                None,
            )

            if (
                batch_hash
                != dispatch_stable_hash(batch)
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch hash verification failed "
                    f"at index {index}."
                )

            if not _valid_hash(batch_hash):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch hash is malformed."
                )

            batch_number = int(
                batch.get(
                    "batch_number",
                    -1,
                )
            )

            if batch_number != index:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch numbers must be contiguous "
                    "and ordered from one."
                )

            batch_id = str(
                batch.get(
                    "batch_id",
                    "",
                )
            )

            if not batch_id.startswith(
                "oia020-batch-"
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch ID is malformed."
                )

            if batch.get("manifest_id") != payload.get(
                "manifest_id"
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch manifest identity mismatch."
                )

            entry_count = int(
                batch.get(
                    "entry_count",
                    -1,
                )
            )

            if entry_count <= 0:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 dispatch batches must be non-empty."
                )

            dispatch_entry_hashes = batch.get(
                "dispatch_entry_hashes"
            )

            source_work_item_hashes = batch.get(
                "source_work_item_hashes"
            )

            if not isinstance(
                dispatch_entry_hashes,
                list,
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch dispatch-entry hashes "
                    "must be a list."
                )

            if not isinstance(
                source_work_item_hashes,
                list,
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch source-work-item hashes "
                    "must be a list."
                )

            if (
                len(dispatch_entry_hashes)
                != entry_count
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch entry count does not "
                    "match dispatch-entry hashes."
                )

            if (
                len(source_work_item_hashes)
                != entry_count
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch entry count does not "
                    "match work-item hashes."
                )

            batch_entries: list[
                dict[str, Any]
            ] = []

            for entry_hash in dispatch_entry_hashes:
                if entry_hash not in entry_by_hash:
                    raise QualifiedResearchDispatchClaimInvariantError(
                        "OIA-020 batch references an unknown "
                        "dispatch-entry hash."
                    )

                batch_entries.append(
                    entry_by_hash[entry_hash]
                )

            expected_sequences = list(
                range(
                    int(
                        batch[
                            "first_dispatch_sequence"
                        ]
                    ),
                    int(
                        batch[
                            "last_dispatch_sequence"
                        ]
                    ) + 1,
                )
            )

            actual_sequences = [
                int(entry["dispatch_sequence"])
                for entry in batch_entries
            ]

            if actual_sequences != expected_sequences:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch dispatch sequence range "
                    "does not match entries."
                )

            expected_queue_positions = list(
                range(
                    int(
                        batch[
                            "first_queue_position"
                        ]
                    ),
                    int(
                        batch[
                            "last_queue_position"
                        ]
                    ) + 1,
                )
            )

            actual_queue_positions = [
                int(entry["queue_position"])
                for entry in batch_entries
            ]

            if (
                actual_queue_positions
                != expected_queue_positions
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch queue-position range "
                    "does not match entries."
                )

            actual_work_item_hashes = [
                str(entry["source_work_item_hash"])
                for entry in batch_entries
            ]

            if (
                actual_work_item_hashes
                != source_work_item_hashes
            ):
                raise QualifiedResearchDispatchClaimInvariantError(
                    "OIA-020 batch work-item hashes do not "
                    "match entries."
                )

            if batch_number in seen_batch_numbers:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "Duplicate OIA-020 batch number."
                )

            if batch_id in seen_batch_ids:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "Duplicate OIA-020 batch ID."
                )

            if batch_hash in seen_batch_hashes:
                raise QualifiedResearchDispatchClaimInvariantError(
                    "Duplicate OIA-020 batch hash."
                )

            seen_batch_numbers.add(
                batch_number
            )
            seen_batch_ids.add(
                batch_id
            )
            seen_batch_hashes.add(
                batch_hash
            )

            referenced_entry_hashes.extend(
                dispatch_entry_hashes
            )

            batch["batch_hash"] = batch_hash
            verified_batches.append(
                batch
            )

        if referenced_entry_hashes != [
            entry["dispatch_entry_hash"]
            for entry in verified_entries
        ]:
            raise QualifiedResearchDispatchClaimInvariantError(
                "OIA-020 batches do not cover dispatch entries "
                "exactly once and in order."
            )

        payload["entries"] = verified_entries
        payload["batches"] = verified_batches
        payload["manifest_hash"] = manifest_hash

        return payload

    def claim(
        self,
        *,
        worker_id: str,
        batch_number: int,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchDispatchClaim:
        normalized_worker_id = _normalize_worker_id(
            worker_id
        )

        if isinstance(batch_number, bool):
            raise QualifiedResearchDispatchClaimInvariantError(
                "batch_number must be an integer."
            )

        try:
            normalized_batch_number = int(
                batch_number
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise QualifiedResearchDispatchClaimInvariantError(
                "batch_number must be an integer."
            ) from exc

        if normalized_batch_number <= 0:
            raise QualifiedResearchDispatchClaimInvariantError(
                "batch_number must be positive."
            )

        generated_at = _aware_utc(
            generated_at
            or datetime.now(timezone.utc),
            "generated_at",
        )

        manifest = self._load_manifest()

        selected_batches = [
            batch
            for batch in manifest["batches"]
            if int(batch["batch_number"])
            == normalized_batch_number
        ]

        if len(selected_batches) != 1:
            raise QualifiedResearchDispatchClaimInvariantError(
                "Requested OIA-020 batch does not exist: "
                f"{normalized_batch_number}"
            )

        selected_batch = selected_batches[0]

        selected_entry_hashes = tuple(
            str(value)
            for value in selected_batch[
                "dispatch_entry_hashes"
            ]
        )

        selected_entries = [
            entry
            for entry in manifest["entries"]
            if entry["dispatch_entry_hash"]
            in selected_entry_hashes
        ]

        selected_entries.sort(
            key=lambda entry: int(
                entry["dispatch_sequence"]
            )
        )

        if len(selected_entries) != int(
            selected_batch["entry_count"]
        ):
            raise QualifiedResearchDispatchClaimInvariantError(
                "Selected OIA-020 batch entry count mismatch."
            )

        source_manifest_hash = str(
            manifest["manifest_hash"]
        )

        source_batch_hash = str(
            selected_batch["batch_hash"]
        )

        claim_id = _claim_id(
            manifest_hash=source_manifest_hash,
            batch_hash=source_batch_hash,
            worker_id=normalized_worker_id,
        )

        claim_entries: list[
            OracleQualifiedResearchDispatchClaimEntry
        ] = []

        for claim_sequence, source_entry in enumerate(
            selected_entries,
            start=1,
        ):
            body = {
                "claim_sequence": claim_sequence,
                "dispatch_sequence": int(
                    source_entry[
                        "dispatch_sequence"
                    ]
                ),
                "batch_number": int(
                    source_entry[
                        "batch_number"
                    ]
                ),
                "batch_position": int(
                    source_entry[
                        "batch_position"
                    ]
                ),
                "work_item_id": str(
                    source_entry[
                        "work_item_id"
                    ]
                ),
                "queue_position": int(
                    source_entry[
                        "queue_position"
                    ]
                ),
                "source_rank": int(
                    source_entry[
                        "source_rank"
                    ]
                ),
                "dimension": str(
                    source_entry[
                        "dimension"
                    ]
                ),
                "key": str(
                    source_entry[
                        "key"
                    ]
                ),
                "tier": str(
                    source_entry[
                        "tier"
                    ]
                ),
                "priority_score": str(
                    source_entry[
                        "priority_score"
                    ]
                ),
                "research_objective": str(
                    source_entry[
                        "research_objective"
                    ]
                ),
                "required_operations": tuple(
                    str(value)
                    for value in source_entry[
                        "required_operations"
                    ]
                ),
                "prohibited_operations": tuple(
                    str(value)
                    for value in source_entry[
                        "prohibited_operations"
                    ]
                ),
                "completion_requirements": tuple(
                    str(value)
                    for value in source_entry[
                        "completion_requirements"
                    ]
                ),
                "claim_status": CLAIMED,
                "ranking_policy_id": str(
                    source_entry[
                        "ranking_policy_id"
                    ]
                ),
                "tier_policy_id": str(
                    source_entry[
                        "tier_policy_id"
                    ]
                ),
                "queue_policy_id": str(
                    source_entry[
                        "queue_policy_id"
                    ]
                ),
                "work_item_policy_id": str(
                    source_entry[
                        "work_item_policy_id"
                    ]
                ),
                "dispatch_policy_id": str(
                    source_entry[
                        "dispatch_policy_id"
                    ]
                ),
                "claim_policy_id": CLAIM_POLICY_ID,
                "source_eligibility_decision_hash": str(
                    source_entry[
                        "source_eligibility_decision_hash"
                    ]
                ),
                "source_ranking_record_hash": str(
                    source_entry[
                        "source_ranking_record_hash"
                    ]
                ),
                "source_tier_record_hash": str(
                    source_entry[
                        "source_tier_record_hash"
                    ]
                ),
                "source_queue_record_hash": str(
                    source_entry[
                        "source_queue_record_hash"
                    ]
                ),
                "source_work_item_hash": str(
                    source_entry[
                        "source_work_item_hash"
                    ]
                ),
                "source_dispatch_entry_hash": str(
                    source_entry[
                        "dispatch_entry_hash"
                    ]
                ),
            }

            claim_entries.append(
                OracleQualifiedResearchDispatchClaimEntry(
                    **body,
                    claim_entry_hash=stable_hash(
                        body
                    ),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "claim_id": claim_id,
            "claim_status": CLAIM_READY,
            "worker_id": normalized_worker_id,
            "dispatch_directory": str(
                self._dispatch_directory
            ),
            "claim_directory": str(
                self._claim_directory
            ),
            "manifest_id": str(
                manifest["manifest_id"]
            ),
            "selected_batch_id": str(
                selected_batch["batch_id"]
            ),
            "selected_batch_number": (
                normalized_batch_number
            ),
            "selected_batch_entry_count": len(
                claim_entries
            ),
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
            "claim_policy_id": CLAIM_POLICY_ID,
            "entries": tuple(
                claim_entries
            ),
            "source_manifest_hash": (
                source_manifest_hash
            ),
            "source_batch_hash": (
                source_batch_hash
            ),
            "read_only_corpus": READ_ONLY_CORPUS,
            "research_execution_allowed": (
                RESEARCH_EXECUTION_ALLOWED
            ),
            "execution_allowed": EXECUTION_ALLOWED,
            "alerts_allowed": ALERTS_ALLOWED,
            "qseries_handoff_allowed": (
                QSERIES_HANDOFF_ALLOWED
            ),
            "signals_allowed": SIGNALS_ALLOWED,
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
            "claim_artifact_persistence_allowed": (
                CLAIM_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }

        claim = OracleQualifiedResearchDispatchClaim(
            **body,
            claim_hash=stable_hash(body),
        )

        if persist:
            payload = dict(
                claim.to_dict()
            )

            _atomic_write(
                self._claim_directory
                / "current.json",
                payload,
            )

            _atomic_write(
                self._claim_directory
                / "claims"
                / (
                    f"{claim.claim_id}-"
                    f"{claim.claim_hash}.json"
                ),
                payload,
            )

            _atomic_write(
                self._claim_directory
                / "workers"
                / normalized_worker_id
                / (
                    f"batch-{normalized_batch_number}-"
                    f"{claim.claim_id}.json"
                ),
                payload,
            )

        return claim


def format_claim(
    claim: OracleQualifiedResearchDispatchClaim,
) -> str:
    lines = [
        "=" * 164,
        (
            "ORACLE QUALIFIED RESEARCH "
            "DISPATCH CLAIM"
        ),
        "=" * 164,
        (
            "Generated at:    "
            f"{claim.generated_at.isoformat()}"
        ),
        (
            "Claim ID:        "
            f"{claim.claim_id}"
        ),
        (
            "Claim status:    "
            f"{claim.claim_status}"
        ),
        (
            "Worker ID:       "
            f"{claim.worker_id}"
        ),
        (
            "Manifest ID:     "
            f"{claim.manifest_id}"
        ),
        (
            "Selected batch:  "
            f"{claim.selected_batch_number} | "
            f"{claim.selected_batch_id}"
        ),
        (
            "Claim entries:   "
            f"{claim.selected_batch_entry_count}"
        ),
        "-" * 164,
        (
            f"{'CLAIM':>5}  "
            f"{'DISPATCH':>8}  "
            f"{'BATCH':>5}  "
            f"{'POS':>4}  "
            f"{'QUEUE':>5}  "
            f"{'RANK':>5}  "
            f"{'TIER':10} "
            f"{'STATUS':9} "
            f"{'DIMENSION':32} "
            f"{'KEY':32} "
            f"{'SCORE':>12} "
            f"{'WORK ITEM ID':40}"
        ),
    ]

    for entry in claim.entries:
        lines.append(
            f"{entry.claim_sequence:>5}  "
            f"{entry.dispatch_sequence:>8}  "
            f"{entry.batch_number:>5}  "
            f"{entry.batch_position:>4}  "
            f"{entry.queue_position:>5}  "
            f"{entry.source_rank:>5}  "
            f"{entry.tier:10} "
            f"{entry.claim_status:9} "
            f"{entry.dimension[:32]:32} "
            f"{entry.key[:32]:32} "
            f"{entry.priority_score:>12} "
            f"{entry.work_item_id:40}"
        )

    lines.extend(
        [
            "-" * 164,
            f"Claim hash: {claim.claim_hash}",
            (
                "DISPATCH CONSUMPTION CLAIM ONLY — "
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
            "OIA-021 qualified research dispatch claim gate"
        )
    )

    parser.add_argument(
        "--dispatch-directory",
        default=str(
            DEFAULT_DISPATCH_DIRECTORY
        ),
    )

    parser.add_argument(
        "--claim-directory",
        default=str(
            DEFAULT_CLAIM_DIRECTORY
        ),
    )

    parser.add_argument(
        "--worker-id",
        required=True,
    )

    parser.add_argument(
        "--batch-number",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--no-persist",
        action="store_true",
    )

    args = parser.parse_args(
        argv
    )

    claim = OracleQualifiedResearchDispatchClaimGate(
        dispatch_directory=(
            args.dispatch_directory
        ),
        claim_directory=(
            args.claim_directory
        ),
    ).claim(
        worker_id=args.worker_id,
        batch_number=args.batch_number,
        persist=not args.no_persist,
    )

    print(
        format_claim(claim)
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
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_manifest_builder import (
    DISPATCH_POLICY_ID,
    DISPATCH_READY,
    MANIFEST_READY,
    stable_hash as dispatch_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_claim_gate import (
    CLAIMED,
    CLAIM_POLICY_ID,
    CLAIM_READY,
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleQualifiedResearchDispatchClaimGate,
    QualifiedResearchDispatchClaimInvariantError,
    format_claim,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    9,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_entry(
    *,
    index: int,
    batch_number: int,
    batch_position: int,
    tier: str,
    score: str,
) -> dict:
    body = {
        "dispatch_sequence": index,
        "batch_number": batch_number,
        "batch_position": batch_position,
        "work_item_id": (
            f"oia019-{index:032x}"
        ),
        "work_item_status": READY,
        "queue_position": index,
        "source_rank": index,
        "dimension": (
            "candidate_family_horizon"
        ),
        "key": f"candidate-{index}|300",
        "tier": tier,
        "priority_score": score,
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
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "dispatch_status": DISPATCH_READY,
        "reason_codes": [
            "oia_019_work_item_verified",
            "work_item_identity_preserved",
            "queue_position_preserved",
            "upstream_lineage_preserved",
            "deterministic_dispatch_sequence_assigned",
            "research_dispatch_definition_only",
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
        "source_work_item_hash": (
            f"{index + 400:064x}"[-64:]
        ),
    }

    return {
        **body,
        "dispatch_entry_hash": dispatch_hash(
            body
        ),
    }


def make_batch(
    *,
    manifest_id: str,
    batch_number: int,
    entries: list[dict],
    batch_size: int,
) -> dict:
    body = {
        "manifest_id": manifest_id,
        "batch_id": (
            f"oia020-batch-{batch_number:032x}"
        ),
        "batch_number": batch_number,
        "batch_size_limit": batch_size,
        "entry_count": len(entries),
        "first_dispatch_sequence": (
            entries[0]["dispatch_sequence"]
        ),
        "last_dispatch_sequence": (
            entries[-1]["dispatch_sequence"]
        ),
        "first_queue_position": (
            entries[0]["queue_position"]
        ),
        "last_queue_position": (
            entries[-1]["queue_position"]
        ),
        "dispatch_entry_hashes": [
            entry["dispatch_entry_hash"]
            for entry in entries
        ],
        "source_work_item_hashes": [
            entry["source_work_item_hash"]
            for entry in entries
        ],
    }

    return {
        **body,
        "batch_hash": dispatch_hash(
            body
        ),
    }


def write_manifest(
    directory: Path,
) -> dict:
    manifest_id = (
        "oia020-manifest-"
        + "a" * 32
    )

    entries = [
        make_entry(
            index=1,
            batch_number=1,
            batch_position=1,
            tier=TIER_1,
            score="88.00000000",
        ),
        make_entry(
            index=2,
            batch_number=1,
            batch_position=2,
            tier=TIER_1,
            score="78.00000000",
        ),
        make_entry(
            index=3,
            batch_number=2,
            batch_position=1,
            tier=TIER_2,
            score="62.00000000",
        ),
        make_entry(
            index=4,
            batch_number=2,
            batch_position=2,
            tier=TIER_3,
            score="42.00000000",
        ),
    ]

    batches = [
        make_batch(
            manifest_id=manifest_id,
            batch_number=1,
            entries=entries[:2],
            batch_size=2,
        ),
        make_batch(
            manifest_id=manifest_id,
            batch_number=2,
            entries=entries[2:],
            batch_size=2,
        ),
    ]

    body = {
        "schema_version": "OIA-020",
        "engine_id": "OIA-020",
        "generated_at": NOW,
        "manifest_id": manifest_id,
        "manifest_status": MANIFEST_READY,
        "work_item_directory": "work-items",
        "dispatch_directory": str(directory),
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "batch_size": 2,
        "source_work_item_count": 4,
        "dispatch_entry_count": 4,
        "dispatch_batch_count": 2,
        "tier_1_dispatch_count": 2,
        "tier_2_dispatch_count": 1,
        "tier_3_dispatch_count": 1,
        "entries": entries,
        "batches": batches,
        "source_work_item_report_hash": (
            "f" * 64
        ),
        "read_only_corpus": True,
        "research_execution_allowed": False,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "dispatch_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "manifest_hash": dispatch_hash(
            body
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

        dispatch_directory = (
            root
            / "dispatch"
        )

        claim_directory = (
            root
            / "claims"
        )

        source_manifest = write_manifest(
            dispatch_directory
        )

        gate = (
            OracleQualifiedResearchDispatchClaimGate(
                dispatch_directory=(
                    dispatch_directory
                ),
                claim_directory=(
                    claim_directory
                ),
            )
        )

        claim = gate.claim(
            worker_id="oracle-research-worker-01",
            batch_number=2,
            generated_at=NOW,
            persist=True,
        )

        assert (
            claim.schema_version
            == SCHEMA_VERSION
            == "OIA-021"
        )

        assert (
            claim.engine_id
            == ENGINE_ID
            == "OIA-021"
        )

        assert claim.claim_status == CLAIM_READY
        assert (
            claim.worker_id
            == "oracle-research-worker-01"
        )
        assert claim.selected_batch_number == 2
        assert claim.selected_batch_entry_count == 2
        assert claim.claim_policy_id == CLAIM_POLICY_ID

        assert [
            entry.claim_sequence
            for entry in claim.entries
        ] == [
            1,
            2,
        ]

        assert [
            entry.dispatch_sequence
            for entry in claim.entries
        ] == [
            3,
            4,
        ]

        assert [
            entry.batch_position
            for entry in claim.entries
        ] == [
            1,
            2,
        ]

        assert all(
            entry.claim_status == CLAIMED
            for entry in claim.entries
        )

        assert [
            entry.tier
            for entry in claim.entries
        ] == [
            TIER_2,
            TIER_3,
        ]

        assert (
            claim.source_manifest_hash
            == source_manifest[
                "manifest_hash"
            ]
        )

        assert (
            claim.source_batch_hash
            == source_manifest[
                "batches"
            ][1]["batch_hash"]
        )

        for entry in claim.entries:
            payload = dict(
                entry.to_dict()
            )

            digest = payload.pop(
                "claim_entry_hash"
            )

            assert digest == stable_hash(
                payload
            )

            assert (
                "create_market_order"
                in entry.prohibited_operations
            )

            assert (
                "handoff_to_qseries_execution"
                in entry.prohibited_operations
            )

        claim_payload = dict(
            claim.to_dict()
        )

        claim_digest = claim_payload.pop(
            "claim_hash"
        )

        assert claim_digest == stable_hash(
            claim_payload
        )

        assert claim.claim_id.startswith(
            "oia021-claim-"
        )

        assert claim.read_only_corpus
        assert not claim.research_execution_allowed
        assert not claim.execution_allowed
        assert not claim.alerts_allowed
        assert not claim.qseries_handoff_allowed
        assert not claim.signals_allowed
        assert (
            not claim.trading_recommendations_allowed
        )
        assert not claim.source_mutation_allowed
        assert (
            not claim.market_order_creation_allowed
        )
        assert not claim.funds_movement_allowed
        assert (
            not claim.portfolio_mutation_allowed
        )
        assert (
            claim.claim_artifact_persistence_allowed
        )

        current_path = (
            claim_directory
            / "current.json"
        )

        immutable_path = (
            claim_directory
            / "claims"
            / (
                f"{claim.claim_id}-"
                f"{claim.claim_hash}.json"
            )
        )

        worker_path = (
            claim_directory
            / "workers"
            / "oracle-research-worker-01"
            / (
                "batch-2-"
                f"{claim.claim_id}.json"
            )
        )

        assert current_path.exists()
        assert immutable_path.exists()
        assert worker_path.exists()

        current_bytes = (
            current_path.read_bytes()
        )

        immutable_bytes = (
            immutable_path.read_bytes()
        )

        replay = gate.claim(
            worker_id="ORACLE-RESEARCH-WORKER-01",
            batch_number=2,
            generated_at=NOW,
            persist=True,
        )

        assert replay.claim_id == claim.claim_id
        assert replay.claim_hash == claim.claim_hash

        assert (
            current_path.read_bytes()
            == current_bytes
        )

        assert (
            immutable_path.read_bytes()
            == immutable_bytes
        )

        rendered = format_claim(
            claim
        )

        assert (
            "ORACLE QUALIFIED RESEARCH "
            "DISPATCH CLAIM"
            in rendered
        )

        assert "oracle-research-worker-01" in rendered
        assert "candidate-3|300" in rendered
        assert "NO RESEARCH EXECUTION" in rendered

        try:
            gate.claim(
                worker_id="x",
                batch_number=1,
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchClaimInvariantError:
            pass
        else:
            raise AssertionError(
                "Malformed worker identity was not rejected."
            )

        try:
            gate.claim(
                worker_id="oracle-worker-02",
                batch_number=99,
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchClaimInvariantError:
            pass
        else:
            raise AssertionError(
                "Unknown dispatch batch was not rejected."
            )

        tampered = json.loads(
            (
                dispatch_directory
                / "current.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        tampered["entries"][0][
            "priority_score"
        ] = "1.00000000"

        (
            dispatch_directory
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
            gate.claim(
                worker_id="oracle-worker-03",
                batch_number=1,
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchClaimInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-020 manifest was not rejected."
            )

    print(
        "[PASS] OIA-021 Oracle Qualified Research "
        "Dispatch Claim Gate"
    )


if __name__ == "__main__":
    run_test()
'''


INIT_IMPORT_BLOCK = r'''
from .oracle_qualified_research_dispatch_claim_gate import (
    CLAIMED,
    CLAIM_POLICY_ID,
    CLAIM_READY,
    OracleQualifiedResearchDispatchClaim,
    OracleQualifiedResearchDispatchClaimEntry,
    OracleQualifiedResearchDispatchClaimGate,
)
'''


INIT_EXPORTS = (
    "CLAIMED",
    "CLAIM_POLICY_ID",
    "CLAIM_READY",
    "OracleQualifiedResearchDispatchClaim",
    "OracleQualifiedResearchDispatchClaimEntry",
    "OracleQualifiedResearchDispatchClaimGate",
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


def verify_oia_020_contract(
    path: Path,
) -> None:
    if not path.exists():
        raise SystemExit(
            "[FAIL] OIA-020 production module is missing. "
            "Install and pass OIA-020 first."
        )

    text = path.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        'SCHEMA_VERSION = "OIA-020"',
        'ENGINE_ID = "OIA-020"',
        "DISPATCH_POLICY_ID",
        "oracle.qualified-research-dispatch-manifest.v1",
        'MANIFEST_READY = "manifest_ready"',
        'DISPATCH_READY = "dispatch_ready"',
        "DEFAULT_DISPATCH_DIRECTORY",
        (
            "class "
            "OracleQualifiedResearchDispatchEntry:"
        ),
        (
            "class "
            "OracleQualifiedResearchDispatchBatch:"
        ),
        (
            "class "
            "OracleQualifiedResearchDispatchManifest:"
        ),
        (
            "class "
            "OracleQualifiedResearchDispatchManifestBuilder:"
        ),
        "dispatch_sequence",
        "batch_number",
        "batch_position",
        "dispatch_entry_hash",
        "batch_hash",
        "manifest_hash",
        "source_eligibility_decision_hash",
        "source_ranking_record_hash",
        "source_tier_record_hash",
        "source_queue_record_hash",
        "source_work_item_hash",
        "research_execution_allowed",
        "execution_allowed",
        "qseries_handoff_allowed",
        "dispatch_artifact_persistence_allowed",
    )

    missing = [
        token
        for token in required_tokens
        if token not in text
    ]

    if missing:
        raise SystemExit(
            "[FAIL] Actual OIA-020 production "
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
        "claim_gate import"
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
            "oracle_qualified_research_dispatch_"
            "manifest_builder.py"
        )
    )

    production_path = (
        analytics_directory
        / (
            "oracle_qualified_research_dispatch_"
            "claim_gate.py"
        )
    )

    test_path = (
        root
        / (
            "test_oia_021_oracle_qualified_research_"
            "dispatch_claim_gate.py"
        )
    )

    initializer_path = (
        analytics_directory
        / "__init__.py"
    )

    print("========================================")
    print(" OIA-021 INSTALLER")
    print(" QUALIFIED RESEARCH DISPATCH")
    print(" DETERMINISTIC CLAIM GATE")
    print("========================================")

    verify_oia_020_contract(
        dependency_path
    )

    print(
        "[OK] Actual OIA-020 dispatch manifest "
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
        "[OK] OIA-021 production, package, "
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
        "[OK] OIA-021 test executed successfully"
    )

    print(
        "[DONE] OIA-021 Oracle Qualified Research "
        "Dispatch Claim Gate installed"
    )

    print()

    print(
        "Claim a verified research dispatch batch with:"
    )

    print(
        "python -m "
        "qseries_v2.oracle_intelligence.analytics."
        "oracle_qualified_research_dispatch_claim_gate "
        "--worker-id oracle-research-worker-01 "
        "--batch-number 1"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )