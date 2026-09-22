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

from .oracle_certified_research_evidence_read_execution_invocation_activation_gate import (
    DEFAULT_ACTIVE_EVIDENCE_READ_EXECUTION_INVOCATION_DIRECTORY,
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVE,
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_ISSUED,
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID,
)

SCHEMA_VERSION = "OIA-038"
ENGINE_ID = "OIA-038"

EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-binding.v1"
)
EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED = (
    "evidence_read_execution_adapter_binding_issued"
)
EVIDENCE_READ_EXECUTION_ADAPTER_BOUND = (
    "evidence_read_execution_adapter_bound"
)

DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_evidence_read_execution_adapter_bindings"
)

APPROVED_READ_ONLY_ADAPTER_IDS = (
    "oracle_read_only_canonical_observation_adapter.v1",
    "oracle_read_only_market_state_lineage_adapter.v1",
)
OPERATION_ADAPTER_MAP = MappingProxyType(
    {
        "read_canonical_observations":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_market_state_lineage":
            "oracle_read_only_market_state_lineage_adapter.v1",
    }
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
ADAPTER_BINDING_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionAdapterBindingError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
    CertifiedResearchEvidenceReadExecutionAdapterBindingError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
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


def _binding_manifest_id(source_activation_hash: str) -> str:
    seed = {
        "source_evidence_read_execution_invocation_activation_hash":
            source_activation_hash,
        "policy": EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID,
    }
    return f"oia038-read-adapter-binding-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterBinding:
    binding_sequence: int
    activation_sequence: int
    invocation_sequence: int
    authorization_sequence: int
    readiness_sequence: int
    request_sequence: int
    task_sequence: int
    work_item_id: str
    worker_id: str
    dimension: str
    key: str
    evidence_scope_id: str
    read_operations: tuple[str, ...]
    adapter_ids: tuple[str, ...]
    operation_adapter_bindings: tuple[tuple[str, str], ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    binding_status: str
    source_evidence_read_request_hash: str
    source_active_evidence_read_request_hash: str
    source_readiness_entry_hash: str
    source_authorization_entry_hash: str
    source_invocation_hash: str
    source_active_invocation_hash: str
    adapter_binding_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterBindingManifest:
    schema_version: str
    engine_id: str
    bound_at: datetime
    evidence_read_execution_adapter_binding_manifest_id: str
    binding_manifest_status: str
    worker_id: str
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
    binding_count: int
    approved_read_only_adapter_ids: tuple[str, ...]
    evidence_read_execution_invocation_activation_policy_id: str
    evidence_read_execution_adapter_binding_policy_id: str
    bindings: tuple[OracleCertifiedResearchEvidenceReadExecutionAdapterBinding, ...]
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
    adapter_binding_artifact_persistence_allowed: bool
    evidence_read_execution_adapter_binding_manifest_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionAdapterBindingGate:
    def __init__(
        self,
        *,
        active_invocation_directory: Path | str = (
            DEFAULT_ACTIVE_EVIDENCE_READ_EXECUTION_INVOCATION_DIRECTORY
        ),
        binding_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_DIRECTORY
        ),
    ) -> None:
        self._active_invocation_directory = Path(active_invocation_directory)
        self._binding_directory = Path(binding_directory)

    def _load_activation(self) -> dict[str, Any]:
        path = self._active_invocation_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                f"OIA-037 current invocation activation is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                "OIA-037 invocation activation is invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                "OIA-037 invocation activation must be a JSON object."
            )

        activation_hash = payload.pop(
            "evidence_read_execution_invocation_activation_hash",
            None,
        )
        if (
            not _valid_hash(activation_hash)
            or stable_hash(payload) != activation_hash
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                "OIA-037 invocation activation hash verification failed."
            )
        payload["evidence_read_execution_invocation_activation_hash"] = (
            activation_hash
        )

        expected = {
            "schema_version": "OIA-037",
            "engine_id": "OIA-037",
            "activation_status":
                EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_ISSUED,
            "evidence_read_execution_invocation_activation_policy_id":
                EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID,
            "read_only_corpus": True,
            "evidence_collection_allowed": True,
            "corpus_read_requests_allowed": True,
            "corpus_read_execution_allowed": False,
            "read_execution_readiness_allowed": True,
            "read_execution_authorization_allowed": True,
            "read_execution_invocation_allowed": True,
            "read_execution_invocation_activation_allowed": True,
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
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                    f"OIA-037 activation invariant failed: {key}."
                )

        invocations = payload.get("invocations")
        if (
            not isinstance(invocations, list)
            or not invocations
            or payload.get("active_invocation_count") != len(invocations)
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                "OIA-037 active invocation records are invalid."
            )

        for invocation in invocations:
            if not isinstance(invocation, dict):
                raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                    "OIA-037 active invocation must be an object."
                )
            invocation_hash = invocation.pop("active_invocation_hash", None)
            if (
                not _valid_hash(invocation_hash)
                or stable_hash(invocation) != invocation_hash
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                    "OIA-037 active invocation hash verification failed."
                )
            invocation["active_invocation_hash"] = invocation_hash
            if (
                invocation.get("activation_status")
                != EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVE
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                    "OIA-037 invocation is not active."
                )
            operations = invocation.get("active_read_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                    "OIA-037 active invocation has no read operations."
                )
            for operation in operations:
                if (
                    not isinstance(operation, str)
                    or not operation.startswith("read_")
                    or operation not in OPERATION_ADAPTER_MAP
                ):
                    raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                        f"No approved read-only adapter for operation: {operation!r}."
                    )

        for name in (
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
                raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                    f"OIA-037 lineage hash invalid: {name}."
                )
        return payload

    def bind(
        self,
        *,
        bound_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionAdapterBindingManifest:
        bound_at = _aware_utc(bound_at, "bound_at")
        source = self._load_activation()

        bindings = []
        for sequence, invocation in enumerate(source["invocations"], start=1):
            operation_adapter_bindings = tuple(
                (operation, OPERATION_ADAPTER_MAP[operation])
                for operation in invocation["active_read_operations"]
            )
            adapter_ids = tuple(
                dict.fromkeys(adapter_id for _, adapter_id in operation_adapter_bindings)
            )
            if any(
                adapter_id not in APPROVED_READ_ONLY_ADAPTER_IDS
                or "read_only" not in adapter_id
                for adapter_id in adapter_ids
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterBindingInvariantError(
                    "A non-approved or write-capable adapter was selected."
                )

            body = {
                "binding_sequence": sequence,
                "activation_sequence": invocation["activation_sequence"],
                "invocation_sequence": invocation["invocation_sequence"],
                "authorization_sequence": invocation["authorization_sequence"],
                "readiness_sequence": invocation["readiness_sequence"],
                "request_sequence": invocation["request_sequence"],
                "task_sequence": invocation["task_sequence"],
                "work_item_id": invocation["work_item_id"],
                "worker_id": invocation["worker_id"],
                "dimension": invocation["dimension"],
                "key": invocation["key"],
                "evidence_scope_id": invocation["evidence_scope_id"],
                "read_operations": tuple(invocation["active_read_operations"]),
                "adapter_ids": adapter_ids,
                "operation_adapter_bindings": operation_adapter_bindings,
                "prohibited_operations":
                    tuple(invocation["prohibited_operations"]),
                "completion_requirements":
                    tuple(invocation["completion_requirements"]),
                "binding_status": EVIDENCE_READ_EXECUTION_ADAPTER_BOUND,
                "source_evidence_read_request_hash":
                    invocation["source_evidence_read_request_hash"],
                "source_active_evidence_read_request_hash":
                    invocation["source_active_evidence_read_request_hash"],
                "source_readiness_entry_hash":
                    invocation["source_readiness_entry_hash"],
                "source_authorization_entry_hash":
                    invocation["source_authorization_entry_hash"],
                "source_invocation_hash": invocation["source_invocation_hash"],
                "source_active_invocation_hash":
                    invocation["active_invocation_hash"],
            }
            bindings.append(
                OracleCertifiedResearchEvidenceReadExecutionAdapterBinding(
                    **body,
                    adapter_binding_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "bound_at": bound_at,
            "evidence_read_execution_adapter_binding_manifest_id":
                _binding_manifest_id(
                    source[
                        "evidence_read_execution_invocation_activation_hash"
                    ]
                ),
            "binding_manifest_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_read_execution_invocation_activation_id":
                source[
                    "evidence_read_execution_invocation_activation_id"
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
            "binding_count": len(bindings),
            "approved_read_only_adapter_ids":
                APPROVED_READ_ONLY_ADAPTER_IDS,
            "evidence_read_execution_invocation_activation_policy_id":
                source[
                    "evidence_read_execution_invocation_activation_policy_id"
                ],
            "evidence_read_execution_adapter_binding_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID,
            "bindings": tuple(bindings),
            "source_evidence_read_execution_invocation_activation_hash":
                source[
                    "evidence_read_execution_invocation_activation_hash"
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
            "adapter_binding_artifact_persistence_allowed":
                ADAPTER_BINDING_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = OracleCertifiedResearchEvidenceReadExecutionAdapterBindingManifest(
            **body,
            evidence_read_execution_adapter_binding_manifest_hash=
                stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._binding_directory / "current.json", payload)
            _atomic_write(
                self._binding_directory
                / "manifests"
                / (
                    f"{result.evidence_read_execution_adapter_binding_manifest_id}"
                    ".json"
                ),
                payload,
            )
            _atomic_write(
                self._binding_directory
                / "workers"
                / result.worker_id
                / (
                    f"{result.evidence_read_execution_adapter_binding_manifest_id}"
                    ".json"
                ),
                payload,
            )
        return result
