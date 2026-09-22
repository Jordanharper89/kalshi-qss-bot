from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA039 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_readiness_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_authorization_gate.py"
TEST = ROOT / "test_oia_040_oracle_certified_research_evidence_read_execution_adapter_authorization_gate.py"
INIT = ANALYTICS / "__init__.py"

PRODUCTION_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_binding_gate import (
    APPROVED_READ_ONLY_ADAPTER_IDS,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_readiness_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_READY,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
    stable_hash as readiness_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_authorization_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
    CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationGate,
    stable_hash,
)

H = [f"{index:064x}" for index in range(1, 90)]


def seed(directory: Path) -> dict:
    entry_body = {
        "readiness_sequence": 1,
        "binding_sequence": 1,
        "activation_sequence": 1,
        "invocation_sequence": 1,
        "authorization_sequence": 1,
        "request_sequence": 1,
        "task_sequence": 1,
        "work_item_id": "work.test",
        "worker_id": "oracle-worker-test",
        "dimension": "market_microstructure",
        "key": "spread-regime",
        "evidence_scope_id": "scope.test",
        "read_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "adapter_ids": list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "operation_adapter_bindings": [
            [
                "read_canonical_observations",
                "oracle_read_only_canonical_observation_adapter.v1",
            ],
            [
                "read_market_state_lineage",
                "oracle_read_only_market_state_lineage_adapter.v1",
            ],
        ],
        "adapter_contract_checks": [
            "adapter_id_allowlisted",
            "adapter_identity_read_only",
            "operation_mapping_exact",
            "source_binding_hash_verified",
            "corpus_execution_disabled",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "readiness_status": EVIDENCE_READ_EXECUTION_ADAPTER_READY,
        "source_active_invocation_hash": H[1],
        "source_adapter_binding_hash": H[2],
    }
    entry = dict(entry_body)
    entry["adapter_readiness_hash"] = readiness_hash(entry_body)

    body = {
        "schema_version": "OIA-039",
        "engine_id": "OIA-039",
        "evaluated_at": "2026-07-21T21:00:00+00:00",
        "evidence_read_execution_adapter_readiness_manifest_id": "oia039-test",
        "readiness_manifest_status":
            EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
        "worker_id": "oracle-worker-test",
        "source_evidence_read_execution_adapter_binding_manifest_id": "oia038-test",
        "source_evidence_read_execution_invocation_activation_id": "oia037-test",
        "source_evidence_read_execution_invocation_manifest_id": "oia036-test",
        "source_evidence_read_execution_authorization_id": "oia035-test",
        "source_evidence_read_execution_readiness_id": "oia034-test",
        "source_evidence_read_request_activation_id": "oia033-test",
        "source_evidence_read_request_manifest_id": "oia032-test",
        "source_evidence_task_activation_id": "oia031-test",
        "source_evidence_task_manifest_id": "oia030-test",
        "source_evidence_batch_activation_id": "oia029-test",
        "source_evidence_batch_id": "oia028-test",
        "source_evidence_session_id": "oia027-test",
        "source_evidence_manifest_id": "oia026-test",
        "source_certification_id": "oia025-test",
        "source_readiness_id": "oia024-test",
        "source_session_id": "oia023-test",
        "source_activation_id": "oia022-test",
        "source_claim_id": "oia021-test",
        "dispatch_manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "readiness_count": 1,
        "approved_read_only_adapter_ids":
            list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "evidence_read_execution_adapter_binding_policy_id": "oia038-policy",
        "evidence_read_execution_adapter_readiness_policy_id":
            EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
        "readiness_entries": [entry],
        "source_evidence_read_execution_adapter_binding_manifest_hash": H[3],
        "source_evidence_read_execution_invocation_activation_hash": H[4],
        "source_evidence_read_execution_invocation_manifest_hash": H[5],
        "source_evidence_read_execution_authorization_hash": H[6],
        "source_evidence_read_execution_readiness_hash": H[7],
        "source_evidence_read_request_activation_hash": H[8],
        "source_evidence_read_request_manifest_hash": H[9],
        "source_evidence_task_activation_hash": H[10],
        "source_evidence_task_manifest_hash": H[11],
        "source_evidence_batch_activation_hash": H[12],
        "source_evidence_batch_hash": H[13],
        "source_evidence_session_hash": H[14],
        "source_evidence_manifest_hash": H[15],
        "source_certification_hash": H[16],
        "source_readiness_hash": H[17],
        "source_session_hash": H[18],
        "source_activation_hash": H[19],
        "source_claim_hash": H[20],
        "source_dispatch_manifest_hash": H[21],
        "source_batch_hash": H[22],
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
    payload = dict(body)
    payload["evidence_read_execution_adapter_readiness_manifest_hash"] = (
        readiness_hash(body)
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-040 TEST")
    print(" EVIDENCE READ ADAPTER AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness_directory = root / "readiness"
        authorization_directory = root / "authorization"
        source = seed(readiness_directory)

        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationGate(
            readiness_directory=readiness_directory,
            authorization_directory=authorization_directory,
        )
        fixed = datetime(2026, 7, 21, 22, 0, tzinfo=timezone.utc)
        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-040"
        assert first.engine_id == "OIA-040"
        assert first.authorization_manifest_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED
        )
        assert first.evidence_read_execution_adapter_authorization_policy_id == (
            EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID
        )
        assert first.authorization_count == 1
        assert first.authorizations[0].authorization_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED
        )
        assert first.source_evidence_read_execution_adapter_readiness_manifest_hash == (
            source["evidence_read_execution_adapter_readiness_manifest_hash"]
        )
        assert first.authorizations[0].source_adapter_readiness_hash == (
            source["readiness_entries"][0]["adapter_readiness_hash"]
        )
        assert set(first.authorizations[0].authorized_adapter_ids).issubset(
            set(APPROVED_READ_ONLY_ADAPTER_IDS)
        )
        assert all(
            operation.startswith("read_")
            for operation in first.authorizations[0].authorized_read_operations
        )
        assert "readiness_hash_verified" in (
            first.authorizations[0].authorization_checks
        )
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_adapter_authorization_allowed is True

        for value in (
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
        ):
            assert value is False

        body = dict(first.to_dict())
        manifest_hash = body.pop(
            "evidence_read_execution_adapter_authorization_manifest_hash"
        )
        assert manifest_hash == stable_hash(body)

        authorization_body = dict(first.authorizations[0].to_dict())
        authorization_hash_value = authorization_body.pop(
            "adapter_authorization_hash"
        )
        assert authorization_hash_value == stable_hash(authorization_body)

        assert (authorization_directory / "current.json").exists()
        assert list((authorization_directory / "manifests").glob("*.json"))
        assert list(
            (authorization_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (readiness_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["readiness_entries"][0]["adapter_contract_checks"].remove(
            "corpus_execution_disabled"
        )
        (readiness_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.authorize(authorized_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-039 adapter readiness accepted.")

    print("[PASS] Actual OIA-039 adapter readiness contract consumed")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-039 lineage preserved")
    print("[PASS] Only readiness-certified read-only adapters authorized")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or incomplete readiness rejected")
    print("[PASS] Atomic adapter-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

INIT_BLOCK = r"""
from .oracle_certified_research_evidence_read_execution_adapter_authorization_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
    OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorization,
    OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationGate,
    OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationManifest,
)

__all__ = [
    "EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED",
    "EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED",
    "EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorization",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationGate",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationManifest",
] + __all__
"""


def verify_oia039() -> None:
    if not OIA039.exists():
        raise RuntimeError(f"Actual OIA-039 production module missing: {OIA039}")
    text = OIA039.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION = "OIA-039"',
        'ENGINE_ID = "OIA-039"',
        "EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID",
        "EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED",
        "EVIDENCE_READ_EXECUTION_ADAPTER_READY",
        "evidence_read_execution_adapter_readiness_manifest_hash",
        "adapter_readiness_hash",
        "adapter_contract_checks",
        "operation_adapter_bindings",
        "adapter_ids",
        "read_operations",
        "corpus_read_execution_allowed",
        "read_execution_adapter_readiness_allowed",
        "source_evidence_read_execution_adapter_binding_manifest_hash",
        "source_evidence_read_execution_invocation_activation_hash",
        "source_evidence_read_execution_invocation_manifest_hash",
        "source_evidence_read_execution_authorization_hash",
        "source_evidence_read_execution_readiness_hash",
        "source_evidence_read_request_activation_hash",
        "source_evidence_task_manifest_hash",
        "source_evidence_batch_hash",
        "source_certification_hash",
        "source_dispatch_manifest_hash",
        "source_batch_hash",
        "qseries_handoff_allowed",
        "market_order_creation_allowed",
        "funds_movement_allowed",
        "portfolio_mutation_allowed",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError(f"Actual OIA-039 production contract mismatch: {missing}")


def write_full(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "from .oracle_certified_research_evidence_read_execution_adapter_authorization_gate "
        "import ("
    )
    if marker not in existing:
        INIT.write_text(
            existing.rstrip() + "\n" + INIT_BLOCK.strip() + "\n",
            encoding="utf-8",
        )
        print(f"[OK] PACKAGE UPDATED: {INIT}")
    else:
        print(f"[OK] PACKAGE ALREADY CURRENT: {INIT}")


def main() -> int:
    print("=" * 40)
    print(" OIA-040 INSTALLER")
    print(" EVIDENCE READ ADAPTER AUTHORIZATION")
    print(" READ-ONLY ADAPTER AUTHORITY BOUNDARY")
    print("=" * 40)

    verify_oia039()
    print("[OK] Actual OIA-039 adapter readiness contract verified")

    write_full(PRODUCTION, PRODUCTION_SOURCE)
    write_full(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(PRODUCTION), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    print("[OK] Production, test, and package syntax verified")

    result = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.returncode)

    print("[OK] OIA-040 test executed automatically")
    print()
    print(
        "[DONE] OIA-040 certified research evidence read execution "
        "adapter authorization gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
