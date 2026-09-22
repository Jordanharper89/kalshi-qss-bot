from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "OIA-048"
ENGINE_ID = "OIA-048"

POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "active-invocation-execution-authorization.v1"
)

STATUS_ACTIVE_INVOCATION_AUTHORIZED = (
    "evidence_read_execution_adapter_active_invocation_execution_authorized"
)

STATUS_AUTHORIZATION_ISSUED = (
    "evidence_read_execution_adapter_active_invocation_execution_authorization_issued"
)

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_active_invocation_execution_readiness"
)

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_active_invocation_execution_authorization"
)


class ActiveInvocationExecutionAuthorizationInvariantError(RuntimeError):
    """Raised when the OIA-047 readiness contract is invalid or unsafe."""


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
        raise ActiveInvocationExecutionAuthorizationInvariantError(
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
class ActiveInvocationExecutionAuthorizationEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    authorization_arguments: dict[str, Any]
    authorization_checks: tuple[str, ...]
    authorization_status: str
    source_active_invocation_execution_readiness_hash: str
    source_active_execution_invocation_hash: str
    source_execution_invocation_hash: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    active_invocation_execution_authorization_hash: str


@dataclass(frozen=True)
class ActiveInvocationExecutionAuthorizationManifest:
    schema_version: str
    engine_id: str
    authorized_at: str
    execution_authorization_id: str
    execution_authorization_status: str
    execution_authorization_policy_id: str
    worker_id: str
    authorization_entry_count: int
    authorization_entries: tuple[
        ActiveInvocationExecutionAuthorizationEntry,
        ...,
    ]
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_invocation_activation_id: str
    source_invocation_activation_manifest_hash: str
    source_execution_invocation_manifest_id: str
    source_execution_invocation_manifest_hash: str
    source_prior_execution_authorization_id: str
    source_prior_execution_authorization_manifest_hash: str
    source_prior_execution_readiness_id: str
    source_prior_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    execution_authorization_issued: bool
    callable_resolution_evaluation_allowed: bool
    callable_resolution_allowed: bool
    callable_resolution_performed: bool
    callable_binding_allowed: bool
    callable_binding_performed: bool
    adapter_execution_allowed: bool
    adapter_execution_performed: bool
    corpus_read_execution_allowed: bool
    corpus_read_execution_performed: bool
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
    authorization_artifact_persistence_allowed: bool
    execution_authorization_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate:
    """
    OIA-048 active-invocation execution-authorization boundary.

    This gate authorizes the exact OIA-047 readiness-certified invocation for
    the next certification step: callable-resolution evaluation.

    Authorization is not callable resolution and is not execution.

    This component does not:

    - import an adapter module,
    - resolve an adapter callable,
    - bind invocation arguments,
    - invoke a callable,
    - connect to PostgreSQL,
    - perform a network request,
    - read the certified evidence corpus,
    - create research conclusions,
    - create forecasts,
    - create signals,
    - create alerts,
    - communicate with Q Series,
    - create orders,
    - move funds,
    - mutate a portfolio.
    """

    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.authorization_directory = Path(authorization_directory)

    def _load_readiness_manifest(self) -> dict[str, Any]:
        current = self.readiness_directory / "current.json"

        if not current.exists():
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                f"OIA-047 current readiness artifact missing: {current}"
            )

        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                "OIA-047 readiness artifact could not be decoded."
            ) from error

        if not isinstance(source, dict):
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                "OIA-047 readiness artifact must be a JSON object."
            )

        manifest_hash = source.pop(
            "execution_readiness_manifest_hash",
            None,
        )

        if (
            not valid_hash(manifest_hash)
            or stable_hash(source) != manifest_hash
        ):
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                "OIA-047 execution-readiness manifest hash verification failed."
            )

        source["execution_readiness_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-047",
            "engine_id": "OIA-047",
            "execution_readiness_status":
                "evidence_read_execution_adapter_active_invocation_execution_readiness_issued",
            "execution_readiness_policy_id":
                "oracle.certified-research-evidence-read-execution-adapter-"
                "active-invocation-execution-readiness.v1",
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

        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    f"OIA-047 invariant failed: {field_name}."
                )

        identifier_fields = {
            "execution_readiness_id",
            "worker_id",
            "source_invocation_activation_id",
            "source_execution_invocation_manifest_id",
            "source_execution_authorization_id",
            "source_execution_readiness_id",
        }

        for field_name in identifier_fields:
            value = source.get(field_name)

            if not isinstance(value, str) or not value:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    f"OIA-047 identifier is invalid: {field_name}."
                )

        hash_fields = {
            "source_invocation_activation_manifest_hash",
            "source_execution_invocation_manifest_hash",
            "source_execution_authorization_manifest_hash",
            "source_execution_readiness_manifest_hash",
            "source_activation_hash",
        }

        for field_name in hash_fields:
            if not valid_hash(source.get(field_name)):
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    f"OIA-047 hash field is invalid: {field_name}."
                )

        readiness_entry_count = source.get(
            "readiness_entry_count"
        )
        readiness_entries = source.get("readiness_entries")

        if (
            not isinstance(readiness_entry_count, int)
            or isinstance(readiness_entry_count, bool)
            or readiness_entry_count < 1
        ):
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                "OIA-047 readiness-entry count is invalid."
            )

        if (
            not isinstance(readiness_entries, list)
            or len(readiness_entries) != readiness_entry_count
        ):
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                "OIA-047 readiness-entry collection is invalid."
            )

        source_lineage = source.get("source_lineage")

        if not isinstance(source_lineage, dict) or not source_lineage:
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                "OIA-047 source lineage is missing."
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
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                "OIA-047 lineage is incomplete: "
                f"{sorted(missing_lineage)}"
            )

        for field_name in (
            required_lineage_fields - {"selected_batch_number"}
        ):
            value = source_lineage.get(field_name)

            if not isinstance(value, str) or not value:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    f"OIA-047 lineage field is invalid: {field_name}."
                )

        selected_batch_number = source_lineage.get(
            "selected_batch_number"
        )

        if (
            not isinstance(selected_batch_number, int)
            or isinstance(selected_batch_number, bool)
            or selected_batch_number < 1
        ):
            raise ActiveInvocationExecutionAuthorizationInvariantError(
                "OIA-047 selected batch number is invalid."
            )

        required_readiness_checks = {
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
        }

        seen_work_item_ids: set[str] = set()
        seen_readiness_hashes: set[str] = set()

        for expected_sequence, entry in enumerate(
            readiness_entries,
            start=1,
        ):
            if not isinstance(entry, dict):
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 readiness entry must be an object."
                )

            readiness_hash = entry.pop(
                "active_invocation_execution_readiness_hash",
                None,
            )

            if (
                not valid_hash(readiness_hash)
                or stable_hash(entry) != readiness_hash
            ):
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 readiness-entry hash verification failed."
                )

            entry[
                "active_invocation_execution_readiness_hash"
            ] = readiness_hash

            if readiness_hash in seen_readiness_hashes:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 contains a duplicate readiness-entry hash."
                )

            seen_readiness_hashes.add(readiness_hash)

            if entry.get("sequence") != expected_sequence:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 readiness-entry sequence is non-canonical."
                )

            if entry.get("worker_id") != source["worker_id"]:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 readiness-entry worker mismatch."
                )

            if (
                entry.get("readiness_status")
                != "evidence_read_execution_adapter_active_invocation_execution_ready"
            ):
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 active invocation is not execution-ready."
                )

            work_item_id = entry.get("work_item_id")
            adapter_id = entry.get("adapter_id")
            read_operation = entry.get("read_operation")
            arguments = entry.get("readiness_arguments")
            checks = entry.get("readiness_checks")

            if not isinstance(work_item_id, str) or not work_item_id:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 work-item identity is invalid."
                )

            if work_item_id in seen_work_item_ids:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 contains duplicate work-item identities."
                )

            seen_work_item_ids.add(work_item_id)

            if (
                not isinstance(adapter_id, str)
                or not adapter_id.startswith("oracle_read_only_")
                or "write" in adapter_id.lower()
                or "mutation" in adapter_id.lower()
                or "delete" in adapter_id.lower()
                or "order" in adapter_id.lower()
                or "fund" in adapter_id.lower()
                or "portfolio" in adapter_id.lower()
            ):
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 adapter identity is not approved read-only."
                )

            if (
                not isinstance(read_operation, str)
                or not read_operation.startswith("read_")
                or "write" in read_operation.lower()
                or "delete" in read_operation.lower()
                or "update" in read_operation.lower()
                or "insert" in read_operation.lower()
                or "order" in read_operation.lower()
                or "fund" in read_operation.lower()
                or "portfolio" in read_operation.lower()
            ):
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 operation is not a bounded read operation."
                )

            if not isinstance(arguments, dict):
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 readiness arguments are invalid."
                )

            if set(arguments) != {
                "activated",
                "read_only",
                "execute",
                "callable_resolution_requested",
            }:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 readiness argument allowlist mismatch."
                )

            if arguments.get("activated") is not True:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 invocation is not activated."
                )

            if arguments.get("read_only") is not True:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 invocation is not read-only."
                )

            if arguments.get("execute") is not False:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 invocation crossed the execution boundary."
                )

            if arguments.get("callable_resolution_requested") is not False:
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 performed or requested callable resolution."
                )

            if (
                not isinstance(checks, list)
                or not required_readiness_checks.issubset(set(checks))
            ):
                raise ActiveInvocationExecutionAuthorizationInvariantError(
                    "OIA-047 readiness checks are incomplete."
                )

            lineage_hash_fields = {
                "source_active_execution_invocation_hash",
                "source_execution_invocation_hash",
                "source_authorization_entry_hash",
                "source_readiness_entry_hash",
                "source_active_adapter_invocation_hash",
            }

            for field_name in lineage_hash_fields:
                if not valid_hash(entry.get(field_name)):
                    raise ActiveInvocationExecutionAuthorizationInvariantError(
                        "OIA-047 readiness lineage hash is invalid: "
                        f"{field_name}."
                    )

        return source

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> ActiveInvocationExecutionAuthorizationManifest:
        authorized_at = aware_utc(
            authorized_at,
            "authorized_at",
        )

        source = self._load_readiness_manifest()

        authorization_entries: list[
            ActiveInvocationExecutionAuthorizationEntry
        ] = []

        for sequence, readiness_entry in enumerate(
            source["readiness_entries"],
            start=1,
        ):
            authorization_arguments = {
                "activated": True,
                "read_only": True,
                "execute": False,
                "callable_resolution_requested": False,
                "callable_resolution_authorized": True,
            }

            entry_body = {
                "sequence": sequence,
                "worker_id": readiness_entry["worker_id"],
                "work_item_id": readiness_entry["work_item_id"],
                "adapter_id": readiness_entry["adapter_id"],
                "read_operation": readiness_entry["read_operation"],
                "authorization_arguments":
                    authorization_arguments,
                "authorization_checks": (
                    "execution_readiness_manifest_hash_verified",
                    "execution_readiness_entry_hash_verified",
                    "invocation_activation_lineage_verified",
                    "execution_invocation_lineage_verified",
                    "prior_authorization_lineage_verified",
                    "prior_readiness_lineage_verified",
                    "adapter_read_only_identity_verified",
                    "operation_read_only_verified",
                    "authorization_argument_allowlist_verified",
                    "callable_resolution_authorized_but_not_requested",
                    "callable_resolution_not_performed",
                    "callable_binding_remained_disabled",
                    "adapter_execution_remained_disabled",
                    "corpus_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "authorization_status":
                    STATUS_ACTIVE_INVOCATION_AUTHORIZED,
                "source_active_invocation_execution_readiness_hash":
                    readiness_entry[
                        "active_invocation_execution_readiness_hash"
                    ],
                "source_active_execution_invocation_hash":
                    readiness_entry[
                        "source_active_execution_invocation_hash"
                    ],
                "source_execution_invocation_hash":
                    readiness_entry[
                        "source_execution_invocation_hash"
                    ],
                "source_authorization_entry_hash":
                    readiness_entry[
                        "source_authorization_entry_hash"
                    ],
                "source_readiness_entry_hash":
                    readiness_entry[
                        "source_readiness_entry_hash"
                    ],
                "source_active_adapter_invocation_hash":
                    readiness_entry[
                        "source_active_adapter_invocation_hash"
                    ],
            }

            authorization_entries.append(
                ActiveInvocationExecutionAuthorizationEntry(
                    **entry_body,
                    active_invocation_execution_authorization_hash=stable_hash(
                        entry_body
                    ),
                )
            )

        source_readiness_manifest_hash = source[
            "execution_readiness_manifest_hash"
        ]

        execution_authorization_id = (
            "oia048-active-invocation-execution-authorization-"
            + stable_hash(
                {
                    "source_execution_readiness_manifest_hash":
                        source_readiness_manifest_hash,
                    "execution_authorization_policy_id":
                        POLICY_ID,
                }
            )[:32]
        )

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at.isoformat(),
            "execution_authorization_id":
                execution_authorization_id,
            "execution_authorization_status":
                STATUS_AUTHORIZATION_ISSUED,
            "execution_authorization_policy_id":
                POLICY_ID,
            "worker_id": source["worker_id"],
            "authorization_entry_count":
                len(authorization_entries),
            "authorization_entries":
                tuple(authorization_entries),
            "source_execution_readiness_id":
                source["execution_readiness_id"],
            "source_execution_readiness_manifest_hash":
                source_readiness_manifest_hash,
            "source_invocation_activation_id":
                source["source_invocation_activation_id"],
            "source_invocation_activation_manifest_hash":
                source[
                    "source_invocation_activation_manifest_hash"
                ],
            "source_execution_invocation_manifest_id":
                source[
                    "source_execution_invocation_manifest_id"
                ],
            "source_execution_invocation_manifest_hash":
                source[
                    "source_execution_invocation_manifest_hash"
                ],
            "source_prior_execution_authorization_id":
                source["source_execution_authorization_id"],
            "source_prior_execution_authorization_manifest_hash":
                source[
                    "source_execution_authorization_manifest_hash"
                ],
            "source_prior_execution_readiness_id":
                source["source_execution_readiness_id"],
            "source_prior_execution_readiness_manifest_hash":
                source[
                    "source_execution_readiness_manifest_hash"
                ],
            "source_activation_hash":
                source["source_activation_hash"],
            "source_lineage":
                dict(source["source_lineage"]),
            "execution_authorization_issued": True,
            "callable_resolution_evaluation_allowed": True,
            "callable_resolution_allowed": False,
            "callable_resolution_performed": False,
            "callable_binding_allowed": False,
            "callable_binding_performed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "corpus_read_execution_performed": False,
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
            "authorization_artifact_persistence_allowed": True,
        }

        serializable_body = dict(manifest_body)
        serializable_body["authorization_entries"] = [
            asdict(entry)
            for entry in authorization_entries
        ]

        result = ActiveInvocationExecutionAuthorizationManifest(
            **manifest_body,
            execution_authorization_manifest_hash=stable_hash(
                serializable_body
            ),
        )

        if persist:
            payload = asdict(result)

            atomic_write(
                self.authorization_directory / "current.json",
                payload,
            )

            atomic_write(
                self.authorization_directory
                / "authorizations"
                / f"{execution_authorization_id}.json",
                payload,
            )

            atomic_write(
                self.authorization_directory
                / "workers"
                / result.worker_id
                / f"{execution_authorization_id}.json",
                payload,
            )

        return result
