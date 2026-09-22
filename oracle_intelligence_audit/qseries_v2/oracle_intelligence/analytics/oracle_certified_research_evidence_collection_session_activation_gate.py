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

from .oracle_certified_research_evidence_collection_manifest_builder import (
    EVIDENCE_ENTRY_AUTHORIZED,
    EVIDENCE_MANIFEST_ISSUED,
    EVIDENCE_MANIFEST_POLICY_ID,
    DEFAULT_EVIDENCE_MANIFEST_DIRECTORY,
)

SCHEMA_VERSION = "OIA-027"
ENGINE_ID = "OIA-027"
EVIDENCE_SESSION_POLICY_ID = "oracle.certified-research-evidence-collection-session-activation.v1"

EVIDENCE_SESSION_ACTIVE = "evidence_collection_session_active"
EVIDENCE_ENTRY_ACTIVE = "evidence_collection_entry_active"

DEFAULT_EVIDENCE_SESSION_DIRECTORY = (
    Path("runtime") / "oracle_intelligence" / "certified_research_evidence_collection_session"
)

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
SESSION_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceCollectionSessionActivationError(RuntimeError):
    pass


class CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
    CertifiedResearchEvidenceCollectionSessionActivationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
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
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
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
    rendered = json.dumps(_canonical(payload), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", delete=False,
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp",
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


def _session_id(source_manifest_hash: str, worker_id: str) -> str:
    digest = stable_hash({
        "source_evidence_manifest_hash": source_manifest_hash,
        "worker_id": worker_id,
        "evidence_session_policy_id": EVIDENCE_SESSION_POLICY_ID,
    })
    return f"oia027-evidence-session-{digest[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionSessionEntry:
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
    session_status: str
    evidence_manifest_policy_id: str
    evidence_session_policy_id: str
    source_certification_entry_hash: str
    source_evidence_entry_hash: str
    session_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionSession:
    schema_version: str
    engine_id: str
    activated_at: datetime
    evidence_session_id: str
    session_status: str
    worker_id: str
    evidence_manifest_directory: str
    evidence_session_directory: str
    source_evidence_manifest_id: str
    source_certification_id: str
    source_readiness_id: str
    source_session_id: str
    source_activation_id: str
    source_claim_id: str
    dispatch_manifest_id: str
    selected_batch_id: str
    selected_batch_number: int
    session_entry_count: int
    evidence_manifest_policy_id: str
    evidence_session_policy_id: str
    entries: tuple[OracleCertifiedResearchEvidenceCollectionSessionEntry, ...]
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
    session_artifact_persistence_allowed: bool
    evidence_session_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceCollectionSessionActivationGate:
    def __init__(
        self,
        *,
        evidence_manifest_directory: Path | str = DEFAULT_EVIDENCE_MANIFEST_DIRECTORY,
        evidence_session_directory: Path | str = DEFAULT_EVIDENCE_SESSION_DIRECTORY,
    ) -> None:
        self._evidence_manifest_directory = Path(evidence_manifest_directory)
        self._evidence_session_directory = Path(evidence_session_directory)

    def _load_manifest(self) -> dict[str, Any]:
        path = self._evidence_manifest_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                f"OIA-026 current evidence manifest is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                f"OIA-026 current evidence manifest is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                "OIA-026 evidence manifest must be a JSON object."
            )
        manifest_hash = payload.pop("evidence_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                "OIA-026 evidence manifest hash verification failed."
            )
        payload["evidence_manifest_hash"] = manifest_hash
        expected = {
            "schema_version": "OIA-026",
            "engine_id": "OIA-026",
            "manifest_status": EVIDENCE_MANIFEST_ISSUED,
            "evidence_manifest_policy_id": EVIDENCE_MANIFEST_POLICY_ID,
            "read_only_corpus": True,
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
            "evidence_manifest_persistence_allowed": True,
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                    f"OIA-026 evidence manifest invariant failed: {key}."
                )
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                "OIA-026 evidence manifest entries must be a non-empty list."
            )
        if payload.get("evidence_entry_count") != len(entries):
            raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                "OIA-026 evidence entry count mismatch."
            )
        for name in (
            "source_certification_hash", "source_readiness_hash", "source_session_hash",
            "source_activation_hash", "source_claim_hash", "source_dispatch_manifest_hash",
            "source_batch_hash",
        ):
            if not _valid_hash(payload.get(name)):
                raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                    f"OIA-026 {name} is invalid."
                )
        for entry in entries:
            if not isinstance(entry, dict):
                raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                    "OIA-026 evidence entry must be an object."
                )
            entry_hash = entry.pop("evidence_entry_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                    "OIA-026 evidence entry hash verification failed."
                )
            entry["evidence_entry_hash"] = entry_hash
            if entry.get("evidence_status") != EVIDENCE_ENTRY_AUTHORIZED:
                raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                    "OIA-026 evidence entry is not authorized."
                )
            operations = entry.get("authorized_evidence_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                    "OIA-026 authorized evidence operations are missing."
                )
            prohibited = entry.get("prohibited_operations")
            if not isinstance(prohibited, list) or "create_market_order" not in prohibited:
                raise CertifiedResearchEvidenceCollectionSessionActivationInvariantError(
                    "OIA-026 prohibited operations contract is incomplete."
                )
        return payload

    def activate(
        self,
        *,
        activated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceCollectionSession:
        manifest = self._load_manifest()
        activated = _aware_utc(activated_at or datetime.now(timezone.utc), "activated_at")
        worker_id = str(manifest["worker_id"])
        source_manifest_hash = str(manifest["evidence_manifest_hash"])
        session_id = _session_id(source_manifest_hash, worker_id)

        entries: list[OracleCertifiedResearchEvidenceCollectionSessionEntry] = []
        for session_sequence, source in enumerate(manifest["entries"], start=1):
            entry_body = {
                "session_sequence": session_sequence,
                "evidence_sequence": source["evidence_sequence"],
                "work_item_id": source["work_item_id"],
                "worker_id": worker_id,
                "dimension": source["dimension"],
                "key": source["key"],
                "tier": source["tier"],
                "priority_score": source["priority_score"],
                "research_objective": source["research_objective"],
                "evidence_scope_id": source["evidence_scope_id"],
                "authorized_evidence_operations": tuple(source["authorized_evidence_operations"]),
                "prohibited_operations": tuple(source["prohibited_operations"]),
                "completion_requirements": tuple(source["completion_requirements"]),
                "session_status": EVIDENCE_ENTRY_ACTIVE,
                "evidence_manifest_policy_id": EVIDENCE_MANIFEST_POLICY_ID,
                "evidence_session_policy_id": EVIDENCE_SESSION_POLICY_ID,
                "source_certification_entry_hash": source["source_certification_entry_hash"],
                "source_evidence_entry_hash": source["evidence_entry_hash"],
            }
            payload = dict(entry_body)
            payload["session_entry_hash"] = stable_hash(entry_body)
            entries.append(OracleCertifiedResearchEvidenceCollectionSessionEntry(**payload))

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated,
            "evidence_session_id": session_id,
            "session_status": EVIDENCE_SESSION_ACTIVE,
            "worker_id": worker_id,
            "evidence_manifest_directory": str(self._evidence_manifest_directory),
            "evidence_session_directory": str(self._evidence_session_directory),
            "source_evidence_manifest_id": manifest["evidence_manifest_id"],
            "source_certification_id": manifest["source_certification_id"],
            "source_readiness_id": manifest["source_readiness_id"],
            "source_session_id": manifest["source_session_id"],
            "source_activation_id": manifest["source_activation_id"],
            "source_claim_id": manifest["source_claim_id"],
            "dispatch_manifest_id": manifest["dispatch_manifest_id"],
            "selected_batch_id": manifest["selected_batch_id"],
            "selected_batch_number": manifest["selected_batch_number"],
            "session_entry_count": len(entries),
            "evidence_manifest_policy_id": EVIDENCE_MANIFEST_POLICY_ID,
            "evidence_session_policy_id": EVIDENCE_SESSION_POLICY_ID,
            "entries": tuple(entries),
            "source_evidence_manifest_hash": source_manifest_hash,
            "source_certification_hash": manifest["source_certification_hash"],
            "source_readiness_hash": manifest["source_readiness_hash"],
            "source_session_hash": manifest["source_session_hash"],
            "source_activation_hash": manifest["source_activation_hash"],
            "source_claim_hash": manifest["source_claim_hash"],
            "source_dispatch_manifest_hash": manifest["source_dispatch_manifest_hash"],
            "source_batch_hash": manifest["source_batch_hash"],
            "read_only_corpus": READ_ONLY_CORPUS,
            "evidence_collection_allowed": EVIDENCE_COLLECTION_ALLOWED,
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
            "session_artifact_persistence_allowed": SESSION_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        payload = dict(body)
        payload["evidence_session_hash"] = stable_hash(body)
        result = OracleCertifiedResearchEvidenceCollectionSession(**payload)
        if persist:
            self._persist(result)
        return result

    def _persist(self, session: OracleCertifiedResearchEvidenceCollectionSession) -> None:
        payload = session.to_dict()
        _atomic_write(self._evidence_session_directory / "current.json", payload)
        _atomic_write(
            self._evidence_session_directory / "sessions" / f"{session.evidence_session_id}.json",
            payload,
        )
        _atomic_write(
            self._evidence_session_directory / "workers" / session.worker_id /
            f"{session.evidence_session_id}.json", payload,
        )
