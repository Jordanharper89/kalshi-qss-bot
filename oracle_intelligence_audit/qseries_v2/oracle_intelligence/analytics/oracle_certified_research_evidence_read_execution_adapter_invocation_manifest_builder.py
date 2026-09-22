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

from .oracle_certified_research_evidence_read_execution_adapter_authorization_gate import (
    DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_DIRECTORY,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
)
from .oracle_certified_research_evidence_read_execution_adapter_binding_gate import (
    APPROVED_READ_ONLY_ADAPTER_IDS,
    OPERATION_ADAPTER_MAP,
)

SCHEMA_VERSION = "OIA-041"
ENGINE_ID = "OIA-041"

EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-invocation.v1"
)
EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_MANIFEST_ISSUED = (
    "evidence_read_execution_adapter_invocation_manifest_issued"
)
EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_READY = (
    "evidence_read_execution_adapter_invocation_ready"
)

DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_evidence_read_execution_adapter_invocations"
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
READ_EXECUTION_ADAPTER_INVOCATION_ALLOWED = True
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
ADAPTER_INVOCATION_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionAdapterInvocationError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
    CertifiedResearchEvidenceReadExecutionAdapterInvocationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
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


def _manifest_id(source_authorization_hash: str) -> str:
    seed = {
        "source_evidence_read_execution_adapter_authorization_manifest_hash":
            source_authorization_hash,
        "policy": EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID,
    }
    return f"oia041-read-adapter-invocation-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterInvocation:
    adapter_invocation_sequence: int
    adapter_authorization_sequence: int
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
    adapter_id: str
    read_operation: str
    invocation_arguments: Mapping[str, Any]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    invocation_status: str
    source_active_invocation_hash: str
    source_adapter_binding_hash: str
    source_adapter_readiness_hash: str
    source_adapter_authorization_hash: str
    adapter_invocation_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationManifest:
    schema_version: str
    engine_id: str
    generated_at: datetime
    evidence_read_execution_adapter_invocation_manifest_id: str
    invocation_manifest_status: str
    worker_id: str
    source_evidence_read_execution_adapter_authorization_manifest_id: str
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
    adapter_invocation_count: int
    approved_read_only_adapter_ids: tuple[str, ...]
    evidence_read_execution_adapter_authorization_policy_id: str
    evidence_read_execution_adapter_invocation_policy_id: str
    adapter_invocations: tuple[
        OracleCertifiedResearchEvidenceReadExecutionAdapterInvocation, ...
    ]
    source_evidence_read_execution_adapter_authorization_manifest_hash: str
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
    read_execution_adapter_invocation_allowed: bool
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
    adapter_invocation_artifact_persistence_allowed: bool
    evidence_read_execution_adapter_invocation_manifest_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationManifestBuilder:
    def __init__(
        self,
        *,
        authorization_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_DIRECTORY
        ),
        invocation_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_DIRECTORY
        ),
    ) -> None:
        self._authorization_directory = Path(authorization_directory)
        self._invocation_directory = Path(invocation_directory)

    def _load_authorization_manifest(self) -> dict[str, Any]:
        path = self._authorization_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                f"OIA-040 current adapter authorization manifest is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                "OIA-040 adapter authorization manifest is invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                "OIA-040 adapter authorization manifest must be a JSON object."
            )

        manifest_hash = payload.pop(
            "evidence_read_execution_adapter_authorization_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                "OIA-040 adapter authorization manifest hash verification failed."
            )
        payload["evidence_read_execution_adapter_authorization_manifest_hash"] = (
            manifest_hash
        )

        expected = {
            "schema_version": "OIA-040",
            "engine_id": "OIA-040",
            "authorization_manifest_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED,
            "evidence_read_execution_adapter_authorization_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
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
            "read_execution_adapter_authorization_allowed": True,
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
            "adapter_authorization_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    f"OIA-040 authorization invariant failed: {key}."
                )

        if tuple(payload.get("approved_read_only_adapter_ids", ())) != (
            APPROVED_READ_ONLY_ADAPTER_IDS
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                "OIA-040 approved adapter allowlist mismatch."
            )

        authorizations = payload.get("authorizations")
        if (
            not isinstance(authorizations, list)
            or not authorizations
            or payload.get("authorization_count") != len(authorizations)
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                "OIA-040 adapter authorizations are invalid."
            )

        for authorization in authorizations:
            if not isinstance(authorization, dict):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    "OIA-040 adapter authorization must be an object."
                )
            authorization_hash = authorization.pop(
                "adapter_authorization_hash", None
            )
            if (
                not _valid_hash(authorization_hash)
                or stable_hash(authorization) != authorization_hash
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    "OIA-040 adapter-authorization hash verification failed."
                )
            authorization["adapter_authorization_hash"] = authorization_hash

            if (
                authorization.get("authorization_status")
                != EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    "OIA-040 adapter authorization is not authorized."
                )

            operations = authorization.get("authorized_read_operations")
            adapter_ids = authorization.get("authorized_adapter_ids")
            bindings = authorization.get(
                "authorized_operation_adapter_bindings"
            )
            checks = authorization.get("authorization_checks")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    "OIA-040 authorization has no read operations."
                )
            if not isinstance(adapter_ids, list) or not adapter_ids:
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    "OIA-040 authorization has no adapter IDs."
                )
            if not isinstance(bindings, list) or not bindings:
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    "OIA-040 authorized operation-adapter bindings are missing."
                )
            required_checks = {
                "readiness_status_verified",
                "readiness_hash_verified",
                "adapter_allowlist_verified",
                "operation_mapping_verified",
                "read_only_identity_verified",
                "corpus_execution_disabled",
            }
            if not isinstance(checks, list) or not required_checks.issubset(set(checks)):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    "OIA-040 adapter authorization checks are incomplete."
                )

            normalized_pairs = []
            for pair in bindings:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                        "OIA-040 operation-adapter authorization is malformed."
                    )
                operation, adapter_id = pair
                if (
                    operation not in operations
                    or operation not in OPERATION_ADAPTER_MAP
                    or OPERATION_ADAPTER_MAP[operation] != adapter_id
                    or adapter_id not in APPROVED_READ_ONLY_ADAPTER_IDS
                    or "read_only" not in adapter_id
                    or not operation.startswith("read_")
                ):
                    raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                        "OIA-040 contains an unauthorized adapter invocation mapping."
                    )
                normalized_pairs.append((operation, adapter_id))

            if tuple(dict.fromkeys(adapter for _, adapter in normalized_pairs)) != tuple(
                adapter_ids
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    "OIA-040 adapter IDs do not match authorized bindings."
                )

        for name in (
            "source_evidence_read_execution_adapter_readiness_manifest_hash",
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
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError(
                    f"OIA-040 lineage hash invalid: {name}."
                )
        return payload

    def build(
        self,
        *,
        generated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationManifest:
        generated_at = _aware_utc(generated_at, "generated_at")
        source = self._load_authorization_manifest()

        adapter_invocations = []
        sequence = 0
        for authorization in source["authorizations"]:
            for operation, adapter_id in authorization[
                "authorized_operation_adapter_bindings"
            ]:
                sequence += 1
                arguments = {
                    "worker_id": authorization["worker_id"],
                    "work_item_id": authorization["work_item_id"],
                    "evidence_scope_id": authorization["evidence_scope_id"],
                    "dimension": authorization["dimension"],
                    "key": authorization["key"],
                    "read_only": True,
                    "execute": False,
                }
                body = {
                    "adapter_invocation_sequence": sequence,
                    "adapter_authorization_sequence":
                        authorization["authorization_sequence"],
                    "adapter_readiness_sequence":
                        authorization["adapter_readiness_sequence"],
                    "binding_sequence": authorization["binding_sequence"],
                    "activation_sequence": authorization["activation_sequence"],
                    "invocation_sequence": authorization["invocation_sequence"],
                    "request_sequence": authorization["request_sequence"],
                    "task_sequence": authorization["task_sequence"],
                    "work_item_id": authorization["work_item_id"],
                    "worker_id": authorization["worker_id"],
                    "dimension": authorization["dimension"],
                    "key": authorization["key"],
                    "evidence_scope_id": authorization["evidence_scope_id"],
                    "adapter_id": adapter_id,
                    "read_operation": operation,
                    "invocation_arguments": arguments,
                    "prohibited_operations":
                        tuple(authorization["prohibited_operations"]),
                    "completion_requirements":
                        tuple(authorization["completion_requirements"]),
                    "invocation_status":
                        EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_READY,
                    "source_active_invocation_hash":
                        authorization["source_active_invocation_hash"],
                    "source_adapter_binding_hash":
                        authorization["source_adapter_binding_hash"],
                    "source_adapter_readiness_hash":
                        authorization["source_adapter_readiness_hash"],
                    "source_adapter_authorization_hash":
                        authorization["adapter_authorization_hash"],
                }
                adapter_invocations.append(
                    OracleCertifiedResearchEvidenceReadExecutionAdapterInvocation(
                        **body,
                        adapter_invocation_hash=stable_hash(body),
                    )
                )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "evidence_read_execution_adapter_invocation_manifest_id":
                _manifest_id(
                    source[
                        "evidence_read_execution_adapter_authorization_manifest_hash"
                    ]
                ),
            "invocation_manifest_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_MANIFEST_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_read_execution_adapter_authorization_manifest_id":
                source[
                    "evidence_read_execution_adapter_authorization_manifest_id"
                ],
            "source_evidence_read_execution_adapter_readiness_manifest_id":
                source[
                    "source_evidence_read_execution_adapter_readiness_manifest_id"
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
                source["source_evidence_read_execution_authorization_id"],
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
            "adapter_invocation_count": len(adapter_invocations),
            "approved_read_only_adapter_ids":
                APPROVED_READ_ONLY_ADAPTER_IDS,
            "evidence_read_execution_adapter_authorization_policy_id":
                source[
                    "evidence_read_execution_adapter_authorization_policy_id"
                ],
            "evidence_read_execution_adapter_invocation_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID,
            "adapter_invocations": tuple(adapter_invocations),
            "source_evidence_read_execution_adapter_authorization_manifest_hash":
                source[
                    "evidence_read_execution_adapter_authorization_manifest_hash"
                ],
            "source_evidence_read_execution_adapter_readiness_manifest_hash":
                source[
                    "source_evidence_read_execution_adapter_readiness_manifest_hash"
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
            "read_execution_adapter_invocation_allowed":
                READ_EXECUTION_ADAPTER_INVOCATION_ALLOWED,
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
            "adapter_invocation_artifact_persistence_allowed":
                ADAPTER_INVOCATION_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationManifest(
            **body,
            evidence_read_execution_adapter_invocation_manifest_hash=
                stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._invocation_directory / "current.json", payload)
            _atomic_write(
                self._invocation_directory
                / "manifests"
                / (
                    f"{result.evidence_read_execution_adapter_invocation_manifest_id}"
                    ".json"
                ),
                payload,
            )
            _atomic_write(
                self._invocation_directory
                / "workers"
                / result.worker_id
                / (
                    f"{result.evidence_read_execution_adapter_invocation_manifest_id}"
                    ".json"
                ),
                payload,
            )
        return result
