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

from .oracle_qualified_research_priority_ranking_engine import RANKING_POLICY_ID
from .oracle_qualified_research_priority_tier_assignment_gate import TIER_POLICY_ID
from .oracle_qualified_research_queue_admission_gate import QUEUE_POLICY_ID
from .oracle_qualified_research_work_item_materialization_engine import WORK_ITEM_POLICY_ID
from .oracle_qualified_research_dispatch_manifest_builder import DISPATCH_POLICY_ID
from .oracle_qualified_research_dispatch_claim_gate import CLAIM_POLICY_ID
from .oracle_qualified_research_claim_activation_gate import ACTIVATION_POLICY_ID
from .oracle_qualified_research_worker_session_manifest_builder import SESSION_POLICY_ID
from .oracle_qualified_research_worker_session_readiness_gate import READINESS_POLICY_ID
from .oracle_qualified_research_worker_session_certification_gate import (
    CERTIFICATION_POLICY_ID,
    SESSION_CERTIFIED,
    ENTRY_CERTIFIED,
    DEFAULT_CERTIFICATION_DIRECTORY,
)

SCHEMA_VERSION = "OIA-026"
ENGINE_ID = "OIA-026"
EVIDENCE_MANIFEST_POLICY_ID = "oracle.certified-research-evidence-collection-manifest.v1"

EVIDENCE_MANIFEST_ISSUED = "evidence_manifest_issued"
EVIDENCE_ENTRY_AUTHORIZED = "evidence_entry_authorized"

DEFAULT_EVIDENCE_MANIFEST_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_evidence_collection_manifest"
)

READ_ONLY_CORPUS = True
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
EVIDENCE_MANIFEST_PERSISTENCE_ALLOWED = True

DEFAULT_EVIDENCE_OPERATIONS = (
    "read_canonical_observations",
    "read_market_state_lineage",
    "read_persistence_metadata",
    "read_source_provenance",
)

DEFAULT_PROHIBITED_OPERATIONS = (
    "write_source_observations",
    "mutate_canonical_corpus",
    "create_forecast",
    "create_signal",
    "create_alert",
    "handoff_to_qseries",
    "invoke_execution_adapter",
    "create_market_order",
    "move_funds",
    "mutate_portfolio",
)


class CertifiedResearchEvidenceCollectionManifestError(RuntimeError):
    pass


class CertifiedResearchEvidenceCollectionManifestInvariantError(
    CertifiedResearchEvidenceCollectionManifestError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CertifiedResearchEvidenceCollectionManifestInvariantError(
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


def _manifest_id(source_certification_hash: str, worker_id: str) -> str:
    digest = stable_hash(
        {
            "source_certification_hash": source_certification_hash,
            "worker_id": worker_id,
            "evidence_manifest_policy_id": EVIDENCE_MANIFEST_POLICY_ID,
        }
    )
    return f"oia026-evidence-manifest-{digest[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionEntry:
    evidence_sequence: int
    certification_sequence: int
    readiness_sequence: int
    session_sequence: int
    activation_sequence: int
    claim_sequence: int
    dispatch_sequence: int
    batch_number: int
    batch_position: int
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
    evidence_status: str
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    claim_policy_id: str
    activation_policy_id: str
    session_policy_id: str
    readiness_policy_id: str
    certification_policy_id: str
    evidence_manifest_policy_id: str
    source_eligibility_decision_hash: str
    source_ranking_record_hash: str
    source_tier_record_hash: str
    source_queue_record_hash: str
    source_work_item_hash: str
    source_dispatch_entry_hash: str
    source_claim_entry_hash: str
    source_activation_entry_hash: str
    source_session_entry_hash: str
    source_readiness_entry_hash: str
    source_certification_entry_hash: str
    evidence_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionManifest:
    schema_version: str
    engine_id: str
    generated_at: datetime
    evidence_manifest_id: str
    manifest_status: str
    worker_id: str
    certification_directory: str
    evidence_manifest_directory: str
    source_certification_id: str
    source_readiness_id: str
    source_session_id: str
    source_activation_id: str
    source_claim_id: str
    dispatch_manifest_id: str
    selected_batch_id: str
    selected_batch_number: int
    evidence_entry_count: int
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    claim_policy_id: str
    activation_policy_id: str
    session_policy_id: str
    readiness_policy_id: str
    certification_policy_id: str
    evidence_manifest_policy_id: str
    entries: tuple[OracleCertifiedResearchEvidenceCollectionEntry, ...]
    source_certification_hash: str
    source_readiness_hash: str
    source_session_hash: str
    source_activation_hash: str
    source_claim_hash: str
    source_dispatch_manifest_hash: str
    source_batch_hash: str
    read_only_corpus: bool
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
    evidence_manifest_persistence_allowed: bool
    evidence_manifest_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceCollectionManifestBuilder:
    def __init__(
        self,
        *,
        certification_directory: Path | str = DEFAULT_CERTIFICATION_DIRECTORY,
        evidence_manifest_directory: Path | str = DEFAULT_EVIDENCE_MANIFEST_DIRECTORY,
    ) -> None:
        self._certification_directory = Path(certification_directory)
        self._evidence_manifest_directory = Path(evidence_manifest_directory)

    def _load_certification(self) -> dict[str, Any]:
        path = self._certification_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                f"OIA-025 current certification is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                f"OIA-025 current certification is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                "OIA-025 certification must be a JSON object."
            )

        certification_hash = payload.pop("certification_hash", None)
        if not _valid_hash(certification_hash):
            raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                "OIA-025 certification_hash is invalid."
            )
        if stable_hash(payload) != certification_hash:
            raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                "OIA-025 certification hash verification failed."
            )
        payload["certification_hash"] = certification_hash

        expected = {
            "schema_version": "OIA-025",
            "engine_id": "OIA-025",
            "certification_status": SESSION_CERTIFIED,
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
            "claim_policy_id": CLAIM_POLICY_ID,
            "activation_policy_id": ACTIVATION_POLICY_ID,
            "session_policy_id": SESSION_POLICY_ID,
            "readiness_policy_id": READINESS_POLICY_ID,
            "certification_policy_id": CERTIFICATION_POLICY_ID,
            "read_only_corpus": True,
            "research_execution_allowed": False,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "trading_recommendations_allowed": False,
            "source_mutation_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "certification_artifact_persistence_allowed": True,
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                    f"OIA-025 certification invariant failed: {key}."
                )

        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                "OIA-025 certification entries must be a non-empty list."
            )
        if payload.get("certification_entry_count") != len(entries):
            raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                "OIA-025 certification entry count mismatch."
            )

        required_hashes = (
            "source_readiness_hash",
            "source_session_hash",
            "source_activation_hash",
            "source_claim_hash",
            "source_manifest_hash",
            "source_batch_hash",
        )
        for name in required_hashes:
            if not _valid_hash(payload.get(name)):
                raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                    f"OIA-025 {name} is invalid."
                )

        for entry in entries:
            if not isinstance(entry, dict):
                raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                    "OIA-025 certification entry must be an object."
                )
            entry_hash = entry.pop("certification_entry_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                    "OIA-025 certification entry hash verification failed."
                )
            entry["certification_entry_hash"] = entry_hash
            if entry.get("certification_status") != ENTRY_CERTIFIED:
                raise CertifiedResearchEvidenceCollectionManifestInvariantError(
                    "OIA-025 certification entry is not certified."
                )
        return payload

    def build(
        self,
        *,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceCollectionManifest:
        certification = self._load_certification()
        generated = _aware_utc(
            generated_at or datetime.now(timezone.utc),
            "generated_at",
        )
        worker_id = str(certification["worker_id"])
        source_certification_hash = str(certification["certification_hash"])
        manifest_id = _manifest_id(source_certification_hash, worker_id)

        entries: list[OracleCertifiedResearchEvidenceCollectionEntry] = []
        for evidence_sequence, source in enumerate(certification["entries"], start=1):
            scope_id = "evidence-scope-" + stable_hash(
                {
                    "source_certification_entry_hash": source["certification_entry_hash"],
                    "worker_id": worker_id,
                    "policy_id": EVIDENCE_MANIFEST_POLICY_ID,
                }
            )[:32]
            entry_body = {
                "evidence_sequence": evidence_sequence,
                "certification_sequence": source["certification_sequence"],
                "readiness_sequence": source["readiness_sequence"],
                "session_sequence": source["session_sequence"],
                "activation_sequence": source["activation_sequence"],
                "claim_sequence": source["claim_sequence"],
                "dispatch_sequence": source["dispatch_sequence"],
                "batch_number": source["batch_number"],
                "batch_position": source["batch_position"],
                "work_item_id": source["work_item_id"],
                "worker_id": worker_id,
                "dimension": source["dimension"],
                "key": source["key"],
                "tier": source["tier"],
                "priority_score": source["priority_score"],
                "research_objective": source["research_objective"],
                "evidence_scope_id": scope_id,
                "authorized_evidence_operations": DEFAULT_EVIDENCE_OPERATIONS,
                "prohibited_operations": DEFAULT_PROHIBITED_OPERATIONS,
                "completion_requirements": tuple(source["completion_requirements"]),
                "evidence_status": EVIDENCE_ENTRY_AUTHORIZED,
                "ranking_policy_id": RANKING_POLICY_ID,
                "tier_policy_id": TIER_POLICY_ID,
                "queue_policy_id": QUEUE_POLICY_ID,
                "work_item_policy_id": WORK_ITEM_POLICY_ID,
                "dispatch_policy_id": DISPATCH_POLICY_ID,
                "claim_policy_id": CLAIM_POLICY_ID,
                "activation_policy_id": ACTIVATION_POLICY_ID,
                "session_policy_id": SESSION_POLICY_ID,
                "readiness_policy_id": READINESS_POLICY_ID,
                "certification_policy_id": CERTIFICATION_POLICY_ID,
                "evidence_manifest_policy_id": EVIDENCE_MANIFEST_POLICY_ID,
                "source_eligibility_decision_hash": source["source_eligibility_decision_hash"],
                "source_ranking_record_hash": source["source_ranking_record_hash"],
                "source_tier_record_hash": source["source_tier_record_hash"],
                "source_queue_record_hash": source["source_queue_record_hash"],
                "source_work_item_hash": source["source_work_item_hash"],
                "source_dispatch_entry_hash": source["source_dispatch_entry_hash"],
                "source_claim_entry_hash": source["source_claim_entry_hash"],
                "source_activation_entry_hash": source["source_activation_entry_hash"],
                "source_session_entry_hash": source["source_session_entry_hash"],
                "source_readiness_entry_hash": source["source_readiness_entry_hash"],
                "source_certification_entry_hash": source["certification_entry_hash"],
            }
            entry = dict(entry_body)
            entry["evidence_entry_hash"] = stable_hash(entry_body)
            entries.append(OracleCertifiedResearchEvidenceCollectionEntry(**entry))

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated,
            "evidence_manifest_id": manifest_id,
            "manifest_status": EVIDENCE_MANIFEST_ISSUED,
            "worker_id": worker_id,
            "certification_directory": str(self._certification_directory),
            "evidence_manifest_directory": str(self._evidence_manifest_directory),
            "source_certification_id": certification["certification_id"],
            "source_readiness_id": certification["source_readiness_id"],
            "source_session_id": certification["source_session_id"],
            "source_activation_id": certification["source_activation_id"],
            "source_claim_id": certification["source_claim_id"],
            "dispatch_manifest_id": certification["manifest_id"],
            "selected_batch_id": certification["selected_batch_id"],
            "selected_batch_number": certification["selected_batch_number"],
            "evidence_entry_count": len(entries),
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
            "claim_policy_id": CLAIM_POLICY_ID,
            "activation_policy_id": ACTIVATION_POLICY_ID,
            "session_policy_id": SESSION_POLICY_ID,
            "readiness_policy_id": READINESS_POLICY_ID,
            "certification_policy_id": CERTIFICATION_POLICY_ID,
            "evidence_manifest_policy_id": EVIDENCE_MANIFEST_POLICY_ID,
            "entries": tuple(entries),
            "source_certification_hash": source_certification_hash,
            "source_readiness_hash": certification["source_readiness_hash"],
            "source_session_hash": certification["source_session_hash"],
            "source_activation_hash": certification["source_activation_hash"],
            "source_claim_hash": certification["source_claim_hash"],
            "source_dispatch_manifest_hash": certification["source_manifest_hash"],
            "source_batch_hash": certification["source_batch_hash"],
            "read_only_corpus": READ_ONLY_CORPUS,
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
            "evidence_manifest_persistence_allowed": EVIDENCE_MANIFEST_PERSISTENCE_ALLOWED,
        }
        payload = dict(body)
        payload["evidence_manifest_hash"] = stable_hash(body)
        result = OracleCertifiedResearchEvidenceCollectionManifest(**payload)
        if persist:
            self._persist(result)
        return result

    def _persist(self, manifest: OracleCertifiedResearchEvidenceCollectionManifest) -> None:
        payload = manifest.to_dict()
        _atomic_write(self._evidence_manifest_directory / "current.json", payload)
        _atomic_write(
            self._evidence_manifest_directory
            / "manifests"
            / f"{manifest.evidence_manifest_id}.json",
            payload,
        )
        _atomic_write(
            self._evidence_manifest_directory
            / "workers"
            / manifest.worker_id
            / f"{manifest.evidence_manifest_id}.json",
            payload,
        )
