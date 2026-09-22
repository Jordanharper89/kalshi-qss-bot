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

from .oracle_certified_research_evidence_collection_session_activation_gate import (
    DEFAULT_EVIDENCE_SESSION_DIRECTORY,
    EVIDENCE_ENTRY_ACTIVE,
    EVIDENCE_SESSION_ACTIVE,
    EVIDENCE_SESSION_POLICY_ID,
)

SCHEMA_VERSION = "OIA-028"
ENGINE_ID = "OIA-028"
EVIDENCE_BATCH_POLICY_ID = "oracle.certified-research-evidence-collection-batch-manifest.v1"
EVIDENCE_BATCH_ISSUED = "evidence_collection_batch_issued"
EVIDENCE_BATCH_ENTRY_AUTHORIZED = "evidence_collection_batch_entry_authorized"
DEFAULT_EVIDENCE_BATCH_DIRECTORY = Path("runtime") / "oracle_intelligence" / "certified_research_evidence_collection_batches"

READ_ONLY_CORPUS = True
EVIDENCE_COLLECTION_ALLOWED = True
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
BATCH_ARTIFACT_PERSISTENCE_ALLOWED = True

class CertifiedResearchEvidenceCollectionBatchManifestError(RuntimeError):
    pass

class CertifiedResearchEvidenceCollectionBatchManifestInvariantError(CertifiedResearchEvidenceCollectionBatchManifestError):
    pass

def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError(f"{field_name} must be timezone-aware.")
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
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()

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
    rendered = json.dumps(_canonical(payload), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", delete=False, dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
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

def _batch_id(source_session_hash: str, batch_number: int) -> str:
    return f"oia028-evidence-batch-{stable_hash({'source_evidence_session_hash': source_session_hash, 'batch_number': batch_number, 'policy': EVIDENCE_BATCH_POLICY_ID})[:32]}"

@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionBatchEntry:
    batch_sequence: int
    session_sequence: int
    evidence_sequence: int
    work_item_id: str
    worker_id: str
    dimension: str
    key: str
    tier: str
    priority_score: str
    research_objective: str
    evidence_scope_id: str
    authorized_evidence_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    batch_entry_status: str
    source_certification_entry_hash: str
    source_evidence_entry_hash: str
    source_session_entry_hash: str
    batch_entry_hash: str
    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))

@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionBatchManifest:
    schema_version: str
    engine_id: str
    generated_at: datetime
    evidence_batch_id: str
    batch_status: str
    batch_number: int
    worker_id: str
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
    batch_entry_count: int
    evidence_session_policy_id: str
    evidence_batch_policy_id: str
    entries: tuple[OracleCertifiedResearchEvidenceCollectionBatchEntry, ...]
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
    batch_artifact_persistence_allowed: bool
    evidence_batch_hash: str
    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))

class OracleCertifiedResearchEvidenceCollectionBatchManifestBuilder:
    def __init__(self, *, evidence_session_directory: Path | str = DEFAULT_EVIDENCE_SESSION_DIRECTORY, evidence_batch_directory: Path | str = DEFAULT_EVIDENCE_BATCH_DIRECTORY) -> None:
        self._evidence_session_directory = Path(evidence_session_directory)
        self._evidence_batch_directory = Path(evidence_batch_directory)

    def _load_session(self) -> dict[str, Any]:
        path = self._evidence_session_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError(f"OIA-027 current evidence session is missing: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError(f"OIA-027 current evidence session is invalid JSON: {path}") from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError("OIA-027 evidence session must be a JSON object.")
        session_hash = payload.pop("evidence_session_hash", None)
        if not _valid_hash(session_hash) or stable_hash(payload) != session_hash:
            raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError("OIA-027 evidence session hash verification failed.")
        payload["evidence_session_hash"] = session_hash
        expected = {
            "schema_version": "OIA-027", "engine_id": "OIA-027", "session_status": EVIDENCE_SESSION_ACTIVE,
            "evidence_session_policy_id": EVIDENCE_SESSION_POLICY_ID, "read_only_corpus": True,
            "evidence_collection_allowed": True, "research_execution_allowed": False,
            "analytic_conclusion_allowed": False, "forecast_creation_allowed": False,
            "signals_allowed": False, "alerts_allowed": False, "qseries_handoff_allowed": False,
            "execution_allowed": False, "trading_recommendations_allowed": False,
            "source_mutation_allowed": False, "market_order_creation_allowed": False,
            "funds_movement_allowed": False, "portfolio_mutation_allowed": False,
            "session_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError(f"OIA-027 evidence session invariant failed: {key}.")
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries or payload.get("session_entry_count") != len(entries):
            raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError("OIA-027 evidence session entries are invalid.")
        for entry in entries:
            if not isinstance(entry, dict):
                raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError("OIA-027 session entry must be an object.")
            entry_hash = entry.pop("session_entry_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError("OIA-027 session entry hash verification failed.")
            entry["session_entry_hash"] = entry_hash
            if entry.get("session_status") != EVIDENCE_ENTRY_ACTIVE:
                raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError("OIA-027 session entry is not active.")
        return payload

    def build(self, *, generated_at: datetime, batch_number: int = 1, persist: bool = True) -> OracleCertifiedResearchEvidenceCollectionBatchManifest:
        generated_at = _aware_utc(generated_at, "generated_at")
        if not isinstance(batch_number, int) or batch_number < 1:
            raise CertifiedResearchEvidenceCollectionBatchManifestInvariantError("batch_number must be a positive integer.")
        source = self._load_session()
        entries = []
        for index, source_entry in enumerate(source["entries"], start=1):
            body = {
                "batch_sequence": index, "session_sequence": source_entry["session_sequence"],
                "evidence_sequence": source_entry["evidence_sequence"], "work_item_id": source_entry["work_item_id"],
                "worker_id": source_entry["worker_id"], "dimension": source_entry["dimension"], "key": source_entry["key"],
                "tier": source_entry["tier"], "priority_score": source_entry["priority_score"],
                "research_objective": source_entry["research_objective"], "evidence_scope_id": source_entry["evidence_scope_id"],
                "authorized_evidence_operations": tuple(source_entry["authorized_evidence_operations"]),
                "prohibited_operations": tuple(source_entry["prohibited_operations"]),
                "completion_requirements": tuple(source_entry["completion_requirements"]),
                "batch_entry_status": EVIDENCE_BATCH_ENTRY_AUTHORIZED,
                "source_certification_entry_hash": source_entry["source_certification_entry_hash"],
                "source_evidence_entry_hash": source_entry["source_evidence_entry_hash"],
                "source_session_entry_hash": source_entry["session_entry_hash"],
            }
            entries.append(OracleCertifiedResearchEvidenceCollectionBatchEntry(**body, batch_entry_hash=stable_hash(body)))
        body = {
            "schema_version": SCHEMA_VERSION, "engine_id": ENGINE_ID, "generated_at": generated_at,
            "evidence_batch_id": _batch_id(source["evidence_session_hash"], batch_number),
            "batch_status": EVIDENCE_BATCH_ISSUED, "batch_number": batch_number, "worker_id": source["worker_id"],
            "source_evidence_session_id": source["evidence_session_id"],
            "source_evidence_manifest_id": source["source_evidence_manifest_id"],
            "source_certification_id": source["source_certification_id"], "source_readiness_id": source["source_readiness_id"],
            "source_session_id": source["source_session_id"], "source_activation_id": source["source_activation_id"],
            "source_claim_id": source["source_claim_id"], "dispatch_manifest_id": source["dispatch_manifest_id"],
            "selected_batch_id": source["selected_batch_id"], "selected_batch_number": source["selected_batch_number"],
            "batch_entry_count": len(entries), "evidence_session_policy_id": source["evidence_session_policy_id"],
            "evidence_batch_policy_id": EVIDENCE_BATCH_POLICY_ID, "entries": tuple(entries),
            "source_evidence_session_hash": source["evidence_session_hash"],
            "source_evidence_manifest_hash": source["source_evidence_manifest_hash"],
            "source_certification_hash": source["source_certification_hash"], "source_readiness_hash": source["source_readiness_hash"],
            "source_session_hash": source["source_session_hash"], "source_activation_hash": source["source_activation_hash"],
            "source_claim_hash": source["source_claim_hash"], "source_dispatch_manifest_hash": source["source_dispatch_manifest_hash"],
            "source_batch_hash": source["source_batch_hash"], "read_only_corpus": READ_ONLY_CORPUS,
            "evidence_collection_allowed": EVIDENCE_COLLECTION_ALLOWED, "research_execution_allowed": RESEARCH_EXECUTION_ALLOWED,
            "analytic_conclusion_allowed": ANALYTIC_CONCLUSION_ALLOWED, "forecast_creation_allowed": FORECAST_CREATION_ALLOWED,
            "signals_allowed": SIGNALS_ALLOWED, "alerts_allowed": ALERTS_ALLOWED, "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,
            "execution_allowed": EXECUTION_ALLOWED, "trading_recommendations_allowed": TRADING_RECOMMENDATIONS_ALLOWED,
            "source_mutation_allowed": SOURCE_MUTATION_ALLOWED, "market_order_creation_allowed": MARKET_ORDER_CREATION_ALLOWED,
            "funds_movement_allowed": FUNDS_MOVEMENT_ALLOWED, "portfolio_mutation_allowed": PORTFOLIO_MUTATION_ALLOWED,
            "batch_artifact_persistence_allowed": BATCH_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = OracleCertifiedResearchEvidenceCollectionBatchManifest(**body, evidence_batch_hash=stable_hash(body))
        if persist:
            payload = result.to_dict()
            _atomic_write(self._evidence_batch_directory / "current.json", payload)
            _atomic_write(self._evidence_batch_directory / "batches" / f"{result.evidence_batch_id}.json", payload)
            _atomic_write(self._evidence_batch_directory / "workers" / result.worker_id / f"{result.evidence_batch_id}.json", payload)
        return result
