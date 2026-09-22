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

from .oracle_certified_research_evidence_read_execution_readiness_gate import (
    DEFAULT_EVIDENCE_READ_EXECUTION_READINESS_DIRECTORY,
    EVIDENCE_READ_EXECUTION_ENTRY_READY,
    EVIDENCE_READ_EXECUTION_READY,
    EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
)

SCHEMA_VERSION = "OIA-035"
ENGINE_ID = "OIA-035"
EVIDENCE_READ_EXECUTION_AUTHORIZATION_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-authorization.v1"
)
EVIDENCE_READ_EXECUTION_AUTHORIZED = "evidence_read_execution_authorized"
EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED = "evidence_read_execution_entry_authorized"
DEFAULT_EVIDENCE_READ_EXECUTION_AUTHORIZATION_DIRECTORY = (
    Path("runtime") / "oracle_intelligence"
    / "certified_research_evidence_read_execution_authorization"
)

READ_ONLY_CORPUS = True
EVIDENCE_COLLECTION_ALLOWED = True
CORPUS_READ_REQUESTS_ALLOWED = True
CORPUS_READ_EXECUTION_ALLOWED = False
READ_EXECUTION_READINESS_ALLOWED = True
READ_EXECUTION_AUTHORIZATION_ALLOWED = True
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
AUTHORIZATION_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionAuthorizationError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
    CertifiedResearchEvidenceReadExecutionAuthorizationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
            f"{field_name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _valid_hash(value: Any) -> bool:
    try:
        return isinstance(value, str) and len(value) == 64 and int(value, 16) >= 0
    except ValueError:
        return False


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_canonical(payload), sort_keys=True, indent=2) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", delete=False,
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp",
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAuthorizationEntry:
    authorization_sequence: int
    readiness_sequence: int
    request_sequence: int
    task_sequence: int
    work_item_id: str
    worker_id: str
    dimension: str
    key: str
    evidence_scope_id: str
    authorized_read_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    authorization_status: str
    source_evidence_read_request_hash: str
    source_active_evidence_read_request_hash: str
    source_readiness_entry_hash: str
    authorization_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAuthorization:
    schema_version: str
    engine_id: str
    authorized_at: datetime
    evidence_read_execution_authorization_id: str
    authorization_status: str
    worker_id: str
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
    authorization_entry_count: int
    evidence_read_execution_readiness_policy_id: str
    evidence_read_execution_authorization_policy_id: str
    entries: tuple[OracleCertifiedResearchEvidenceReadExecutionAuthorizationEntry, ...]
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
    evidence_read_execution_authorization_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionAuthorizationGate:
    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_EVIDENCE_READ_EXECUTION_READINESS_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_EVIDENCE_READ_EXECUTION_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self._readiness_directory = Path(readiness_directory)
        self._authorization_directory = Path(authorization_directory)

    def _load(self) -> dict[str, Any]:
        path = self._readiness_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                f"OIA-034 current readiness is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness is invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness must be an object."
            )

        readiness_hash = payload.pop("evidence_read_execution_readiness_hash", None)
        if not _valid_hash(readiness_hash) or stable_hash(payload) != readiness_hash:
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness hash verification failed."
            )
        payload["evidence_read_execution_readiness_hash"] = readiness_hash

        expected = {
            "schema_version": "OIA-034",
            "engine_id": "OIA-034",
            "readiness_status": EVIDENCE_READ_EXECUTION_READY,
            "evidence_read_execution_readiness_policy_id":
                EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
            "read_only_corpus": True,
            "evidence_collection_allowed": True,
            "corpus_read_requests_allowed": True,
            "corpus_read_execution_allowed": False,
            "read_execution_readiness_allowed": True,
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
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    f"OIA-034 invariant failed: {key}."
                )

        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness entries are missing."
            )
        if payload.get("readiness_entry_count") != len(entries):
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness entry count mismatch."
            )

        for entry in entries:
            entry_hash = entry.pop("readiness_entry_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    "OIA-034 readiness-entry hash verification failed."
                )
            entry["readiness_entry_hash"] = entry_hash
            if entry.get("readiness_status") != EVIDENCE_READ_EXECUTION_ENTRY_READY:
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    "OIA-034 readiness entry is not ready."
                )
            operations = entry.get("authorized_read_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    "OIA-034 readiness entry has no read operations."
                )
            if any(not isinstance(op, str) or not op.startswith("read_") for op in operations):
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    "OIA-034 readiness entry contains a non-read operation."
                )

        for key in (
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
            if not _valid_hash(payload.get(key)):
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    f"OIA-034 lineage hash invalid: {key}."
                )
        return payload

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionAuthorization:
        authorized_at = _aware_utc(authorized_at, "authorized_at")
        source = self._load()

        entries = []
        for sequence, item in enumerate(source["entries"], start=1):
            body = {
                "authorization_sequence": sequence,
                "readiness_sequence": item["readiness_sequence"],
                "request_sequence": item["request_sequence"],
                "task_sequence": item["task_sequence"],
                "work_item_id": item["work_item_id"],
                "worker_id": item["worker_id"],
                "dimension": item["dimension"],
                "key": item["key"],
                "evidence_scope_id": item["evidence_scope_id"],
                "authorized_read_operations": tuple(item["authorized_read_operations"]),
                "prohibited_operations": tuple(item["prohibited_operations"]),
                "completion_requirements": tuple(item["completion_requirements"]),
                "authorization_status": EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED,
                "source_evidence_read_request_hash":
                    item["source_evidence_read_request_hash"],
                "source_active_evidence_read_request_hash":
                    item["source_active_evidence_read_request_hash"],
                "source_readiness_entry_hash": item["readiness_entry_hash"],
            }
            entries.append(
                OracleCertifiedResearchEvidenceReadExecutionAuthorizationEntry(
                    **body, authorization_entry_hash=stable_hash(body)
                )
            )

        authorization_id = (
            "oia035-read-execution-authorization-"
            + stable_hash({
                "source": source["evidence_read_execution_readiness_hash"],
                "policy": EVIDENCE_READ_EXECUTION_AUTHORIZATION_POLICY_ID,
            })[:32]
        )
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at,
            "evidence_read_execution_authorization_id": authorization_id,
            "authorization_status": EVIDENCE_READ_EXECUTION_AUTHORIZED,
            "worker_id": source["worker_id"],
            "source_evidence_read_execution_readiness_id":
                source["evidence_read_execution_readiness_id"],
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
            "authorization_entry_count": len(entries),
            "evidence_read_execution_readiness_policy_id":
                source["evidence_read_execution_readiness_policy_id"],
            "evidence_read_execution_authorization_policy_id":
                EVIDENCE_READ_EXECUTION_AUTHORIZATION_POLICY_ID,
            "entries": tuple(entries),
            "source_evidence_read_execution_readiness_hash":
                source["evidence_read_execution_readiness_hash"],
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
            "source_evidence_session_hash": source["source_evidence_session_hash"],
            "source_evidence_manifest_hash": source["source_evidence_manifest_hash"],
            "source_certification_hash": source["source_certification_hash"],
            "source_readiness_hash": source["source_readiness_hash"],
            "source_session_hash": source["source_session_hash"],
            "source_activation_hash": source["source_activation_hash"],
            "source_claim_hash": source["source_claim_hash"],
            "source_dispatch_manifest_hash": source["source_dispatch_manifest_hash"],
            "source_batch_hash": source["source_batch_hash"],
            "read_only_corpus": READ_ONLY_CORPUS,
            "evidence_collection_allowed": EVIDENCE_COLLECTION_ALLOWED,
            "corpus_read_requests_allowed": CORPUS_READ_REQUESTS_ALLOWED,
            "corpus_read_execution_allowed": CORPUS_READ_EXECUTION_ALLOWED,
            "read_execution_readiness_allowed": READ_EXECUTION_READINESS_ALLOWED,
            "read_execution_authorization_allowed":
                READ_EXECUTION_AUTHORIZATION_ALLOWED,
            "research_execution_allowed": RESEARCH_EXECUTION_ALLOWED,
            "analytic_conclusion_allowed": ANALYTIC_CONCLUSION_ALLOWED,
            "forecast_creation_allowed": FORECAST_CREATION_ALLOWED,
            "signals_allowed": SIGNALS_ALLOWED,
            "alerts_allowed": ALERTS_ALLOWED,
            "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,
            "execution_allowed": EXECUTION_ALLOWED,
            "trading_recommendations_allowed": TRADING_RECOMMENDATIONS_ALLOWED,
            "source_mutation_allowed": SOURCE_MUTATION_ALLOWED,
            "market_order_creation_allowed": MARKET_ORDER_CREATION_ALLOWED,
            "funds_movement_allowed": FUNDS_MOVEMENT_ALLOWED,
            "portfolio_mutation_allowed": PORTFOLIO_MUTATION_ALLOWED,
            "authorization_artifact_persistence_allowed":
                AUTHORIZATION_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = OracleCertifiedResearchEvidenceReadExecutionAuthorization(
            **body,
            evidence_read_execution_authorization_hash=stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._authorization_directory / "current.json", payload)
            _atomic_write(
                self._authorization_directory / "authorizations"
                / f"{authorization_id}.json", payload,
            )
            _atomic_write(
                self._authorization_directory / "workers" / result.worker_id
                / f"{authorization_id}.json", payload,
            )
        return result
