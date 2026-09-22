from pathlib import Path
import py_compile
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

OIA047 = (
    ANALYTICS
    / "oracle_certified_research_evidence_read_execution_adapter_active_invocation_execution_readiness_gate.py"
)

PRODUCTION = (
    ANALYTICS
    / "oracle_certified_research_evidence_read_execution_adapter_active_invocation_execution_authorization_gate.py"
)

TEST = (
    ROOT
    / "test_oia_048_oracle_certified_research_evidence_read_execution_adapter_active_invocation_execution_authorization_gate.py"
)

INIT = ANALYTICS / "__init__.py"


PRODUCTION_SOURCE = r'''
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
'''


TEST_SOURCE = r'''
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_active_invocation_execution_authorization_gate import (
    ActiveInvocationExecutionAuthorizationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate,
    POLICY_ID,
    STATUS_ACTIVE_INVOCATION_AUTHORIZED,
    STATUS_AUTHORIZATION_ISSUED,
    stable_hash,
)


def source_lineage() -> dict:
    return {
        "source_evidence_read_execution_adapter_invocation_manifest_id":
            "oia041-test",
        "source_evidence_read_execution_adapter_authorization_manifest_id":
            "oia040-test",
        "source_evidence_read_execution_adapter_readiness_manifest_id":
            "oia039-test",
        "source_evidence_read_execution_adapter_binding_manifest_id":
            "oia038-test",
        "source_evidence_read_execution_invocation_activation_id":
            "oia037-test",
        "source_evidence_read_execution_invocation_manifest_id":
            "oia036-test",
        "source_evidence_read_execution_authorization_id":
            "oia035-test",
        "source_evidence_read_execution_readiness_id":
            "oia034-test",
        "source_evidence_read_request_activation_id":
            "oia033-test",
        "source_evidence_read_request_manifest_id":
            "oia032-test",
        "source_evidence_task_activation_id":
            "oia031-test",
        "source_evidence_task_manifest_id":
            "oia030-test",
        "source_evidence_batch_activation_id":
            "oia029-test",
        "source_evidence_batch_id":
            "oia028-test",
        "source_evidence_session_id":
            "oia027-test",
        "source_evidence_manifest_id":
            "oia026-test",
        "source_certification_id":
            "oia025-test",
        "source_readiness_id":
            "oia024-test",
        "source_session_id":
            "oia023-test",
        "source_activation_id":
            "oia022-test",
        "source_claim_id":
            "oia021-test",
        "dispatch_manifest_id":
            "oia020-test",
        "selected_batch_id":
            "oia020-batch",
        "selected_batch_number": 1,
    }


def seed_oia047(directory: Path) -> dict:
    readiness_entry_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation":
            "read_canonical_observations",
        "readiness_arguments": {
            "activated": True,
            "read_only": True,
            "execute": False,
            "callable_resolution_requested": False,
        },
        "readiness_checks": [
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
        ],
        "readiness_status":
            "evidence_read_execution_adapter_active_invocation_execution_ready",
        "source_active_execution_invocation_hash":
            stable_hash({"source": "oia046-active"}),
        "source_execution_invocation_hash":
            stable_hash({"source": "oia045-invocation"}),
        "source_authorization_entry_hash":
            stable_hash({"source": "oia044-authorization"}),
        "source_readiness_entry_hash":
            stable_hash({"source": "oia043-readiness"}),
        "source_active_adapter_invocation_hash":
            stable_hash({"source": "oia042-active"}),
    }

    readiness_entry = dict(readiness_entry_body)
    readiness_entry[
        "active_invocation_execution_readiness_hash"
    ] = stable_hash(readiness_entry_body)

    manifest_body = {
        "schema_version": "OIA-047",
        "engine_id": "OIA-047",
        "evaluated_at":
            "2026-07-22T05:00:00+00:00",
        "execution_readiness_id":
            "oia047-test-readiness",
        "execution_readiness_status":
            "evidence_read_execution_adapter_active_invocation_execution_readiness_issued",
        "execution_readiness_policy_id":
            "oracle.certified-research-evidence-read-execution-adapter-"
            "active-invocation-execution-readiness.v1",
        "worker_id":
            "oracle-worker-test",
        "readiness_entry_count": 1,
        "readiness_entries": [readiness_entry],
        "source_invocation_activation_id":
            "oia046-test-activation",
        "source_invocation_activation_manifest_hash":
            stable_hash({"source": "oia046-manifest"}),
        "source_execution_invocation_manifest_id":
            "oia045-test-manifest",
        "source_execution_invocation_manifest_hash":
            stable_hash({"source": "oia045-manifest"}),
        "source_execution_authorization_id":
            "oia044-test-authorization",
        "source_execution_authorization_manifest_hash":
            stable_hash({"source": "oia044-manifest"}),
        "source_execution_readiness_id":
            "oia043-test-readiness",
        "source_execution_readiness_manifest_hash":
            stable_hash({"source": "oia043-manifest"}),
        "source_activation_hash":
            stable_hash({"source": "oia042-activation"}),
        "source_lineage":
            source_lineage(),
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

    payload = dict(manifest_body)
    payload[
        "execution_readiness_manifest_hash"
    ] = stable_hash(manifest_body)

    directory.mkdir(parents=True, exist_ok=True)

    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def rehash_readiness(payload: dict) -> dict:
    for entry in payload["readiness_entries"]:
        entry_body = dict(entry)
        entry_body.pop(
            "active_invocation_execution_readiness_hash",
            None,
        )

        entry[
            "active_invocation_execution_readiness_hash"
        ] = stable_hash(entry_body)

    manifest_body = dict(payload)
    manifest_body.pop(
        "execution_readiness_manifest_hash",
        None,
    )

    payload[
        "execution_readiness_manifest_hash"
    ] = stable_hash(manifest_body)

    return payload


def expect_rejection(
    gate: OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate,
    authorized_at: datetime,
    message: str,
) -> None:
    try:
        gate.authorize(
            authorized_at=authorized_at,
            persist=False,
        )
    except ActiveInvocationExecutionAuthorizationInvariantError:
        return

    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-048 TEST")
    print(" ACTIVE INVOCATION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        readiness_directory = root / "readiness"
        authorization_directory = root / "authorization"

        source = seed_oia047(readiness_directory)

        gate = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate(
                readiness_directory=readiness_directory,
                authorization_directory=authorization_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            6,
            0,
            tzinfo=timezone.utc,
        )

        first = gate.authorize(
            authorized_at=fixed,
            persist=True,
        )

        second = gate.authorize(
            authorized_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-048"
        assert first.engine_id == "OIA-048"

        assert (
            first.execution_authorization_status
            == STATUS_AUTHORIZATION_ISSUED
        )

        assert (
            first.execution_authorization_policy_id
            == POLICY_ID
        )

        assert first.authorization_entry_count == 1

        entry = first.authorization_entries[0]

        assert (
            entry.authorization_status
            == STATUS_ACTIVE_INVOCATION_AUTHORIZED
        )

        assert (
            entry.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )

        assert (
            entry.read_operation
            == "read_canonical_observations"
        )

        assert entry.authorization_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
            "callable_resolution_requested": False,
            "callable_resolution_authorized": True,
        }

        assert (
            entry.source_active_invocation_execution_readiness_hash
            == source["readiness_entries"][0][
                "active_invocation_execution_readiness_hash"
            ]
        )

        assert (
            entry.source_active_execution_invocation_hash
            == source["readiness_entries"][0][
                "source_active_execution_invocation_hash"
            ]
        )

        assert (
            entry.source_execution_invocation_hash
            == source["readiness_entries"][0][
                "source_execution_invocation_hash"
            ]
        )

        assert (
            entry.source_authorization_entry_hash
            == source["readiness_entries"][0][
                "source_authorization_entry_hash"
            ]
        )

        assert (
            entry.source_readiness_entry_hash
            == source["readiness_entries"][0][
                "source_readiness_entry_hash"
            ]
        )

        assert (
            entry.source_active_adapter_invocation_hash
            == source["readiness_entries"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
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
        }.issubset(set(entry.authorization_checks))

        assert first.source_execution_readiness_id == (
            source["execution_readiness_id"]
        )

        assert (
            first.source_execution_readiness_manifest_hash
            == source["execution_readiness_manifest_hash"]
        )

        assert first.source_invocation_activation_id == (
            source["source_invocation_activation_id"]
        )

        assert (
            first.source_invocation_activation_manifest_hash
            == source[
                "source_invocation_activation_manifest_hash"
            ]
        )

        assert (
            first.source_execution_invocation_manifest_id
            == source[
                "source_execution_invocation_manifest_id"
            ]
        )

        assert (
            first.source_execution_invocation_manifest_hash
            == source[
                "source_execution_invocation_manifest_hash"
            ]
        )

        assert (
            first.source_prior_execution_authorization_id
            == source["source_execution_authorization_id"]
        )

        assert (
            first.source_prior_execution_authorization_manifest_hash
            == source[
                "source_execution_authorization_manifest_hash"
            ]
        )

        assert (
            first.source_prior_execution_readiness_id
            == source["source_execution_readiness_id"]
        )

        assert (
            first.source_prior_execution_readiness_manifest_hash
            == source[
                "source_execution_readiness_manifest_hash"
            ]
        )

        assert (
            first.source_activation_hash
            == source["source_activation_hash"]
        )

        assert first.source_lineage == source["source_lineage"]

        assert first.execution_authorization_issued is True
        assert first.callable_resolution_evaluation_allowed is True
        assert first.callable_resolution_allowed is False
        assert first.callable_resolution_performed is False
        assert first.callable_binding_allowed is False
        assert first.callable_binding_performed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.corpus_read_execution_performed is False
        assert first.authorization_artifact_persistence_allowed is True

        prohibited_values = (
            first.research_execution_allowed,
            first.analytic_conclusion_allowed,
            first.forecast_creation_allowed,
            first.signals_allowed,
            first.alerts_allowed,
            first.qseries_handoff_allowed,
            first.execution_allowed,
            first.trading_recommendations_allowed,
            first.source_mutation_allowed,
            first.market_order_creation_allowed,
            first.funds_movement_allowed,
            first.portfolio_mutation_allowed,
        )

        assert all(value is False for value in prohibited_values)

        manifest_body = dict(first.__dict__)
        manifest_hash = manifest_body.pop(
            "execution_authorization_manifest_hash"
        )

        manifest_body["authorization_entries"] = [
            dict(item.__dict__)
            for item in first.authorization_entries
        ]

        assert manifest_hash == stable_hash(manifest_body)

        entry_body = dict(entry.__dict__)
        entry_hash = entry_body.pop(
            "active_invocation_execution_authorization_hash"
        )

        assert entry_hash == stable_hash(entry_body)

        assert (
            authorization_directory / "current.json"
        ).exists()

        assert list(
            (
                authorization_directory
                / "authorizations"
            ).glob("*.json")
        )

        assert list(
            (
                authorization_directory
                / "workers"
                / first.worker_id
            ).glob("*.json")
        )

        current = json.loads(
            (
                authorization_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        assert current["execution_authorization_issued"] is True

        assert (
            current[
                "callable_resolution_evaluation_allowed"
            ]
            is True
        )

        assert current["callable_resolution_allowed"] is False
        assert current["callable_resolution_performed"] is False
        assert current["callable_binding_allowed"] is False
        assert current["callable_binding_performed"] is False
        assert current["adapter_execution_allowed"] is False
        assert current["adapter_execution_performed"] is False
        assert current["corpus_read_execution_allowed"] is False
        assert current["corpus_read_execution_performed"] is False
        assert current["execution_allowed"] is False
        assert current["qseries_handoff_allowed"] is False

        tampered_execute = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered_execute["readiness_entries"][0][
            "readiness_arguments"
        ]["execute"] = True

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(tampered_execute, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Tampered executable OIA-047 readiness accepted.",
        )

        seed_oia047(readiness_directory)

        resolution_requested = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        resolution_requested["readiness_entries"][0][
            "readiness_arguments"
        ]["callable_resolution_requested"] = True

        rehash_readiness(resolution_requested)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(resolution_requested, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Premature callable-resolution request was authorized.",
        )

        seed_oia047(readiness_directory)

        write_capable = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        write_capable["readiness_entries"][0][
            "adapter_id"
        ] = "oracle_write_capable_observation_adapter.v1"

        rehash_readiness(write_capable)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(write_capable, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Write-capable adapter was execution-authorized.",
        )

        seed_oia047(readiness_directory)

        unsafe_operation = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        unsafe_operation["readiness_entries"][0][
            "read_operation"
        ] = "update_canonical_observations"

        rehash_readiness(unsafe_operation)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(unsafe_operation, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Mutating operation was execution-authorized.",
        )

        seed_oia047(readiness_directory)

        duplicate = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        duplicate_entry = dict(
            duplicate["readiness_entries"][0]
        )

        duplicate_entry["sequence"] = 2

        duplicate["readiness_entries"].append(
            duplicate_entry
        )

        duplicate["readiness_entry_count"] = 2

        rehash_readiness(duplicate)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(duplicate, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Duplicate readiness work item was authorized.",
        )

        seed_oia047(readiness_directory)

        missing_lineage = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        del missing_lineage["source_lineage"][
            "source_evidence_manifest_id"
        ]

        rehash_readiness(missing_lineage)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(missing_lineage, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Incomplete OIA-020 through OIA-047 lineage was authorized.",
        )

    print("[PASS] Actual OIA-047 execution-readiness contract consumed")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-047 lineage preserved")
    print("[PASS] Exact readiness-certified read-only invocation authorized")
    print("[PASS] Callable-resolution evaluation authorized")
    print("[PASS] Callable resolution itself remained disabled")
    print("[PASS] No adapter was imported, resolved, bound, invoked, or executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, mutating, or write-capable input rejected")
    print("[PASS] Atomic execution-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


INIT_BLOCK = r'''
from .oracle_certified_research_evidence_read_execution_adapter_active_invocation_execution_authorization_gate import (
    ActiveInvocationExecutionAuthorizationEntry,
    ActiveInvocationExecutionAuthorizationInvariantError,
    ActiveInvocationExecutionAuthorizationManifest,
    OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate,
    POLICY_ID as OIA048_POLICY_ID,
    STATUS_ACTIVE_INVOCATION_AUTHORIZED as OIA048_STATUS_ACTIVE_INVOCATION_AUTHORIZED,
    STATUS_AUTHORIZATION_ISSUED as OIA048_STATUS_AUTHORIZATION_ISSUED,
)

__all__ = [
    "ActiveInvocationExecutionAuthorizationEntry",
    "ActiveInvocationExecutionAuthorizationInvariantError",
    "ActiveInvocationExecutionAuthorizationManifest",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate",
    "OIA048_POLICY_ID",
    "OIA048_STATUS_ACTIVE_INVOCATION_AUTHORIZED",
    "OIA048_STATUS_AUTHORIZATION_ISSUED",
] + __all__
'''


def verify_oia047() -> None:
    if not OIA047.exists():
        raise RuntimeError(
            f"Actual OIA-047 production module missing: {OIA047}"
        )

    text = OIA047.read_text(encoding="utf-8")

    required_tokens = [
        'SCHEMA_VERSION = "OIA-047"',
        'ENGINE_ID = "OIA-047"',
        "ActiveInvocationExecutionReadinessEntry",
        "ActiveInvocationExecutionReadinessManifest",
        "OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionReadinessGate",
        "evidence_read_execution_adapter_active_invocation_execution_ready",
        "evidence_read_execution_adapter_active_invocation_execution_readiness_issued",
        "active_invocation_execution_readiness_hash",
        "execution_readiness_manifest_hash",
        "source_active_execution_invocation_hash",
        "source_execution_invocation_hash",
        "source_authorization_entry_hash",
        "source_readiness_entry_hash",
        "source_active_adapter_invocation_hash",
        "execution_authorization_evaluation_allowed",
        "callable_resolution_allowed",
        "callable_resolution_performed",
        "callable_binding_allowed",
        "adapter_execution_allowed",
        "adapter_execution_performed",
        "corpus_read_execution_allowed",
        "qseries_handoff_allowed",
        "execution_allowed",
        "market_order_creation_allowed",
        "funds_movement_allowed",
        "portfolio_mutation_allowed",
    ]

    missing = [
        token
        for token in required_tokens
        if token not in text
    ]

    if missing:
        raise RuntimeError(
            "Actual OIA-047 production contract mismatch: "
            f"{missing}"
        )


def write_full(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        source.strip() + "\n",
        encoding="utf-8",
    )

    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    existing = (
        INIT.read_text(encoding="utf-8")
        if INIT.exists()
        else "__all__ = []\n"
    )

    marker = (
        "from .oracle_certified_research_evidence_read_execution_"
        "adapter_active_invocation_execution_authorization_gate import ("
    )

    if marker not in existing:
        INIT.write_text(
            existing.rstrip()
            + "\n"
            + INIT_BLOCK.strip()
            + "\n",
            encoding="utf-8",
        )

        print(f"[OK] PACKAGE UPDATED: {INIT}")
    else:
        print(f"[OK] PACKAGE ALREADY CURRENT: {INIT}")


def main() -> int:
    print("=" * 40)
    print(" OIA-048 INSTALLER")
    print(" ACTIVE INVOCATION AUTHORIZATION")
    print(" PRE-CALLABLE-RESOLUTION GATE")
    print("=" * 40)

    verify_oia047()

    print(
        "[OK] Actual OIA-047 execution-readiness contract verified"
    )

    write_full(PRODUCTION, PRODUCTION_SOURCE)
    write_full(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(
        str(PRODUCTION),
        doraise=True,
    )

    py_compile.compile(
        str(TEST),
        doraise=True,
    )

    py_compile.compile(
        str(INIT),
        doraise=True,
    )

    print("[OK] Production, test, and package syntax verified")

    result = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )

    if result.returncode:
        raise SystemExit(result.returncode)

    print("[OK] OIA-048 test executed automatically")
    print()
    print(
        "[DONE] OIA-048 certified research evidence read execution "
        "adapter active invocation execution authorization gate installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())