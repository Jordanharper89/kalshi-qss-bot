from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "OIA-046"
ENGINE_ID = "OIA-046"

POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "execution-invocation-activation.v1"
)

STATUS_INVOCATION_ACTIVE = (
    "evidence_read_execution_adapter_execution_invocation_active"
)

STATUS_ACTIVATION_ISSUED = (
    "evidence_read_execution_adapter_execution_invocation_activation_issued"
)

DEFAULT_INVOCATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_invocations"
)

DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_invocation_activation"
)


class AdapterExecutionInvocationActivationInvariantError(RuntimeError):
    """Raised when the OIA-045 invocation manifest is invalid or unsafe."""


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
        raise AdapterExecutionInvocationActivationInvariantError(
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
class ActiveAdapterExecutionInvocation:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    active_invocation_arguments: dict[str, Any]
    activation_checks: tuple[str, ...]
    activation_status: str
    source_execution_invocation_hash: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    active_execution_invocation_hash: str


@dataclass(frozen=True)
class AdapterExecutionInvocationActivationManifest:
    schema_version: str
    engine_id: str
    activated_at: str
    activation_id: str
    activation_status: str
    activation_policy_id: str
    worker_id: str
    active_invocation_count: int
    active_invocations: tuple[ActiveAdapterExecutionInvocation, ...]
    source_execution_invocation_manifest_id: str
    source_execution_invocation_manifest_hash: str
    source_execution_authorization_id: str
    source_execution_authorization_manifest_hash: str
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    invocation_activation_issued: bool
    execution_readiness_evaluation_allowed: bool
    callable_resolution_allowed: bool
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
    activation_artifact_persistence_allowed: bool
    activation_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationActivationGate:
    """
    OIA-046 exact invocation activation boundary.

    This gate activates the canonical invocation produced by OIA-045 so that a
    later certified component may evaluate execution readiness.

    Activation is not execution.

    This component does not:
    - import an adapter,
    - resolve a callable,
    - bind a callable,
    - connect to PostgreSQL,
    - perform a network request,
    - read the certified corpus,
    - produce research conclusions,
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
        invocation_directory: Path | str = DEFAULT_INVOCATION_DIRECTORY,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
    ) -> None:
        self.invocation_directory = Path(invocation_directory)
        self.activation_directory = Path(activation_directory)

    def _load_invocation_manifest(self) -> dict[str, Any]:
        current = self.invocation_directory / "current.json"

        if not current.exists():
            raise AdapterExecutionInvocationActivationInvariantError(
                f"OIA-045 current invocation artifact missing: {current}"
            )

        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation artifact could not be decoded."
            ) from error

        if not isinstance(source, dict):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation artifact must be a JSON object."
            )

        manifest_hash = source.pop(
            "invocation_manifest_hash",
            None,
        )

        if (
            not valid_hash(manifest_hash)
            or stable_hash(source) != manifest_hash
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation manifest hash verification failed."
            )

        source["invocation_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-045",
            "engine_id": "OIA-045",
            "invocation_manifest_status":
                "evidence_read_execution_adapter_execution_invocation_manifest_issued",
            "invocation_manifest_created": True,
            "invocation_activation_allowed": True,
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
            "invocation_artifact_persistence_allowed": True,
        }

        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise AdapterExecutionInvocationActivationInvariantError(
                    f"OIA-045 invariant failed: {field_name}."
                )

        invocation_manifest_id = source.get(
            "invocation_manifest_id"
        )
        invocation_policy_id = source.get(
            "invocation_policy_id"
        )
        worker_id = source.get("worker_id")
        invocation_count = source.get("invocation_count")
        invocations = source.get("invocations")

        if (
            not isinstance(invocation_manifest_id, str)
            or not invocation_manifest_id
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation manifest ID is invalid."
            )

        if (
            invocation_policy_id
            != (
                "oracle.certified-research-evidence-read-execution-adapter-"
                "execution-invocation-manifest.v1"
            )
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation policy mismatch."
            )

        if not isinstance(worker_id, str) or not worker_id:
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 worker ID is invalid."
            )

        if (
            not isinstance(invocation_count, int)
            or isinstance(invocation_count, bool)
            or invocation_count < 1
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation count is invalid."
            )

        if (
            not isinstance(invocations, list)
            or len(invocations) != invocation_count
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation collection is invalid."
            )

        hash_fields = {
            "source_execution_authorization_manifest_hash",
            "source_execution_readiness_manifest_hash",
            "source_activation_hash",
        }

        for field_name in hash_fields:
            if not valid_hash(source.get(field_name)):
                raise AdapterExecutionInvocationActivationInvariantError(
                    f"OIA-045 hash field is invalid: {field_name}."
                )

        identifier_fields = {
            "source_execution_authorization_id",
            "source_execution_readiness_id",
        }

        for field_name in identifier_fields:
            value = source.get(field_name)

            if not isinstance(value, str) or not value:
                raise AdapterExecutionInvocationActivationInvariantError(
                    f"OIA-045 identifier is invalid: {field_name}."
                )

        source_lineage = source.get("source_lineage")

        if not isinstance(source_lineage, dict) or not source_lineage:
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 source lineage is missing."
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
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 lineage is incomplete: "
                f"{sorted(missing_lineage)}"
            )

        for field_name in (
            required_lineage_fields - {"selected_batch_number"}
        ):
            value = source_lineage.get(field_name)

            if not isinstance(value, str) or not value:
                raise AdapterExecutionInvocationActivationInvariantError(
                    f"OIA-045 lineage field is invalid: {field_name}."
                )

        selected_batch_number = source_lineage.get(
            "selected_batch_number"
        )

        if (
            not isinstance(selected_batch_number, int)
            or isinstance(selected_batch_number, bool)
            or selected_batch_number < 1
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 selected batch number is invalid."
            )

        required_invocation_checks = {
            "authorization_manifest_hash_verified",
            "authorization_entry_hash_verified",
            "readiness_entry_lineage_verified",
            "active_invocation_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_argument_allowlist_verified",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }

        seen_work_item_ids: set[str] = set()
        seen_invocation_hashes: set[str] = set()

        for expected_sequence, invocation in enumerate(
            invocations,
            start=1,
        ):
            if not isinstance(invocation, dict):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation must be an object."
                )

            invocation_hash = invocation.pop(
                "execution_invocation_hash",
                None,
            )

            if (
                not valid_hash(invocation_hash)
                or stable_hash(invocation) != invocation_hash
            ):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 execution invocation hash verification failed."
                )

            invocation["execution_invocation_hash"] = invocation_hash

            if invocation_hash in seen_invocation_hashes:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 contains a duplicate invocation hash."
                )

            seen_invocation_hashes.add(invocation_hash)

            if invocation.get("sequence") != expected_sequence:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation sequence is non-canonical."
                )

            if invocation.get("worker_id") != worker_id:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation worker identity mismatch."
                )

            if (
                invocation.get("invocation_status")
                != "evidence_read_execution_adapter_execution_invocation_ready"
            ):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation is not ready for activation."
                )

            work_item_id = invocation.get("work_item_id")
            adapter_id = invocation.get("adapter_id")
            read_operation = invocation.get("read_operation")
            arguments = invocation.get("invocation_arguments")
            checks = invocation.get("invocation_checks")

            if not isinstance(work_item_id, str) or not work_item_id:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 work-item identity is invalid."
                )

            if work_item_id in seen_work_item_ids:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 contains duplicate work-item identities."
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
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 adapter identity is not approved read-only."
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
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 operation is not a bounded read operation."
                )

            if not isinstance(arguments, dict):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation arguments are invalid."
                )

            if set(arguments) != {
                "activated",
                "read_only",
                "execute",
            }:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation argument allowlist mismatch."
                )

            if arguments.get("activated") is not True:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation lacks prior activation."
                )

            if arguments.get("read_only") is not True:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation is not read-only."
                )

            if arguments.get("execute") is not False:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation crossed the execution boundary."
                )

            if (
                not isinstance(checks, list)
                or not required_invocation_checks.issubset(set(checks))
            ):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation checks are incomplete."
                )

            lineage_hash_fields = {
                "source_authorization_entry_hash",
                "source_readiness_entry_hash",
                "source_active_adapter_invocation_hash",
            }

            for field_name in lineage_hash_fields:
                if not valid_hash(invocation.get(field_name)):
                    raise AdapterExecutionInvocationActivationInvariantError(
                        f"OIA-045 invocation lineage hash is invalid: "
                        f"{field_name}."
                    )

        return source

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> AdapterExecutionInvocationActivationManifest:
        activated_at = aware_utc(activated_at, "activated_at")
        source = self._load_invocation_manifest()

        active_invocations: list[
            ActiveAdapterExecutionInvocation
        ] = []

        for sequence, invocation in enumerate(
            source["invocations"],
            start=1,
        ):
            active_arguments = dict(
                invocation["invocation_arguments"]
            )

            # OIA-046 activates the invocation identity for later readiness
            # evaluation. The actual execution bit remains closed.
            active_arguments["activated"] = True
            active_arguments["read_only"] = True
            active_arguments["execute"] = False

            body = {
                "sequence": sequence,
                "worker_id": invocation["worker_id"],
                "work_item_id": invocation["work_item_id"],
                "adapter_id": invocation["adapter_id"],
                "read_operation": invocation["read_operation"],
                "active_invocation_arguments": active_arguments,
                "activation_checks": (
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
                ),
                "activation_status": STATUS_INVOCATION_ACTIVE,
                "source_execution_invocation_hash":
                    invocation["execution_invocation_hash"],
                "source_authorization_entry_hash":
                    invocation["source_authorization_entry_hash"],
                "source_readiness_entry_hash":
                    invocation["source_readiness_entry_hash"],
                "source_active_adapter_invocation_hash":
                    invocation[
                        "source_active_adapter_invocation_hash"
                    ],
            }

            active_invocations.append(
                ActiveAdapterExecutionInvocation(
                    **body,
                    active_execution_invocation_hash=stable_hash(
                        body
                    ),
                )
            )

        source_manifest_hash = source[
            "invocation_manifest_hash"
        ]

        activation_id = (
            "oia046-adapter-execution-invocation-activation-"
            + stable_hash(
                {
                    "source_execution_invocation_manifest_hash":
                        source_manifest_hash,
                    "activation_policy_id": POLICY_ID,
                }
            )[:32]
        )

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at.isoformat(),
            "activation_id": activation_id,
            "activation_status": STATUS_ACTIVATION_ISSUED,
            "activation_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "active_invocation_count": len(active_invocations),
            "active_invocations": tuple(active_invocations),
            "source_execution_invocation_manifest_id":
                source["invocation_manifest_id"],
            "source_execution_invocation_manifest_hash":
                source_manifest_hash,
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
            "source_lineage": dict(source["source_lineage"]),
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

        serializable_body = dict(manifest_body)
        serializable_body["active_invocations"] = [
            asdict(invocation)
            for invocation in active_invocations
        ]

        result = AdapterExecutionInvocationActivationManifest(
            **manifest_body,
            activation_manifest_hash=stable_hash(
                serializable_body
            ),
        )

        if persist:
            payload = asdict(result)

            atomic_write(
                self.activation_directory / "current.json",
                payload,
            )

            atomic_write(
                self.activation_directory
                / "activations"
                / f"{activation_id}.json",
                payload,
            )

            atomic_write(
                self.activation_directory
                / "workers"
                / result.worker_id
                / f"{activation_id}.json",
                payload,
            )

        return result
