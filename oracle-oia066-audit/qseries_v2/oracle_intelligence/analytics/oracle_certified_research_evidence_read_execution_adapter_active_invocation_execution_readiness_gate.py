from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "OIA-047"
ENGINE_ID = "OIA-047"

POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "active-invocation-execution-readiness.v1"
)

STATUS_ACTIVE_INVOCATION_READY = (
    "evidence_read_execution_adapter_active_invocation_execution_ready"
)

STATUS_READINESS_ISSUED = (
    "evidence_read_execution_adapter_active_invocation_execution_readiness_issued"
)

DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_invocation_activation"
)

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_active_invocation_execution_readiness"
)


class ActiveInvocationExecutionReadinessInvariantError(RuntimeError):
    """Raised when the OIA-046 active-invocation contract is unsafe."""


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ActiveInvocationExecutionReadinessInvariantError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=path.parent,
    )
    temporary_path = Path(handle.name)

    try:
        with handle:
            json.dump(
                payload,
                handle,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@dataclass(frozen=True)
class ActiveInvocationExecutionReadinessEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    readiness_arguments: dict[str, Any]
    readiness_checks: tuple[str, ...]
    readiness_status: str
    source_active_execution_invocation_hash: str
    source_execution_invocation_hash: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    active_invocation_execution_readiness_hash: str


@dataclass(frozen=True)
class ActiveInvocationExecutionReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    execution_readiness_id: str
    execution_readiness_status: str
    execution_readiness_policy_id: str
    worker_id: str
    readiness_entry_count: int
    readiness_entries: tuple[ActiveInvocationExecutionReadinessEntry, ...]
    source_invocation_activation_id: str
    source_invocation_activation_manifest_hash: str
    source_execution_invocation_manifest_id: str
    source_execution_invocation_manifest_hash: str
    source_execution_authorization_id: str
    source_execution_authorization_manifest_hash: str
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    execution_readiness_issued: bool
    execution_authorization_evaluation_allowed: bool
    callable_resolution_allowed: bool
    callable_resolution_performed: bool
    callable_binding_allowed: bool
    adapter_execution_allowed: bool
    adapter_execution_performed: bool
    corpus_read_execution_allowed: bool
    research_execution_allowed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    execution_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    readiness_artifact_persistence_allowed: bool
    execution_readiness_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionReadinessGate:
    """
    OIA-047 active-invocation execution-readiness boundary.

    This gate verifies that every OIA-046 active invocation remains:

    - deterministic,
    - authorized,
    - read-only,
    - non-executing,
    - lineage-complete,
    - eligible for a later execution-authorization decision.

    It does not import, resolve, bind, invoke, or execute an adapter.
    """

    def __init__(
        self,
        *,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
    ) -> None:
        self.activation_directory = Path(activation_directory)
        self.readiness_directory = Path(readiness_directory)

    def _load_activation_manifest(self) -> dict[str, Any]:
        current = self.activation_directory / "current.json"

        if not current.exists():
            raise ActiveInvocationExecutionReadinessInvariantError(
                f"OIA-046 current activation artifact missing: {current}"
            )

        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ActiveInvocationExecutionReadinessInvariantError(
                "OIA-046 activation artifact could not be decoded."
            ) from error

        if not isinstance(source, dict):
            raise ActiveInvocationExecutionReadinessInvariantError(
                "OIA-046 activation artifact must be a JSON object."
            )

        manifest_hash = source.pop(
            "activation_manifest_hash",
            None,
        )

        if (
            not valid_hash(manifest_hash)
            or stable_hash(source) != manifest_hash
        ):
            raise ActiveInvocationExecutionReadinessInvariantError(
                "OIA-046 activation manifest hash verification failed."
            )

        source["activation_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-046",
            "engine_id": "OIA-046",
            "activation_status":
                "evidence_read_execution_adapter_execution_invocation_activation_issued",
            "activation_policy_id":
                "oracle.certified-research-evidence-read-execution-adapter-"
                "execution-invocation-activation.v1",
            "invocation_activation_issued": True,
            "execution_readiness_evaluation_allowed": True,
            "callable_resolution_allowed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "research_execution_allowed": False,
            "analytic_conclusion_allowed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "trading_recommendations_allowed": False,
            "source_mutation_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "activation_artifact_persistence_allowed": True,
        }

        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    f"OIA-046 invariant failed: {field_name}."
                )

        identifier_fields = {
            "activation_id",
            "worker_id",
            "source_execution_invocation_manifest_id",
            "source_execution_authorization_id",
            "source_execution_readiness_id",
        }

        for field_name in identifier_fields:
            value = source.get(field_name)

            if not isinstance(value, str) or not value:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    f"OIA-046 identifier is invalid: {field_name}."
                )

        hash_fields = {
            "source_execution_invocation_manifest_hash",
            "source_execution_authorization_manifest_hash",
            "source_execution_readiness_manifest_hash",
            "source_activation_hash",
        }

        for field_name in hash_fields:
            if not valid_hash(source.get(field_name)):
                raise ActiveInvocationExecutionReadinessInvariantError(
                    f"OIA-046 hash field is invalid: {field_name}."
                )

        active_invocation_count = source.get(
            "active_invocation_count"
        )
        active_invocations = source.get("active_invocations")

        if (
            not isinstance(active_invocation_count, int)
            or isinstance(active_invocation_count, bool)
            or active_invocation_count < 1
        ):
            raise ActiveInvocationExecutionReadinessInvariantError(
                "OIA-046 active invocation count is invalid."
            )

        if (
            not isinstance(active_invocations, list)
            or len(active_invocations) != active_invocation_count
        ):
            raise ActiveInvocationExecutionReadinessInvariantError(
                "OIA-046 active invocation collection is invalid."
            )

        source_lineage = source.get("source_lineage")

        if not isinstance(source_lineage, dict) or not source_lineage:
            raise ActiveInvocationExecutionReadinessInvariantError(
                "OIA-046 source lineage is missing."
            )

        required_lineage_fields = {
            "source_evidence_read_execution_adapter_invocation_manifest_id",
            "source_evidence_read_execution_adapter_authorization_manifest_id",
            "source_evidence_read_execution_adapter_readiness_manifest_id",
            "source_evidence_read_execution_adapter_binding_manifest_id",
            "source_evidence_read_execution_invocation_activation_id",
            "source_evidence_read_execution_invocation_manifest_id",
            "source_evidence_read_execution_authorization_id",
            "source_evidence_read_execution_readiness_id",
            "source_evidence_read_request_activation_id",
            "source_evidence_read_request_manifest_id",
            "source_evidence_task_activation_id",
            "source_evidence_task_manifest_id",
            "source_evidence_batch_activation_id",
            "source_evidence_batch_id",
            "source_evidence_session_id",
            "source_evidence_manifest_id",
            "source_certification_id",
            "source_readiness_id",
            "source_session_id",
            "source_activation_id",
            "source_claim_id",
            "dispatch_manifest_id",
            "selected_batch_id",
            "selected_batch_number",
        }

        missing_lineage = required_lineage_fields - set(
            source_lineage
        )

        if missing_lineage:
            raise ActiveInvocationExecutionReadinessInvariantError(
                "OIA-046 lineage is incomplete: "
                f"{sorted(missing_lineage)}"
            )

        for field_name in (
            required_lineage_fields - {"selected_batch_number"}
        ):
            value = source_lineage.get(field_name)

            if not isinstance(value, str) or not value:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    f"OIA-046 lineage field is invalid: {field_name}."
                )

        selected_batch_number = source_lineage.get(
            "selected_batch_number"
        )

        if (
            not isinstance(selected_batch_number, int)
            or isinstance(selected_batch_number, bool)
            or selected_batch_number < 1
        ):
            raise ActiveInvocationExecutionReadinessInvariantError(
                "OIA-046 selected batch number is invalid."
            )

        required_activation_checks = {
            "invocation_manifest_hash_verified",
            "execution_invocation_hash_verified",
            "authorization_lineage_verified",
            "readiness_lineage_verified",
            "prior_activation_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_argument_allowlist_verified",
            "active_invocation_remained_non_executing",
            "callable_resolution_remained_disabled",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }

        seen_work_item_ids: set[str] = set()
        seen_active_hashes: set[str] = set()

        for expected_sequence, invocation in enumerate(
            active_invocations,
            start=1,
        ):
            if not isinstance(invocation, dict):
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation must be an object."
                )

            active_hash = invocation.pop(
                "active_execution_invocation_hash",
                None,
            )

            if (
                not valid_hash(active_hash)
                or stable_hash(invocation) != active_hash
            ):
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation hash verification failed."
                )

            invocation[
                "active_execution_invocation_hash"
            ] = active_hash

            if active_hash in seen_active_hashes:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 contains a duplicate active invocation hash."
                )

            seen_active_hashes.add(active_hash)

            if invocation.get("sequence") != expected_sequence:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation sequence is non-canonical."
                )

            if invocation.get("worker_id") != source["worker_id"]:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation worker mismatch."
                )

            if (
                invocation.get("activation_status")
                != "evidence_read_execution_adapter_execution_invocation_active"
            ):
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 invocation is not active."
                )

            work_item_id = invocation.get("work_item_id")
            adapter_id = invocation.get("adapter_id")
            read_operation = invocation.get("read_operation")
            arguments = invocation.get(
                "active_invocation_arguments"
            )
            checks = invocation.get("activation_checks")

            if not isinstance(work_item_id, str) or not work_item_id:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 work-item identity is invalid."
                )

            if work_item_id in seen_work_item_ids:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 contains duplicate work-item identities."
                )

            seen_work_item_ids.add(work_item_id)

            if (
                not isinstance(adapter_id, str)
                or not adapter_id.startswith("oracle_read_only_")
                or "write" in adapter_id.lower()
                or "mutation" in adapter_id.lower()
                or "order" in adapter_id.lower()
                or "fund" in adapter_id.lower()
                or "portfolio" in adapter_id.lower()
            ):
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 adapter identity is not approved read-only."
                )

            if (
                not isinstance(read_operation, str)
                or not read_operation.startswith("read_")
                or "write" in read_operation.lower()
                or "delete" in read_operation.lower()
                or "update" in read_operation.lower()
                or "insert" in read_operation.lower()
                or "order" in read_operation.lower()
            ):
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 operation is not a bounded read operation."
                )

            if not isinstance(arguments, dict):
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation arguments are invalid."
                )

            if set(arguments) != {
                "activated",
                "read_only",
                "execute",
            }:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation argument allowlist mismatch."
                )

            if arguments.get("activated") is not True:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation is not activated."
                )

            if arguments.get("read_only") is not True:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation is not read-only."
                )

            if arguments.get("execute") is not False:
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 active invocation crossed the execution boundary."
                )

            if (
                not isinstance(checks, list)
                or not required_activation_checks.issubset(set(checks))
            ):
                raise ActiveInvocationExecutionReadinessInvariantError(
                    "OIA-046 activation checks are incomplete."
                )

            lineage_hash_fields = {
                "source_execution_invocation_hash",
                "source_authorization_entry_hash",
                "source_readiness_entry_hash",
                "source_active_adapter_invocation_hash",
            }

            for field_name in lineage_hash_fields:
                if not valid_hash(invocation.get(field_name)):
                    raise ActiveInvocationExecutionReadinessInvariantError(
                        f"OIA-046 active-invocation lineage hash is invalid: "
                        f"{field_name}."
                    )

        return source

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> ActiveInvocationExecutionReadinessManifest:
        evaluated_at = aware_utc(evaluated_at, "evaluated_at")
        source = self._load_activation_manifest()

        readiness_entries: list[
            ActiveInvocationExecutionReadinessEntry
        ] = []

        for sequence, invocation in enumerate(
            source["active_invocations"],
            start=1,
        ):
            readiness_arguments = {
                "activated": True,
                "read_only": True,
                "execute": False,
                "callable_resolution_requested": False,
            }

            entry_body = {
                "sequence": sequence,
                "worker_id": invocation["worker_id"],
                "work_item_id": invocation["work_item_id"],
                "adapter_id": invocation["adapter_id"],
                "read_operation": invocation["read_operation"],
                "readiness_arguments": readiness_arguments,
                "readiness_checks": (
                    "activation_manifest_hash_verified",
                    "active_execution_invocation_hash_verified",
                    "execution_invocation_lineage_verified",
                    "authorization_lineage_verified",
                    "readiness_lineage_verified",
                    "adapter_read_only_identity_verified",
                    "operation_read_only_verified",
                    "invocation_argument_allowlist_verified",
                    "active_invocation_remained_non_executing",
                    "callable_resolution_not_performed",
                    "callable_binding_remained_disabled",
                    "corpus_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "readiness_status":
                    STATUS_ACTIVE_INVOCATION_READY,
                "source_active_execution_invocation_hash":
                    invocation[
                        "active_execution_invocation_hash"
                    ],
                "source_execution_invocation_hash":
                    invocation[
                        "source_execution_invocation_hash"
                    ],
                "source_authorization_entry_hash":
                    invocation[
                        "source_authorization_entry_hash"
                    ],
                "source_readiness_entry_hash":
                    invocation["source_readiness_entry_hash"],
                "source_active_adapter_invocation_hash":
                    invocation[
                        "source_active_adapter_invocation_hash"
                    ],
            }

            readiness_entries.append(
                ActiveInvocationExecutionReadinessEntry(
                    **entry_body,
                    active_invocation_execution_readiness_hash=stable_hash(
                        entry_body
                    ),
                )
            )

        source_activation_manifest_hash = source[
            "activation_manifest_hash"
        ]

        execution_readiness_id = (
            "oia047-active-invocation-execution-readiness-"
            + stable_hash(
                {
                    "source_invocation_activation_manifest_hash":
                        source_activation_manifest_hash,
                    "execution_readiness_policy_id":
                        POLICY_ID,
                }
            )[:32]
        )

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "execution_readiness_id":
                execution_readiness_id,
            "execution_readiness_status":
                STATUS_READINESS_ISSUED,
            "execution_readiness_policy_id":
                POLICY_ID,
            "worker_id": source["worker_id"],
            "readiness_entry_count":
                len(readiness_entries),
            "readiness_entries":
                tuple(readiness_entries),
            "source_invocation_activation_id":
                source["activation_id"],
            "source_invocation_activation_manifest_hash":
                source_activation_manifest_hash,
            "source_execution_invocation_manifest_id":
                source[
                    "source_execution_invocation_manifest_id"
                ],
            "source_execution_invocation_manifest_hash":
                source[
                    "source_execution_invocation_manifest_hash"
                ],
            "source_execution_authorization_id":
                source["source_execution_authorization_id"],
            "source_execution_authorization_manifest_hash":
                source[
                    "source_execution_authorization_manifest_hash"
                ],
            "source_execution_readiness_id":
                source["source_execution_readiness_id"],
            "source_execution_readiness_manifest_hash":
                source[
                    "source_execution_readiness_manifest_hash"
                ],
            "source_activation_hash":
                source["source_activation_hash"],
            "source_lineage":
                dict(source["source_lineage"]),
            "execution_readiness_issued": True,
            "execution_authorization_evaluation_allowed": True,
            "callable_resolution_allowed": False,
            "callable_resolution_performed": False,
            "callable_binding_allowed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "research_execution_allowed": False,
            "analytic_conclusion_allowed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "trading_recommendations_allowed": False,
            "source_mutation_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "readiness_artifact_persistence_allowed": True,
        }

        serializable_body = dict(manifest_body)
        serializable_body["readiness_entries"] = [
            asdict(entry)
            for entry in readiness_entries
        ]

        result = ActiveInvocationExecutionReadinessManifest(
            **manifest_body,
            execution_readiness_manifest_hash=stable_hash(
                serializable_body
            ),
        )

        if persist:
            payload = asdict(result)

            atomic_write(
                self.readiness_directory / "current.json",
                payload,
            )

            atomic_write(
                self.readiness_directory
                / "readiness"
                / f"{execution_readiness_id}.json",
                payload,
            )

            atomic_write(
                self.readiness_directory
                / "workers"
                / result.worker_id
                / f"{execution_readiness_id}.json",
                payload,
            )

        return result
