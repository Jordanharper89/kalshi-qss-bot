from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .oracle_certified_research_evidence_read_execution_adapter_binding_gate import (
    APPROVED_READ_ONLY_ADAPTER_IDS,
    OPERATION_ADAPTER_MAP,
)
from .oracle_certified_research_evidence_read_execution_adapter_readiness_gate import (
    DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_DIRECTORY,
    EVIDENCE_READ_EXECUTION_ADAPTER_READY,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
)

SCHEMA_VERSION = "OIA-040"
ENGINE_ID = "OIA-040"

EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-authorization.v1"
)
EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED = (
    "evidence_read_execution_adapter_authorization_issued"
)
EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED = (
    "evidence_read_execution_adapter_authorized"
)

DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_evidence_read_execution_adapter_authorizations"
)

READ_ONLY_CORPUS = True
EVIDENCE_COLLECTION_ALLOWED = True
CORPUS_READ_REQUESTS_ALLOWED = True
CORPUS_READ_EXECUTION_ALLOWED = False
READ_EXECUTION_READINESS_ALLOWED = True
READ_EXECUTION_AUTHORIZATION_ALLOWED = True
READ_EXECUTION_INVOCATION_ALLOWED = True
READ_EXECUTION_INVOCATION_ACTIVATION_ALLOWED = True
READ_EXECUTION_ADAPTER_BINDING_ALLOWED = True
READ_EXECUTION_ADAPTER_READINESS_ALLOWED = True
READ_EXECUTION_ADAPTER_AUTHORIZATION_ALLOWED = True
RESEARCH_EXECUTION_ALLOWED = False
ANALYTIC_CONCLUSION_ALLOWED = False
FORECAST_CREATION_ALLOWED = False
SIGNALS_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
EXECUTION_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
MARKET_ORDER_CREATION_ALLOWED = False
FUNDS_MOVEMENT_ALLOWED = False
PORTFOLIO_MUTATION_ALLOWED = False
ADAPTER_AUTHORIZATION_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionAdapterAuthorizationError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
    CertifiedResearchEvidenceReadExecutionAdapterAuthorizationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
            f"{field_name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
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


def _valid_hash(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(
        _canonical(payload),
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _authorization_manifest_id(source_readiness_hash: str) -> str:
    seed = {
        "source_evidence_read_execution_adapter_readiness_manifest_hash":
            source_readiness_hash,
        "policy": EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
    }
    return f"oia040-read-adapter-authorization-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorization:
    authorization_sequence: int
    adapter_readiness_sequence: int
    binding_sequence: int
    activation_sequence: int
    invocation_sequence: int
    request_sequence: int
    task_sequence: int
    work_item_id: str
    worker_id: str
    dimension: str
    key: str
    evidence_scope_id: str
    authorized_read_operations: tuple[str, ...]
    authorized_adapter_ids: tuple[str, ...]
    authorized_operation_adapter_bindings: tuple[tuple[str, str], ...]
    authorization_checks: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    authorization_status: str
    source_active_invocation_hash: str
    source_adapter_binding_hash: str
    source_adapter_readiness_hash: str
    adapter_authorization_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationManifest:
    schema_version: str
    engine_id: str
    authorized_at: datetime
    evidence_read_execution_adapter_authorization_manifest_id: str
    authorization_manifest_status: str
    worker_id: str
    source_evidence_read_execution_adapter_readiness_manifest_id: str
    source_evidence_read_execution_adapter_binding_manifest_id: str
    source_evidence_read_execution_invocation_activation_id: str
    source_evidence_read_execution_invocation_manifest_id: str
    source_evidence_read_execution_authorization_id: str
    source_evidence_read_execution_readiness_id: str
    source_evidence_read_request_activation_id: str
    source_evidence_read_request_manifest_id: str
    source_evidence_task_activation_id: str
    source_evidence_task_manifest_id: str
    source_evidence_batch_activation_id: str
    source_evidence_batch_id: str
    source_evidence_session_id: str
    source_evidence_manifest_id: str
    source_certification_id: str
    source_readiness_id: str
    source_session_id: str
    source_activation_id: str
    source_claim_id: str
    dispatch_manifest_id: str
    selected_batch_id: str
    selected_batch_number: int
    authorization_count: int
    approved_read_only_adapter_ids: tuple[str, ...]
    evidence_read_execution_adapter_readiness_policy_id: str
    evidence_read_execution_adapter_authorization_policy_id: str
    authorizations: tuple[
        OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorization, ...
    ]
    source_evidence_read_execution_adapter_readiness_manifest_hash: str
    source_evidence_read_execution_adapter_binding_manifest_hash: str
    source_evidence_read_execution_invocation_activation_hash: str
    source_evidence_read_execution_invocation_manifest_hash: str
    source_evidence_read_execution_authorization_hash: str
    source_evidence_read_execution_readiness_hash: str
    source_evidence_read_request_activation_hash: str
    source_evidence_read_request_manifest_hash: str
    source_evidence_task_activation_hash: str
    source_evidence_task_manifest_hash: str
    source_evidence_batch_activation_hash: str
    source_evidence_batch_hash: str
    source_evidence_session_hash: str
    source_evidence_manifest_hash: str
    source_certification_hash: str
    source_readiness_hash: str
    source_session_hash: str
    source_activation_hash: str
    source_claim_hash: str
    source_dispatch_manifest_hash: str
    source_batch_hash: str
    read_only_corpus: bool
    evidence_collection_allowed: bool
    corpus_read_requests_allowed: bool
    corpus_read_execution_allowed: bool
    read_execution_readiness_allowed: bool
    read_execution_authorization_allowed: bool
    read_execution_invocation_allowed: bool
    read_execution_invocation_activation_allowed: bool
    read_execution_adapter_binding_allowed: bool
    read_execution_adapter_readiness_allowed: bool
    read_execution_adapter_authorization_allowed: bool
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
    adapter_authorization_artifact_persistence_allowed: bool
    evidence_read_execution_adapter_authorization_manifest_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationGate:
    def __init__(
        self,
        *,
        readiness_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_DIRECTORY
        ),
        authorization_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_DIRECTORY
        ),
    ) -> None:
        self._readiness_directory = Path(readiness_directory)
        self._authorization_directory = Path(authorization_directory)

    def _load_readiness_manifest(self) -> dict[str, Any]:
        path = self._readiness_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                f"OIA-039 current adapter readiness manifest is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                "OIA-039 adapter readiness manifest is invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                "OIA-039 adapter readiness manifest must be a JSON object."
            )

        manifest_hash = payload.pop(
            "evidence_read_execution_adapter_readiness_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                "OIA-039 adapter readiness manifest hash verification failed."
            )
        payload["evidence_read_execution_adapter_readiness_manifest_hash"] = (
            manifest_hash
        )

        expected = {
            "schema_version": "OIA-039",
            "engine_id": "OIA-039",
            "readiness_manifest_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
            "evidence_read_execution_adapter_readiness_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
            "read_only_corpus": True,
            "evidence_collection_allowed": True,
            "corpus_read_requests_allowed": True,
            "corpus_read_execution_allowed": False,
            "read_execution_readiness_allowed": True,
            "read_execution_authorization_allowed": True,
            "read_execution_invocation_allowed": True,
            "read_execution_invocation_activation_allowed": True,
            "read_execution_adapter_binding_allowed": True,
            "read_execution_adapter_readiness_allowed": True,
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
            "adapter_readiness_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    f"OIA-039 readiness invariant failed: {key}."
                )

        if tuple(payload.get("approved_read_only_adapter_ids", ())) != (
            APPROVED_READ_ONLY_ADAPTER_IDS
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                "OIA-039 approved adapter allowlist mismatch."
            )

        entries = payload.get("readiness_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or payload.get("readiness_count") != len(entries)
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                "OIA-039 adapter readiness entries are invalid."
            )

        for entry in entries:
            if not isinstance(entry, dict):
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    "OIA-039 adapter readiness entry must be an object."
                )
            readiness_hash = entry.pop("adapter_readiness_hash", None)
            if (
                not _valid_hash(readiness_hash)
                or stable_hash(entry) != readiness_hash
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    "OIA-039 adapter-readiness hash verification failed."
                )
            entry["adapter_readiness_hash"] = readiness_hash

            if entry.get("readiness_status") != EVIDENCE_READ_EXECUTION_ADAPTER_READY:
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    "OIA-039 adapter entry is not ready."
                )

            operations = entry.get("read_operations")
            adapter_ids = entry.get("adapter_ids")
            operation_bindings = entry.get("operation_adapter_bindings")
            checks = entry.get("adapter_contract_checks")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    "OIA-039 readiness entry has no operations."
                )
            if not isinstance(adapter_ids, list) or not adapter_ids:
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    "OIA-039 readiness entry has no adapter IDs."
                )
            if not isinstance(operation_bindings, list) or not operation_bindings:
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    "OIA-039 operation-adapter bindings are missing."
                )
            required_checks = {
                "adapter_id_allowlisted",
                "adapter_identity_read_only",
                "operation_mapping_exact",
                "source_binding_hash_verified",
                "corpus_execution_disabled",
            }
            if not isinstance(checks, list) or not required_checks.issubset(set(checks)):
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    "OIA-039 adapter contract checks are incomplete."
                )

            normalized_pairs = []
            for pair in operation_bindings:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                        "OIA-039 operation-adapter binding is malformed."
                    )
                operation, adapter_id = pair
                if (
                    not isinstance(operation, str)
                    or not operation.startswith("read_")
                    or operation not in operations
                    or operation not in OPERATION_ADAPTER_MAP
                    or OPERATION_ADAPTER_MAP[operation] != adapter_id
                    or adapter_id not in APPROVED_READ_ONLY_ADAPTER_IDS
                    or "read_only" not in adapter_id
                ):
                    raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                        "OIA-039 readiness entry contains an unauthorized adapter mapping."
                    )
                normalized_pairs.append((operation, adapter_id))

            if tuple(dict.fromkeys(adapter for _, adapter in normalized_pairs)) != tuple(
                adapter_ids
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    "OIA-039 adapter IDs do not match operation bindings."
                )

        for name in (
            "source_evidence_read_execution_adapter_binding_manifest_hash",
            "source_evidence_read_execution_invocation_activation_hash",
            "source_evidence_read_execution_invocation_manifest_hash",
            "source_evidence_read_execution_authorization_hash",
            "source_evidence_read_execution_readiness_hash",
            "source_evidence_read_request_activation_hash",
            "source_evidence_read_request_manifest_hash",
            "source_evidence_task_activation_hash",
            "source_evidence_task_manifest_hash",
            "source_evidence_batch_activation_hash",
            "source_evidence_batch_hash",
            "source_evidence_session_hash",
            "source_evidence_manifest_hash",
            "source_certification_hash",
            "source_readiness_hash",
            "source_session_hash",
            "source_activation_hash",
            "source_claim_hash",
            "source_dispatch_manifest_hash",
            "source_batch_hash",
        ):
            if not _valid_hash(payload.get(name)):
                raise CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError(
                    f"OIA-039 lineage hash invalid: {name}."
                )
        return payload

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationManifest:
        authorized_at = _aware_utc(authorized_at, "authorized_at")
        source = self._load_readiness_manifest()

        authorizations = []
        for sequence, entry in enumerate(source["readiness_entries"], start=1):
            body = {
                "authorization_sequence": sequence,
                "adapter_readiness_sequence": entry["readiness_sequence"],
                "binding_sequence": entry["binding_sequence"],
                "activation_sequence": entry["activation_sequence"],
                "invocation_sequence": entry["invocation_sequence"],
                "request_sequence": entry["request_sequence"],
                "task_sequence": entry["task_sequence"],
                "work_item_id": entry["work_item_id"],
                "worker_id": entry["worker_id"],
                "dimension": entry["dimension"],
                "key": entry["key"],
                "evidence_scope_id": entry["evidence_scope_id"],
                "authorized_read_operations": tuple(entry["read_operations"]),
                "authorized_adapter_ids": tuple(entry["adapter_ids"]),
                "authorized_operation_adapter_bindings": tuple(
                    tuple(pair) for pair in entry["operation_adapter_bindings"]
                ),
                "authorization_checks": (
                    "readiness_status_verified",
                    "readiness_hash_verified",
                    "adapter_allowlist_verified",
                    "operation_mapping_verified",
                    "read_only_identity_verified",
                    "corpus_execution_disabled",
                ),
                "prohibited_operations":
                    tuple(entry["prohibited_operations"]),
                "completion_requirements":
                    tuple(entry["completion_requirements"]),
                "authorization_status":
                    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED,
                "source_active_invocation_hash":
                    entry["source_active_invocation_hash"],
                "source_adapter_binding_hash":
                    entry["source_adapter_binding_hash"],
                "source_adapter_readiness_hash":
                    entry["adapter_readiness_hash"],
            }
            authorizations.append(
                OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorization(
                    **body,
                    adapter_authorization_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at,
            "evidence_read_execution_adapter_authorization_manifest_id":
                _authorization_manifest_id(
                    source[
                        "evidence_read_execution_adapter_readiness_manifest_hash"
                    ]
                ),
            "authorization_manifest_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_read_execution_adapter_readiness_manifest_id":
                source[
                    "evidence_read_execution_adapter_readiness_manifest_id"
                ],
            "source_evidence_read_execution_adapter_binding_manifest_id":
                source[
                    "source_evidence_read_execution_adapter_binding_manifest_id"
                ],
            "source_evidence_read_execution_invocation_activation_id":
                source[
                    "source_evidence_read_execution_invocation_activation_id"
                ],
            "source_evidence_read_execution_invocation_manifest_id":
                source[
                    "source_evidence_read_execution_invocation_manifest_id"
                ],
            "source_evidence_read_execution_authorization_id":
                source[
                    "source_evidence_read_execution_authorization_id"
                ],
            "source_evidence_read_execution_readiness_id":
                source["source_evidence_read_execution_readiness_id"],
            "source_evidence_read_request_activation_id":
                source["source_evidence_read_request_activation_id"],
            "source_evidence_read_request_manifest_id":
                source["source_evidence_read_request_manifest_id"],
            "source_evidence_task_activation_id":
                source["source_evidence_task_activation_id"],
            "source_evidence_task_manifest_id":
                source["source_evidence_task_manifest_id"],
            "source_evidence_batch_activation_id":
                source["source_evidence_batch_activation_id"],
            "source_evidence_batch_id": source["source_evidence_batch_id"],
            "source_evidence_session_id": source["source_evidence_session_id"],
            "source_evidence_manifest_id": source["source_evidence_manifest_id"],
            "source_certification_id": source["source_certification_id"],
            "source_readiness_id": source["source_readiness_id"],
            "source_session_id": source["source_session_id"],
            "source_activation_id": source["source_activation_id"],
            "source_claim_id": source["source_claim_id"],
            "dispatch_manifest_id": source["dispatch_manifest_id"],
            "selected_batch_id": source["selected_batch_id"],
            "selected_batch_number": source["selected_batch_number"],
            "authorization_count": len(authorizations),
            "approved_read_only_adapter_ids":
                APPROVED_READ_ONLY_ADAPTER_IDS,
            "evidence_read_execution_adapter_readiness_policy_id":
                source["evidence_read_execution_adapter_readiness_policy_id"],
            "evidence_read_execution_adapter_authorization_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
            "authorizations": tuple(authorizations),
            "source_evidence_read_execution_adapter_readiness_manifest_hash":
                source[
                    "evidence_read_execution_adapter_readiness_manifest_hash"
                ],
            "source_evidence_read_execution_adapter_binding_manifest_hash":
                source[
                    "source_evidence_read_execution_adapter_binding_manifest_hash"
                ],
            "source_evidence_read_execution_invocation_activation_hash":
                source[
                    "source_evidence_read_execution_invocation_activation_hash"
                ],
            "source_evidence_read_execution_invocation_manifest_hash":
                source[
                    "source_evidence_read_execution_invocation_manifest_hash"
                ],
            "source_evidence_read_execution_authorization_hash":
                source["source_evidence_read_execution_authorization_hash"],
            "source_evidence_read_execution_readiness_hash":
                source["source_evidence_read_execution_readiness_hash"],
            "source_evidence_read_request_activation_hash":
                source["source_evidence_read_request_activation_hash"],
            "source_evidence_read_request_manifest_hash":
                source["source_evidence_read_request_manifest_hash"],
            "source_evidence_task_activation_hash":
                source["source_evidence_task_activation_hash"],
            "source_evidence_task_manifest_hash":
                source["source_evidence_task_manifest_hash"],
            "source_evidence_batch_activation_hash":
                source["source_evidence_batch_activation_hash"],
            "source_evidence_batch_hash": source["source_evidence_batch_hash"],
            "source_evidence_session_hash":
                source["source_evidence_session_hash"],
            "source_evidence_manifest_hash":
                source["source_evidence_manifest_hash"],
            "source_certification_hash": source["source_certification_hash"],
            "source_readiness_hash": source["source_readiness_hash"],
            "source_session_hash": source["source_session_hash"],
            "source_activation_hash": source["source_activation_hash"],
            "source_claim_hash": source["source_claim_hash"],
            "source_dispatch_manifest_hash":
                source["source_dispatch_manifest_hash"],
            "source_batch_hash": source["source_batch_hash"],
            "read_only_corpus": READ_ONLY_CORPUS,
            "evidence_collection_allowed": EVIDENCE_COLLECTION_ALLOWED,
            "corpus_read_requests_allowed": CORPUS_READ_REQUESTS_ALLOWED,
            "corpus_read_execution_allowed": CORPUS_READ_EXECUTION_ALLOWED,
            "read_execution_readiness_allowed":
                READ_EXECUTION_READINESS_ALLOWED,
            "read_execution_authorization_allowed":
                READ_EXECUTION_AUTHORIZATION_ALLOWED,
            "read_execution_invocation_allowed":
                READ_EXECUTION_INVOCATION_ALLOWED,
            "read_execution_invocation_activation_allowed":
                READ_EXECUTION_INVOCATION_ACTIVATION_ALLOWED,
            "read_execution_adapter_binding_allowed":
                READ_EXECUTION_ADAPTER_BINDING_ALLOWED,
            "read_execution_adapter_readiness_allowed":
                READ_EXECUTION_ADAPTER_READINESS_ALLOWED,
            "read_execution_adapter_authorization_allowed":
                READ_EXECUTION_ADAPTER_AUTHORIZATION_ALLOWED,
            "research_execution_allowed": RESEARCH_EXECUTION_ALLOWED,
            "analytic_conclusion_allowed": ANALYTIC_CONCLUSION_ALLOWED,
            "forecast_creation_allowed": FORECAST_CREATION_ALLOWED,
            "signals_allowed": SIGNALS_ALLOWED,
            "alerts_allowed": ALERTS_ALLOWED,
            "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,
            "execution_allowed": EXECUTION_ALLOWED,
            "trading_recommendations_allowed":
                TRADING_RECOMMENDATIONS_ALLOWED,
            "source_mutation_allowed": SOURCE_MUTATION_ALLOWED,
            "market_order_creation_allowed": MARKET_ORDER_CREATION_ALLOWED,
            "funds_movement_allowed": FUNDS_MOVEMENT_ALLOWED,
            "portfolio_mutation_allowed": PORTFOLIO_MUTATION_ALLOWED,
            "adapter_authorization_artifact_persistence_allowed":
                ADAPTER_AUTHORIZATION_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationManifest(
                **body,
                evidence_read_execution_adapter_authorization_manifest_hash=
                    stable_hash(body),
            )
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._authorization_directory / "current.json", payload)
            _atomic_write(
                self._authorization_directory
                / "manifests"
                / (
                    f"{result.evidence_read_execution_adapter_authorization_manifest_id}"
                    ".json"
                ),
                payload,
            )
            _atomic_write(
                self._authorization_directory
                / "workers"
                / result.worker_id
                / (
                    f"{result.evidence_read_execution_adapter_authorization_manifest_id}"
                    ".json"
                ),
                payload,
            )
        return result
