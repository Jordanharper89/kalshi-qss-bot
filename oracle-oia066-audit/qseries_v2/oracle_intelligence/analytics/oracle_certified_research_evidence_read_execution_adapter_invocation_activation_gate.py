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
from .oracle_certified_research_evidence_read_execution_adapter_invocation_manifest_builder import (
    DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_DIRECTORY,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_MANIFEST_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_READY,
)

SCHEMA_VERSION = "OIA-042"
ENGINE_ID = "OIA-042"

EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-invocation-activation.v1"
)
EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_ISSUED = (
    "evidence_read_execution_adapter_invocation_activation_issued"
)
EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVE = (
    "evidence_read_execution_adapter_invocation_active"
)

DEFAULT_ACTIVE_EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_active_evidence_read_execution_adapter_invocations"
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
READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_ALLOWED = True
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
ADAPTER_INVOCATION_ACTIVATION_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationError(
    RuntimeError
):
    pass


class CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
    CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
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


def _activation_id(source_manifest_hash: str) -> str:
    seed = {
        "source_evidence_read_execution_adapter_invocation_manifest_hash":
            source_manifest_hash,
        "policy":
            EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_POLICY_ID,
    }
    return f"oia042-read-adapter-invocation-activation-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchActiveEvidenceReadExecutionAdapterInvocation:
    activation_sequence: int
    adapter_invocation_sequence: int
    adapter_authorization_sequence: int
    adapter_readiness_sequence: int
    binding_sequence: int
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
    activation_status: str
    source_active_invocation_hash: str
    source_adapter_binding_hash: str
    source_adapter_readiness_hash: str
    source_adapter_authorization_hash: str
    source_adapter_invocation_hash: str
    active_adapter_invocation_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationActivation:
    schema_version: str
    engine_id: str
    activated_at: datetime
    evidence_read_execution_adapter_invocation_activation_id: str
    activation_status: str
    worker_id: str
    source_evidence_read_execution_adapter_invocation_manifest_id: str
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
    active_adapter_invocation_count: int
    approved_read_only_adapter_ids: tuple[str, ...]
    evidence_read_execution_adapter_invocation_policy_id: str
    evidence_read_execution_adapter_invocation_activation_policy_id: str
    active_adapter_invocations: tuple[
        OracleCertifiedResearchActiveEvidenceReadExecutionAdapterInvocation, ...
    ]
    source_evidence_read_execution_adapter_invocation_manifest_hash: str
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
    read_execution_adapter_invocation_activation_allowed: bool
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
    adapter_invocation_activation_artifact_persistence_allowed: bool
    evidence_read_execution_adapter_invocation_activation_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationActivationGate:
    def __init__(
        self,
        *,
        invocation_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_DIRECTORY
        ),
        active_invocation_directory: Path | str = (
            DEFAULT_ACTIVE_EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_DIRECTORY
        ),
    ) -> None:
        self._invocation_directory = Path(invocation_directory)
        self._active_invocation_directory = Path(active_invocation_directory)

    def _load_manifest(self) -> dict[str, Any]:
        path = self._invocation_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                f"OIA-041 current adapter invocation manifest is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                "OIA-041 adapter invocation manifest is invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                "OIA-041 adapter invocation manifest must be a JSON object."
            )

        manifest_hash = payload.pop(
            "evidence_read_execution_adapter_invocation_manifest_hash",
            None,
        )
        if (
            not _valid_hash(manifest_hash)
            or stable_hash(payload) != manifest_hash
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                "OIA-041 adapter invocation manifest hash verification failed."
            )
        payload["evidence_read_execution_adapter_invocation_manifest_hash"] = (
            manifest_hash
        )

        expected = {
            "schema_version": "OIA-041",
            "engine_id": "OIA-041",
            "invocation_manifest_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_MANIFEST_ISSUED,
            "evidence_read_execution_adapter_invocation_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID,
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
            "read_execution_adapter_invocation_allowed": True,
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
            "adapter_invocation_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                    f"OIA-041 invocation invariant failed: {key}."
                )

        if tuple(payload.get("approved_read_only_adapter_ids", ())) != (
            APPROVED_READ_ONLY_ADAPTER_IDS
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                "OIA-041 approved adapter allowlist mismatch."
            )

        invocations = payload.get("adapter_invocations")
        if (
            not isinstance(invocations, list)
            or not invocations
            or payload.get("adapter_invocation_count") != len(invocations)
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                "OIA-041 adapter invocation records are invalid."
            )

        for invocation in invocations:
            if not isinstance(invocation, dict):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                    "OIA-041 adapter invocation must be an object."
                )
            invocation_hash = invocation.pop("adapter_invocation_hash", None)
            if (
                not _valid_hash(invocation_hash)
                or stable_hash(invocation) != invocation_hash
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                    "OIA-041 adapter-invocation hash verification failed."
                )
            invocation["adapter_invocation_hash"] = invocation_hash

            if (
                invocation.get("invocation_status")
                != EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_READY
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                    "OIA-041 adapter invocation is not ready."
                )

            adapter_id = invocation.get("adapter_id")
            operation = invocation.get("read_operation")
            arguments = invocation.get("invocation_arguments")
            if (
                adapter_id not in APPROVED_READ_ONLY_ADAPTER_IDS
                or "read_only" not in adapter_id
                or operation not in OPERATION_ADAPTER_MAP
                or OPERATION_ADAPTER_MAP[operation] != adapter_id
                or not isinstance(operation, str)
                or not operation.startswith("read_")
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                    "OIA-041 invocation contains an unauthorized adapter mapping."
                )
            if (
                not isinstance(arguments, dict)
                or arguments.get("read_only") is not True
                or arguments.get("execute") is not False
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                    "OIA-041 invocation arguments are not non-executing read-only."
                )

        for name in (
            "source_evidence_read_execution_adapter_authorization_manifest_hash",
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
                raise CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError(
                    f"OIA-041 lineage hash invalid: {name}."
                )
        return payload

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationActivation:
        activated_at = _aware_utc(activated_at, "activated_at")
        source = self._load_manifest()

        active_invocations = []
        for sequence, invocation in enumerate(
            source["adapter_invocations"], start=1
        ):
            arguments = dict(invocation["invocation_arguments"])
            arguments["activated"] = True
            arguments["execute"] = False
            arguments["read_only"] = True
            body = {
                "activation_sequence": sequence,
                "adapter_invocation_sequence":
                    invocation["adapter_invocation_sequence"],
                "adapter_authorization_sequence":
                    invocation["adapter_authorization_sequence"],
                "adapter_readiness_sequence":
                    invocation["adapter_readiness_sequence"],
                "binding_sequence": invocation["binding_sequence"],
                "invocation_sequence": invocation["invocation_sequence"],
                "request_sequence": invocation["request_sequence"],
                "task_sequence": invocation["task_sequence"],
                "work_item_id": invocation["work_item_id"],
                "worker_id": invocation["worker_id"],
                "dimension": invocation["dimension"],
                "key": invocation["key"],
                "evidence_scope_id": invocation["evidence_scope_id"],
                "adapter_id": invocation["adapter_id"],
                "read_operation": invocation["read_operation"],
                "invocation_arguments": arguments,
                "prohibited_operations":
                    tuple(invocation["prohibited_operations"]),
                "completion_requirements":
                    tuple(invocation["completion_requirements"]),
                "activation_status":
                    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVE,
                "source_active_invocation_hash":
                    invocation["source_active_invocation_hash"],
                "source_adapter_binding_hash":
                    invocation["source_adapter_binding_hash"],
                "source_adapter_readiness_hash":
                    invocation["source_adapter_readiness_hash"],
                "source_adapter_authorization_hash":
                    invocation["source_adapter_authorization_hash"],
                "source_adapter_invocation_hash":
                    invocation["adapter_invocation_hash"],
            }
            active_invocations.append(
                OracleCertifiedResearchActiveEvidenceReadExecutionAdapterInvocation(
                    **body,
                    active_adapter_invocation_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at,
            "evidence_read_execution_adapter_invocation_activation_id":
                _activation_id(
                    source[
                        "evidence_read_execution_adapter_invocation_manifest_hash"
                    ]
                ),
            "activation_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_read_execution_adapter_invocation_manifest_id":
                source[
                    "evidence_read_execution_adapter_invocation_manifest_id"
                ],
            "source_evidence_read_execution_adapter_authorization_manifest_id":
                source[
                    "source_evidence_read_execution_adapter_authorization_manifest_id"
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
            "active_adapter_invocation_count": len(active_invocations),
            "approved_read_only_adapter_ids":
                APPROVED_READ_ONLY_ADAPTER_IDS,
            "evidence_read_execution_adapter_invocation_policy_id":
                source[
                    "evidence_read_execution_adapter_invocation_policy_id"
                ],
            "evidence_read_execution_adapter_invocation_activation_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_POLICY_ID,
            "active_adapter_invocations": tuple(active_invocations),
            "source_evidence_read_execution_adapter_invocation_manifest_hash":
                source[
                    "evidence_read_execution_adapter_invocation_manifest_hash"
                ],
            "source_evidence_read_execution_adapter_authorization_manifest_hash":
                source[
                    "source_evidence_read_execution_adapter_authorization_manifest_hash"
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
            "read_execution_adapter_invocation_activation_allowed":
                READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_ALLOWED,
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
            "adapter_invocation_activation_artifact_persistence_allowed":
                ADAPTER_INVOCATION_ACTIVATION_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationActivation(
                **body,
                evidence_read_execution_adapter_invocation_activation_hash=
                    stable_hash(body),
            )
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(
                self._active_invocation_directory / "current.json",
                payload,
            )
            _atomic_write(
                self._active_invocation_directory
                / "activations"
                / (
                    f"{result.evidence_read_execution_adapter_invocation_activation_id}"
                    ".json"
                ),
                payload,
            )
            _atomic_write(
                self._active_invocation_directory
                / "workers"
                / result.worker_id
                / (
                    f"{result.evidence_read_execution_adapter_invocation_activation_id}"
                    ".json"
                ),
                payload,
            )
        return result
