from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "OIA-044"
ENGINE_ID = "OIA-044"

POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "execution-authorization.v1"
)

STATUS_AUTHORIZED = (
    "evidence_read_execution_adapter_execution_authorized"
)

STATUS_ISSUED = (
    "evidence_read_execution_adapter_execution_authorization_issued"
)

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_readiness"
)

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_authorization"
)


class AdapterExecutionAuthorizationInvariantError(RuntimeError):
    """Raised when the OIA-043 readiness contract is unsafe or invalid."""


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
        raise AdapterExecutionAuthorizationInvariantError(
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
class AdapterExecutionAuthorizationEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    authorized_invocation_arguments: dict[str, Any]
    authorization_checks: tuple[str, ...]
    authorization_status: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    authorization_entry_hash: str


@dataclass(frozen=True)
class AdapterExecutionAuthorizationManifest:
    schema_version: str
    engine_id: str
    authorized_at: str
    authorization_id: str
    authorization_status: str
    authorization_policy_id: str
    worker_id: str
    authorization_entry_count: int
    entries: tuple[AdapterExecutionAuthorizationEntry, ...]
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    read_only_authorization_issued: bool
    adapter_execution_authorization_allowed: bool
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
    authorization_artifact_persistence_allowed: bool
    authorization_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate:
    """
    OIA-044 authorization boundary.

    This gate authorizes the exact bounded read-only adapter invocation described
    by OIA-043. It does not import, instantiate, invoke, or execute an adapter.

    Authorization here means that a later certified execution component may
    consume the authorization artifact. It does not mean execution occurred.
    """

    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.authorization_directory = Path(authorization_directory)

    def _load_readiness(self) -> dict[str, Any]:
        current = self.readiness_directory / "current.json"

        if not current.exists():
            raise AdapterExecutionAuthorizationInvariantError(
                f"OIA-043 current readiness artifact missing: {current}"
            )

        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness artifact could not be decoded."
            ) from error

        if not isinstance(source, dict):
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness artifact must be a JSON object."
            )

        manifest_hash = source.pop("manifest_hash", None)

        if (
            not valid_hash(manifest_hash)
            or stable_hash(source) != manifest_hash
        ):
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness manifest hash verification failed."
            )

        source["manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-043",
            "engine_id": "OIA-043",
            "status":
                "evidence_read_execution_adapter_execution_readiness_issued",
            "corpus_read_execution_allowed": False,
            "research_execution_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "source_mutation_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }

        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise AdapterExecutionAuthorizationInvariantError(
                    f"OIA-043 invariant failed: {field_name}."
                )

        readiness_id = source.get("readiness_id")
        worker_id = source.get("worker_id")
        source_activation_hash = source.get("source_activation_hash")
        source_lineage = source.get("source_lineage")
        entries = source.get("entries")

        if not isinstance(readiness_id, str) or not readiness_id:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness ID is invalid."
            )

        if not isinstance(worker_id, str) or not worker_id:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 worker ID is invalid."
            )

        if not valid_hash(source_activation_hash):
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 source activation hash is invalid."
            )

        if not isinstance(source_lineage, dict) or not source_lineage:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 source lineage is missing."
            )

        if not isinstance(entries, list) or not entries:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness entries are missing."
            )

        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness entry must be an object."
                )

            entry_hash = entry.pop("entry_hash", None)

            if not valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness entry hash verification failed."
                )

            entry["entry_hash"] = entry_hash

            if entry.get("sequence") != expected_sequence:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness entry sequence is non-canonical."
                )

            if (
                entry.get("status")
                != "evidence_read_execution_adapter_execution_ready"
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 adapter execution entry is not ready."
                )

            if entry.get("worker_id") != worker_id:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness worker identity mismatch."
                )

            work_item_id = entry.get("work_item_id")
            adapter_id = entry.get("adapter_id")
            read_operation = entry.get("read_operation")
            invocation_arguments = entry.get("invocation_arguments")
            checks = entry.get("checks")

            if not isinstance(work_item_id, str) or not work_item_id:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 work-item identity is invalid."
                )

            if (
                not isinstance(adapter_id, str)
                or not adapter_id.startswith("oracle_read_only_")
                or "write" in adapter_id.lower()
                or "mutation" in adapter_id.lower()
                or "order" in adapter_id.lower()
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 adapter is not an approved read-only identity."
                )

            if (
                not isinstance(read_operation, str)
                or not read_operation.startswith("read_")
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 operation is not a bounded read operation."
                )

            if not isinstance(invocation_arguments, dict):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation arguments are invalid."
                )

            if invocation_arguments.get("activated") is not True:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation is not activated."
                )

            if invocation_arguments.get("read_only") is not True:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation is not read-only."
                )

            if invocation_arguments.get("execute") is not False:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation attempted to cross the execution boundary."
                )

            allowed_argument_names = {
                "activated",
                "read_only",
                "execute",
            }

            unexpected_arguments = (
                set(invocation_arguments) - allowed_argument_names
            )

            if unexpected_arguments:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation contains unapproved arguments: "
                    f"{sorted(unexpected_arguments)}"
                )

            required_checks = {
                "activation_hash_verified",
                "adapter_read_only_verified",
                "operation_read_only_verified",
                "invocation_non_executing_verified",
                "corpus_execution_disabled",
            }

            if (
                not isinstance(checks, list)
                or not required_checks.issubset(set(checks))
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness checks are incomplete."
                )

            if not valid_hash(
                entry.get("source_active_adapter_invocation_hash")
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 active invocation lineage hash is invalid."
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
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 lineage is incomplete: "
                f"{sorted(missing_lineage)}"
            )

        for field_name in required_lineage_fields - {"selected_batch_number"}:
            value = source_lineage.get(field_name)
            if not isinstance(value, str) or not value:
                raise AdapterExecutionAuthorizationInvariantError(
                    f"OIA-043 lineage field is invalid: {field_name}."
                )

        selected_batch_number = source_lineage.get("selected_batch_number")
        if (
            not isinstance(selected_batch_number, int)
            or isinstance(selected_batch_number, bool)
            or selected_batch_number < 1
        ):
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 selected batch number is invalid."
            )

        return source

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> AdapterExecutionAuthorizationManifest:
        authorized_at = aware_utc(authorized_at, "authorized_at")
        source = self._load_readiness()

        entries: list[AdapterExecutionAuthorizationEntry] = []

        for sequence, readiness_entry in enumerate(
            source["entries"],
            start=1,
        ):
            authorized_arguments = dict(
                readiness_entry["invocation_arguments"]
            )

            # OIA-044 authorizes a future bounded read-only invocation but does
            # not turn the source request into an executable request.
            authorized_arguments["execute"] = False

            body = {
                "sequence": sequence,
                "worker_id": readiness_entry["worker_id"],
                "work_item_id": readiness_entry["work_item_id"],
                "adapter_id": readiness_entry["adapter_id"],
                "read_operation": readiness_entry["read_operation"],
                "authorized_invocation_arguments": authorized_arguments,
                "authorization_checks": (
                    "readiness_manifest_hash_verified",
                    "readiness_entry_hash_verified",
                    "active_invocation_hash_verified",
                    "adapter_read_only_identity_verified",
                    "operation_read_only_verified",
                    "invocation_arguments_allowlisted",
                    "invocation_remained_non_executing",
                    "corpus_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "authorization_status": STATUS_AUTHORIZED,
                "source_readiness_entry_hash":
                    readiness_entry["entry_hash"],
                "source_active_adapter_invocation_hash":
                    readiness_entry[
                        "source_active_adapter_invocation_hash"
                    ],
            }

            entries.append(
                AdapterExecutionAuthorizationEntry(
                    **body,
                    authorization_entry_hash=stable_hash(body),
                )
            )

        source_manifest_hash = source["manifest_hash"]

        authorization_id = (
            "oia044-adapter-execution-authorization-"
            + stable_hash(
                {
                    "source_execution_readiness_manifest_hash":
                        source_manifest_hash,
                    "authorization_policy_id": POLICY_ID,
                }
            )[:32]
        )

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at.isoformat(),
            "authorization_id": authorization_id,
            "authorization_status": STATUS_ISSUED,
            "authorization_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "authorization_entry_count": len(entries),
            "entries": tuple(entries),
            "source_execution_readiness_id": source["readiness_id"],
            "source_execution_readiness_manifest_hash":
                source_manifest_hash,
            "source_activation_hash": source["source_activation_hash"],
            "source_lineage": dict(source["source_lineage"]),
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

        serializable_body = dict(manifest_body)
        serializable_body["entries"] = [
            asdict(entry) for entry in entries
        ]

        result = AdapterExecutionAuthorizationManifest(
            **manifest_body,
            authorization_manifest_hash=stable_hash(
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
                / f"{authorization_id}.json",
                payload,
            )

            atomic_write(
                self.authorization_directory
                / "workers"
                / result.worker_id
                / f"{authorization_id}.json",
                payload,
            )

        return result
