from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "OIA-045"
ENGINE_ID = "OIA-045"

POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "execution-invocation-manifest.v1"
)

STATUS_INVOCATION_READY = (
    "evidence_read_execution_adapter_execution_invocation_ready"
)

STATUS_MANIFEST_ISSUED = (
    "evidence_read_execution_adapter_execution_invocation_manifest_issued"
)

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_authorization"
)

DEFAULT_INVOCATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_invocations"
)


class AdapterExecutionInvocationInvariantError(RuntimeError):
    """Raised when OIA-044 authorization evidence is invalid or unsafe."""


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
        raise AdapterExecutionInvocationInvariantError(
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
class AdapterExecutionInvocation:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    invocation_arguments: dict[str, Any]
    invocation_checks: tuple[str, ...]
    invocation_status: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    execution_invocation_hash: str


@dataclass(frozen=True)
class AdapterExecutionInvocationManifest:
    schema_version: str
    engine_id: str
    created_at: str
    invocation_manifest_id: str
    invocation_manifest_status: str
    invocation_policy_id: str
    worker_id: str
    invocation_count: int
    invocations: tuple[AdapterExecutionInvocation, ...]
    source_execution_authorization_id: str
    source_execution_authorization_manifest_hash: str
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    invocation_manifest_created: bool
    invocation_activation_allowed: bool
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
    invocation_artifact_persistence_allowed: bool
    invocation_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder:
    """
    OIA-045 exact adapter execution invocation manifest boundary.

    This builder converts the OIA-044 authorization artifact into a canonical
    invocation manifest for later activation.

    It does not import, instantiate, resolve, call, or execute an adapter.
    It does not read the certified corpus.
    """

    def __init__(
        self,
        *,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
        invocation_directory: Path | str = DEFAULT_INVOCATION_DIRECTORY,
    ) -> None:
        self.authorization_directory = Path(authorization_directory)
        self.invocation_directory = Path(invocation_directory)

    def _load_authorization(self) -> dict[str, Any]:
        current = self.authorization_directory / "current.json"

        if not current.exists():
            raise AdapterExecutionInvocationInvariantError(
                f"OIA-044 current authorization artifact missing: {current}"
            )

        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization artifact could not be decoded."
            ) from error

        if not isinstance(source, dict):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization artifact must be a JSON object."
            )

        manifest_hash = source.pop(
            "authorization_manifest_hash",
            None,
        )

        if (
            not valid_hash(manifest_hash)
            or stable_hash(source) != manifest_hash
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization manifest hash verification failed."
            )

        source["authorization_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-044",
            "engine_id": "OIA-044",
            "authorization_status":
                "evidence_read_execution_adapter_execution_authorization_issued",
            "read_only_authorization_issued": True,
            "adapter_execution_authorization_allowed": True,
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
            "authorization_artifact_persistence_allowed": True,
        }

        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise AdapterExecutionInvocationInvariantError(
                    f"OIA-044 invariant failed: {field_name}."
                )

        authorization_id = source.get("authorization_id")
        worker_id = source.get("worker_id")
        policy_id = source.get("authorization_policy_id")
        source_readiness_id = source.get(
            "source_execution_readiness_id"
        )
        source_readiness_hash = source.get(
            "source_execution_readiness_manifest_hash"
        )
        source_activation_hash = source.get(
            "source_activation_hash"
        )
        source_lineage = source.get("source_lineage")
        entries = source.get("entries")

        if not isinstance(authorization_id, str) or not authorization_id:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization ID is invalid."
            )

        if not isinstance(worker_id, str) or not worker_id:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 worker ID is invalid."
            )

        if (
            policy_id
            != (
                "oracle.certified-research-evidence-read-execution-adapter-"
                "execution-authorization.v1"
            )
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization policy mismatch."
            )

        if (
            not isinstance(source_readiness_id, str)
            or not source_readiness_id
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 source readiness ID is invalid."
            )

        if not valid_hash(source_readiness_hash):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 source readiness manifest hash is invalid."
            )

        if not valid_hash(source_activation_hash):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 source activation hash is invalid."
            )

        if not isinstance(source_lineage, dict) or not source_lineage:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 source lineage is missing."
            )

        if (
            not isinstance(entries, list)
            or not entries
            or source.get("authorization_entry_count") != len(entries)
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization entries are invalid."
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

        missing_lineage = required_lineage_fields - set(source_lineage)

        if missing_lineage:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 lineage is incomplete: "
                f"{sorted(missing_lineage)}"
            )

        for field_name in (
            required_lineage_fields - {"selected_batch_number"}
        ):
            value = source_lineage.get(field_name)

            if not isinstance(value, str) or not value:
                raise AdapterExecutionInvocationInvariantError(
                    f"OIA-044 lineage field is invalid: {field_name}."
                )

        selected_batch_number = source_lineage.get(
            "selected_batch_number"
        )

        if (
            not isinstance(selected_batch_number, int)
            or isinstance(selected_batch_number, bool)
            or selected_batch_number < 1
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 selected batch number is invalid."
            )

        required_authorization_checks = {
            "readiness_manifest_hash_verified",
            "readiness_entry_hash_verified",
            "active_invocation_hash_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_arguments_allowlisted",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }

        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization entry must be an object."
                )

            entry_hash = entry.pop(
                "authorization_entry_hash",
                None,
            )

            if (
                not valid_hash(entry_hash)
                or stable_hash(entry) != entry_hash
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization entry hash verification failed."
                )

            entry["authorization_entry_hash"] = entry_hash

            if entry.get("sequence") != expected_sequence:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization entry sequence is non-canonical."
                )

            if entry.get("worker_id") != worker_id:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization worker identity mismatch."
                )

            if (
                entry.get("authorization_status")
                != "evidence_read_execution_adapter_execution_authorized"
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization entry is not authorized."
                )

            work_item_id = entry.get("work_item_id")
            adapter_id = entry.get("adapter_id")
            read_operation = entry.get("read_operation")
            arguments = entry.get(
                "authorized_invocation_arguments"
            )
            checks = entry.get("authorization_checks")

            if not isinstance(work_item_id, str) or not work_item_id:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 work-item identity is invalid."
                )

            if (
                not isinstance(adapter_id, str)
                or not adapter_id.startswith("oracle_read_only_")
                or "write" in adapter_id.lower()
                or "mutation" in adapter_id.lower()
                or "order" in adapter_id.lower()
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 adapter identity is not approved read-only."
                )

            if (
                not isinstance(read_operation, str)
                or not read_operation.startswith("read_")
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 operation is not a bounded read operation."
                )

            if not isinstance(arguments, dict):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorized invocation arguments are invalid."
                )

            if set(arguments) != {
                "activated",
                "read_only",
                "execute",
            }:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorized invocation argument allowlist mismatch."
                )

            if arguments.get("activated") is not True:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 invocation is not activated."
                )

            if arguments.get("read_only") is not True:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 invocation is not read-only."
                )

            if arguments.get("execute") is not False:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 invocation crossed the execution boundary."
                )

            if (
                not isinstance(checks, list)
                or not required_authorization_checks.issubset(set(checks))
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization checks are incomplete."
                )

            if not valid_hash(
                entry.get("source_readiness_entry_hash")
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 source readiness entry hash is invalid."
                )

            if not valid_hash(
                entry.get("source_active_adapter_invocation_hash")
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 source active invocation hash is invalid."
                )

        return source

    def build(
        self,
        *,
        created_at: datetime,
        persist: bool = True,
    ) -> AdapterExecutionInvocationManifest:
        created_at = aware_utc(created_at, "created_at")
        source = self._load_authorization()

        invocations: list[AdapterExecutionInvocation] = []

        for sequence, authorization_entry in enumerate(
            source["entries"],
            start=1,
        ):
            invocation_arguments = dict(
                authorization_entry[
                    "authorized_invocation_arguments"
                ]
            )

            # OIA-045 records the exact authorized invocation while retaining
            # the closed execution bit. Activation and execution are separate,
            # later certified boundaries.
            invocation_arguments["execute"] = False

            body = {
                "sequence": sequence,
                "worker_id": authorization_entry["worker_id"],
                "work_item_id": authorization_entry["work_item_id"],
                "adapter_id": authorization_entry["adapter_id"],
                "read_operation": authorization_entry["read_operation"],
                "invocation_arguments": invocation_arguments,
                "invocation_checks": (
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
                ),
                "invocation_status": STATUS_INVOCATION_READY,
                "source_authorization_entry_hash":
                    authorization_entry[
                        "authorization_entry_hash"
                    ],
                "source_readiness_entry_hash":
                    authorization_entry[
                        "source_readiness_entry_hash"
                    ],
                "source_active_adapter_invocation_hash":
                    authorization_entry[
                        "source_active_adapter_invocation_hash"
                    ],
            }

            invocations.append(
                AdapterExecutionInvocation(
                    **body,
                    execution_invocation_hash=stable_hash(body),
                )
            )

        source_authorization_hash = source[
            "authorization_manifest_hash"
        ]

        invocation_manifest_id = (
            "oia045-adapter-execution-invocation-"
            + stable_hash(
                {
                    "source_execution_authorization_manifest_hash":
                        source_authorization_hash,
                    "invocation_policy_id": POLICY_ID,
                }
            )[:32]
        )

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "created_at": created_at.isoformat(),
            "invocation_manifest_id": invocation_manifest_id,
            "invocation_manifest_status": STATUS_MANIFEST_ISSUED,
            "invocation_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "invocation_count": len(invocations),
            "invocations": tuple(invocations),
            "source_execution_authorization_id":
                source["authorization_id"],
            "source_execution_authorization_manifest_hash":
                source_authorization_hash,
            "source_execution_readiness_id":
                source["source_execution_readiness_id"],
            "source_execution_readiness_manifest_hash":
                source[
                    "source_execution_readiness_manifest_hash"
                ],
            "source_activation_hash":
                source["source_activation_hash"],
            "source_lineage": dict(source["source_lineage"]),
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

        serializable_body = dict(manifest_body)
        serializable_body["invocations"] = [
            asdict(invocation)
            for invocation in invocations
        ]

        result = AdapterExecutionInvocationManifest(
            **manifest_body,
            invocation_manifest_hash=stable_hash(
                serializable_body
            ),
        )

        if persist:
            payload = asdict(result)

            atomic_write(
                self.invocation_directory / "current.json",
                payload,
            )

            atomic_write(
                self.invocation_directory
                / "manifests"
                / f"{invocation_manifest_id}.json",
                payload,
            )

            atomic_write(
                self.invocation_directory
                / "workers"
                / result.worker_id
                / f"{invocation_manifest_id}.json",
                payload,
            )

        return result
