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

from .oracle_certified_research_evidence_collection_batch_manifest_builder import (
    DEFAULT_EVIDENCE_BATCH_DIRECTORY,
    EVIDENCE_BATCH_ENTRY_AUTHORIZED,
    EVIDENCE_BATCH_ISSUED,
    EVIDENCE_BATCH_POLICY_ID,
)

SCHEMA_VERSION = "OIA-029"
ENGINE_ID = "OIA-029"
EVIDENCE_BATCH_ACTIVATION_POLICY_ID = "oracle.certified-research-evidence-collection-batch-activation.v1"
EVIDENCE_BATCH_ACTIVE = "evidence_collection_batch_active"
EVIDENCE_BATCH_ENTRY_ACTIVE = "evidence_collection_batch_entry_active"
DEFAULT_ACTIVE_EVIDENCE_BATCH_DIRECTORY = Path("runtime") / "oracle_intelligence" / "active_certified_research_evidence_collection_batches"

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
ACTIVE_BATCH_ARTIFACT_PERSISTENCE_ALLOWED = True

class CertifiedResearchEvidenceCollectionBatchActivationError(RuntimeError):
    pass

class CertifiedResearchEvidenceCollectionBatchActivationInvariantError(CertifiedResearchEvidenceCollectionBatchActivationError):
    pass

def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError(f"{field_name} must be timezone-aware.")
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
    encoded = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
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

def _activation_id(source_batch_hash: str) -> str:
    return f"oia029-active-evidence-batch-{stable_hash({'source_evidence_batch_hash': source_batch_hash, 'policy': EVIDENCE_BATCH_ACTIVATION_POLICY_ID})[:32]}"

@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionActiveBatchEntry:
    activation_sequence: int
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
    active_entry_status: str
    source_certification_entry_hash: str
    source_evidence_entry_hash: str
    source_session_entry_hash: str
    source_batch_entry_hash: str
    active_entry_hash: str
    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))

@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionActiveBatch:
    schema_version: str
    engine_id: str
    activated_at: datetime
    evidence_batch_activation_id: str
    active_batch_status: str
    batch_number: int
    worker_id: str
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
    active_entry_count: int
    evidence_session_policy_id: str
    evidence_batch_policy_id: str
    evidence_batch_activation_policy_id: str
    entries: tuple[OracleCertifiedResearchEvidenceCollectionActiveBatchEntry, ...]
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
    active_batch_artifact_persistence_allowed: bool
    evidence_batch_activation_hash: str
    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))

class OracleCertifiedResearchEvidenceCollectionBatchActivationGate:
    def __init__(self, *, evidence_batch_directory: Path | str = DEFAULT_EVIDENCE_BATCH_DIRECTORY, active_batch_directory: Path | str = DEFAULT_ACTIVE_EVIDENCE_BATCH_DIRECTORY) -> None:
        self._evidence_batch_directory = Path(evidence_batch_directory)
        self._active_batch_directory = Path(active_batch_directory)

    def _load_batch(self) -> dict[str, Any]:
        path = self._evidence_batch_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError(f"OIA-028 current evidence batch is missing: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError(f"OIA-028 current evidence batch is invalid JSON: {path}") from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError("OIA-028 evidence batch must be a JSON object.")
        batch_hash = payload.pop("evidence_batch_hash", None)
        if not _valid_hash(batch_hash) or stable_hash(payload) != batch_hash:
            raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError("OIA-028 evidence batch hash verification failed.")
        payload["evidence_batch_hash"] = batch_hash
        expected = {
            "schema_version": "OIA-028", "engine_id": "OIA-028", "batch_status": EVIDENCE_BATCH_ISSUED,
            "evidence_batch_policy_id": EVIDENCE_BATCH_POLICY_ID, "read_only_corpus": True,
            "evidence_collection_allowed": True, "research_execution_allowed": False,
            "analytic_conclusion_allowed": False, "forecast_creation_allowed": False,
            "signals_allowed": False, "alerts_allowed": False, "qseries_handoff_allowed": False,
            "execution_allowed": False, "trading_recommendations_allowed": False,
            "source_mutation_allowed": False, "market_order_creation_allowed": False,
            "funds_movement_allowed": False, "portfolio_mutation_allowed": False,
            "batch_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError(f"OIA-028 evidence batch invariant failed: {key}.")
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries or payload.get("batch_entry_count") != len(entries):
            raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError("OIA-028 evidence batch entries are invalid.")
        for entry in entries:
            if not isinstance(entry, dict):
                raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError("OIA-028 batch entry must be an object.")
            entry_hash = entry.pop("batch_entry_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError("OIA-028 batch entry hash verification failed.")
            entry["batch_entry_hash"] = entry_hash
            if entry.get("batch_entry_status") != EVIDENCE_BATCH_ENTRY_AUTHORIZED:
                raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError("OIA-028 batch entry is not authorized.")
        for name in ("source_evidence_session_hash", "source_evidence_manifest_hash", "source_certification_hash", "source_readiness_hash", "source_session_hash", "source_activation_hash", "source_claim_hash", "source_dispatch_manifest_hash", "source_batch_hash"):
            if not _valid_hash(payload.get(name)):
                raise CertifiedResearchEvidenceCollectionBatchActivationInvariantError(f"OIA-028 {name} is invalid.")
        return payload

    def activate(self, *, activated_at: datetime, persist: bool = True) -> OracleCertifiedResearchEvidenceCollectionActiveBatch:
        activated_at = _aware_utc(activated_at, "activated_at")
        source = self._load_batch()
        entries = []
        for sequence, source_entry in enumerate(source["entries"], start=1):
            body = {
                "activation_sequence": sequence, "batch_sequence": source_entry["batch_sequence"],
                "session_sequence": source_entry["session_sequence"], "evidence_sequence": source_entry["evidence_sequence"],
                "work_item_id": source_entry["work_item_id"], "worker_id": source_entry["worker_id"],
                "dimension": source_entry["dimension"], "key": source_entry["key"], "tier": source_entry["tier"],
                "priority_score": source_entry["priority_score"], "research_objective": source_entry["research_objective"],
                "evidence_scope_id": source_entry["evidence_scope_id"],
                "authorized_evidence_operations": tuple(source_entry["authorized_evidence_operations"]),
                "prohibited_operations": tuple(source_entry["prohibited_operations"]),
                "completion_requirements": tuple(source_entry["completion_requirements"]),
                "active_entry_status": EVIDENCE_BATCH_ENTRY_ACTIVE,
                "source_certification_entry_hash": source_entry["source_certification_entry_hash"],
                "source_evidence_entry_hash": source_entry["source_evidence_entry_hash"],
                "source_session_entry_hash": source_entry["source_session_entry_hash"],
                "source_batch_entry_hash": source_entry["batch_entry_hash"],
            }
            entries.append(OracleCertifiedResearchEvidenceCollectionActiveBatchEntry(**body, active_entry_hash=stable_hash(body)))
        body = {
            "schema_version": SCHEMA_VERSION, "engine_id": ENGINE_ID, "activated_at": activated_at,
            "evidence_batch_activation_id": _activation_id(source["evidence_batch_hash"]),
            "active_batch_status": EVIDENCE_BATCH_ACTIVE, "batch_number": source["batch_number"], "worker_id": source["worker_id"],
            "source_evidence_batch_id": source["evidence_batch_id"], "source_evidence_session_id": source["source_evidence_session_id"],
            "source_evidence_manifest_id": source["source_evidence_manifest_id"], "source_certification_id": source["source_certification_id"],
            "source_readiness_id": source["source_readiness_id"], "source_session_id": source["source_session_id"],
            "source_activation_id": source["source_activation_id"], "source_claim_id": source["source_claim_id"],
            "dispatch_manifest_id": source["dispatch_manifest_id"], "selected_batch_id": source["selected_batch_id"],
            "selected_batch_number": source["selected_batch_number"], "active_entry_count": len(entries),
            "evidence_session_policy_id": source["evidence_session_policy_id"], "evidence_batch_policy_id": source["evidence_batch_policy_id"],
            "evidence_batch_activation_policy_id": EVIDENCE_BATCH_ACTIVATION_POLICY_ID, "entries": tuple(entries),
            "source_evidence_batch_hash": source["evidence_batch_hash"], "source_evidence_session_hash": source["source_evidence_session_hash"],
            "source_evidence_manifest_hash": source["source_evidence_manifest_hash"], "source_certification_hash": source["source_certification_hash"],
            "source_readiness_hash": source["source_readiness_hash"], "source_session_hash": source["source_session_hash"],
            "source_activation_hash": source["source_activation_hash"], "source_claim_hash": source["source_claim_hash"],
            "source_dispatch_manifest_hash": source["source_dispatch_manifest_hash"], "source_batch_hash": source["source_batch_hash"],
            "read_only_corpus": READ_ONLY_CORPUS, "evidence_collection_allowed": EVIDENCE_COLLECTION_ALLOWED,
            "research_execution_allowed": RESEARCH_EXECUTION_ALLOWED, "analytic_conclusion_allowed": ANALYTIC_CONCLUSION_ALLOWED,
            "forecast_creation_allowed": FORECAST_CREATION_ALLOWED, "signals_allowed": SIGNALS_ALLOWED, "alerts_allowed": ALERTS_ALLOWED,
            "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED, "execution_allowed": EXECUTION_ALLOWED,
            "trading_recommendations_allowed": TRADING_RECOMMENDATIONS_ALLOWED, "source_mutation_allowed": SOURCE_MUTATION_ALLOWED,
            "market_order_creation_allowed": MARKET_ORDER_CREATION_ALLOWED, "funds_movement_allowed": FUNDS_MOVEMENT_ALLOWED,
            "portfolio_mutation_allowed": PORTFOLIO_MUTATION_ALLOWED,
            "active_batch_artifact_persistence_allowed": ACTIVE_BATCH_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = OracleCertifiedResearchEvidenceCollectionActiveBatch(**body, evidence_batch_activation_hash=stable_hash(body))
        if persist:
            payload = result.to_dict()
            _atomic_write(self._active_batch_directory / "current.json", payload)
            _atomic_write(self._active_batch_directory / "activations" / f"{result.evidence_batch_activation_id}.json", payload)
        return result
