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
from .oracle_qualified_research_worker_session_readiness_gate import (
    READINESS_POLICY_ID,
    READINESS_VERIFIED,
    ENTRY_READINESS_VERIFIED,
    DEFAULT_READINESS_DIRECTORY,
    stable_hash as readiness_stable_hash,
)

SCHEMA_VERSION = "OIA-025"
ENGINE_ID = "OIA-025"
CERTIFICATION_POLICY_ID = "oracle.qualified-research-worker-session-certification.v1"

SESSION_CERTIFIED = "session_certified"
ENTRY_CERTIFIED = "entry_certified"

READ_ONLY_CORPUS = True
RESEARCH_EXECUTION_ALLOWED = False
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
MARKET_ORDER_CREATION_ALLOWED = False
FUNDS_MOVEMENT_ALLOWED = False
PORTFOLIO_MUTATION_ALLOWED = False
CERTIFICATION_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_CERTIFICATION_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_worker_session_certification"
)


class QualifiedResearchWorkerSessionCertificationError(RuntimeError):
    pass


class QualifiedResearchWorkerSessionCertificationInvariantError(
    QualifiedResearchWorkerSessionCertificationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise QualifiedResearchWorkerSessionCertificationInvariantError(
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


def _certification_id(source_readiness_hash: str, worker_id: str) -> str:
    digest = stable_hash(
        {
            "source_readiness_hash": source_readiness_hash,
            "worker_id": worker_id,
            "certification_policy_id": CERTIFICATION_POLICY_ID,
        }
    )
    return f"oia025-certification-{digest[:32]}"


@dataclass(frozen=True)
class OracleQualifiedResearchWorkerSessionCertificationEntry:
    certification_sequence: int
    readiness_sequence: int
    session_sequence: int
    activation_sequence: int
    claim_sequence: int
    dispatch_sequence: int
    batch_number: int
    batch_position: int
    work_item_id: str
    queue_position: int
    source_rank: int
    dimension: str
    key: str
    tier: str
    priority_score: str
    research_objective: str
    required_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    certification_status: str
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
    certification_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleQualifiedResearchWorkerSessionCertification:
    schema_version: str
    engine_id: str
    certified_at: datetime
    certification_id: str
    certification_status: str
    worker_id: str
    readiness_directory: str
    certification_directory: str
    source_readiness_id: str
    source_session_id: str
    source_activation_id: str
    source_claim_id: str
    manifest_id: str
    selected_batch_id: str
    selected_batch_number: int
    certification_entry_count: int
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
    entries: tuple[OracleQualifiedResearchWorkerSessionCertificationEntry, ...]
    source_readiness_hash: str
    source_session_hash: str
    source_activation_hash: str
    source_claim_hash: str
    source_manifest_hash: str
    source_batch_hash: str
    read_only_corpus: bool
    research_execution_allowed: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    certification_artifact_persistence_allowed: bool
    certification_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleQualifiedResearchWorkerSessionCertificationGate:
    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        certification_directory: Path | str = DEFAULT_CERTIFICATION_DIRECTORY,
    ) -> None:
        self._readiness_directory = Path(readiness_directory)
        self._certification_directory = Path(certification_directory)

    def _load_readiness(self) -> dict[str, Any]:
        path = self._readiness_directory / "current.json"
        if not path.exists():
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                f"OIA-024 current readiness is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                f"OIA-024 current readiness is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                "OIA-024 readiness must be a JSON object."
            )

        readiness_hash = payload.pop("readiness_hash", None)
        expected = {
            "schema_version": "OIA-024",
            "engine_id": "OIA-024",
            "readiness_status": READINESS_VERIFIED,
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
            "claim_policy_id": CLAIM_POLICY_ID,
            "activation_policy_id": ACTIVATION_POLICY_ID,
            "session_policy_id": SESSION_POLICY_ID,
            "readiness_policy_id": READINESS_POLICY_ID,
        }
        for field_name, expected_value in expected.items():
            if payload.get(field_name) != expected_value:
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    f"OIA-024 identity mismatch: {field_name}."
                )

        if readiness_hash != readiness_stable_hash(payload):
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                "OIA-024 readiness hash verification failed."
            )
        if not _valid_hash(readiness_hash):
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                "OIA-024 readiness hash is malformed."
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                "OIA-024 read-only corpus invariant failed."
            )
        if payload.get("readiness_artifact_persistence_allowed") is not True:
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                "OIA-024 readiness persistence invariant failed."
            )
        for field_name in (
            "research_execution_allowed",
            "execution_allowed",
            "alerts_allowed",
            "qseries_handoff_allowed",
            "signals_allowed",
            "trading_recommendations_allowed",
            "source_mutation_allowed",
            "market_order_creation_allowed",
            "funds_movement_allowed",
            "portfolio_mutation_allowed",
        ):
            if payload.get(field_name) is not False:
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    f"OIA-024 safety boundary mismatch: {field_name}."
                )

        for field_name in (
            "source_session_hash",
            "source_activation_hash",
            "source_claim_hash",
            "source_manifest_hash",
            "source_batch_hash",
        ):
            if not _valid_hash(payload.get(field_name)):
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    f"OIA-024 {field_name} is malformed."
                )

        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                "OIA-024 readiness entries must be a non-empty list."
            )
        if int(payload.get("readiness_entry_count", -1)) != len(entries):
            raise QualifiedResearchWorkerSessionCertificationInvariantError(
                "OIA-024 readiness entry count mismatch."
            )

        verified: list[dict[str, Any]] = []
        seen_work_items: set[str] = set()
        seen_hashes: set[str] = set()
        previous_dispatch: int | None = None
        for index, raw in enumerate(entries, start=1):
            if not isinstance(raw, dict):
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    f"OIA-024 readiness entry {index} must be an object."
                )
            entry = dict(raw)
            entry_hash = entry.pop("readiness_entry_hash", None)
            if entry_hash != readiness_stable_hash(entry):
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    f"OIA-024 readiness-entry hash failed at index {index}."
                )
            if not _valid_hash(entry_hash):
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    "OIA-024 readiness-entry hash is malformed."
                )
            if int(entry.get("readiness_sequence", -1)) != index:
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    "OIA-024 readiness sequences must be contiguous."
                )
            if entry.get("readiness_status") != ENTRY_READINESS_VERIFIED:
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    "OIA-024 readiness entry is not verified."
                )
            dispatch_sequence = int(entry.get("dispatch_sequence", -1))
            if previous_dispatch is not None and dispatch_sequence != previous_dispatch + 1:
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    "OIA-024 dispatch sequence is not contiguous."
                )
            previous_dispatch = dispatch_sequence
            work_item_id = str(entry.get("work_item_id", ""))
            if not work_item_id.startswith("oia019-"):
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    "OIA-024 work-item ID is malformed."
                )
            if work_item_id in seen_work_items or entry_hash in seen_hashes:
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    "Duplicate OIA-024 readiness lineage."
                )
            for field_name, expected_value in (
                ("ranking_policy_id", RANKING_POLICY_ID),
                ("tier_policy_id", TIER_POLICY_ID),
                ("queue_policy_id", QUEUE_POLICY_ID),
                ("work_item_policy_id", WORK_ITEM_POLICY_ID),
                ("dispatch_policy_id", DISPATCH_POLICY_ID),
                ("claim_policy_id", CLAIM_POLICY_ID),
                ("activation_policy_id", ACTIVATION_POLICY_ID),
                ("session_policy_id", SESSION_POLICY_ID),
                ("readiness_policy_id", READINESS_POLICY_ID),
            ):
                if entry.get(field_name) != expected_value:
                    raise QualifiedResearchWorkerSessionCertificationInvariantError(
                        f"OIA-024 entry policy mismatch: {field_name}."
                    )
            for field_name in (
                "source_eligibility_decision_hash",
                "source_ranking_record_hash",
                "source_tier_record_hash",
                "source_queue_record_hash",
                "source_work_item_hash",
                "source_dispatch_entry_hash",
                "source_claim_entry_hash",
                "source_activation_entry_hash",
                "source_session_entry_hash",
            ):
                if not _valid_hash(entry.get(field_name)):
                    raise QualifiedResearchWorkerSessionCertificationInvariantError(
                        f"OIA-024 {field_name} is malformed."
                    )
            for field_name in (
                "required_operations",
                "prohibited_operations",
                "completion_requirements",
            ):
                value = entry.get(field_name)
                if not isinstance(value, list) or not value:
                    raise QualifiedResearchWorkerSessionCertificationInvariantError(
                        f"OIA-024 {field_name} must be a non-empty list."
                    )
            required_prohibitions = {
                "create_trading_signal",
                "create_trading_recommendation",
                "publish_operator_alert",
                "handoff_to_qseries_execution",
                "create_market_order",
                "move_funds",
                "mutate_portfolio",
                "mutate_source_corpus",
            }
            if not required_prohibitions.issubset(set(entry["prohibited_operations"])):
                raise QualifiedResearchWorkerSessionCertificationInvariantError(
                    "OIA-024 prohibited-operation boundary is incomplete."
                )
            entry["readiness_entry_hash"] = entry_hash
            verified.append(entry)
            seen_work_items.add(work_item_id)
            seen_hashes.add(entry_hash)

        payload["entries"] = verified
        payload["readiness_hash"] = readiness_hash
        return payload

    def certify(
        self,
        *,
        certified_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchWorkerSessionCertification:
        certified_at = _aware_utc(
            certified_at or datetime.now(timezone.utc),
            "certified_at",
        )
        readiness = self._load_readiness()
        source_readiness_hash = str(readiness["readiness_hash"])
        worker_id = str(readiness["worker_id"])
        certification_id = _certification_id(source_readiness_hash, worker_id)

        entries: list[OracleQualifiedResearchWorkerSessionCertificationEntry] = []
        for sequence, source in enumerate(readiness["entries"], start=1):
            body = {
                "certification_sequence": sequence,
                "readiness_sequence": int(source["readiness_sequence"]),
                "session_sequence": int(source["session_sequence"]),
                "activation_sequence": int(source["activation_sequence"]),
                "claim_sequence": int(source["claim_sequence"]),
                "dispatch_sequence": int(source["dispatch_sequence"]),
                "batch_number": int(source["batch_number"]),
                "batch_position": int(source["batch_position"]),
                "work_item_id": str(source["work_item_id"]),
                "queue_position": int(source["queue_position"]),
                "source_rank": int(source["source_rank"]),
                "dimension": str(source["dimension"]),
                "key": str(source["key"]),
                "tier": str(source["tier"]),
                "priority_score": str(source["priority_score"]),
                "research_objective": str(source["research_objective"]),
                "required_operations": tuple(source["required_operations"]),
                "prohibited_operations": tuple(source["prohibited_operations"]),
                "completion_requirements": tuple(source["completion_requirements"]),
                "certification_status": ENTRY_CERTIFIED,
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
                "source_eligibility_decision_hash": str(source["source_eligibility_decision_hash"]),
                "source_ranking_record_hash": str(source["source_ranking_record_hash"]),
                "source_tier_record_hash": str(source["source_tier_record_hash"]),
                "source_queue_record_hash": str(source["source_queue_record_hash"]),
                "source_work_item_hash": str(source["source_work_item_hash"]),
                "source_dispatch_entry_hash": str(source["source_dispatch_entry_hash"]),
                "source_claim_entry_hash": str(source["source_claim_entry_hash"]),
                "source_activation_entry_hash": str(source["source_activation_entry_hash"]),
                "source_session_entry_hash": str(source["source_session_entry_hash"]),
                "source_readiness_entry_hash": str(source["readiness_entry_hash"]),
            }
            entries.append(
                OracleQualifiedResearchWorkerSessionCertificationEntry(
                    **body,
                    certification_entry_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "certified_at": certified_at,
            "certification_id": certification_id,
            "certification_status": SESSION_CERTIFIED,
            "worker_id": worker_id,
            "readiness_directory": str(self._readiness_directory),
            "certification_directory": str(self._certification_directory),
            "source_readiness_id": str(readiness["readiness_id"]),
            "source_session_id": str(readiness["source_session_id"]),
            "source_activation_id": str(readiness["source_activation_id"]),
            "source_claim_id": str(readiness["source_claim_id"]),
            "manifest_id": str(readiness["manifest_id"]),
            "selected_batch_id": str(readiness["selected_batch_id"]),
            "selected_batch_number": int(readiness["selected_batch_number"]),
            "certification_entry_count": len(entries),
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
            "entries": tuple(entries),
            "source_readiness_hash": source_readiness_hash,
            "source_session_hash": str(readiness["source_session_hash"]),
            "source_activation_hash": str(readiness["source_activation_hash"]),
            "source_claim_hash": str(readiness["source_claim_hash"]),
            "source_manifest_hash": str(readiness["source_manifest_hash"]),
            "source_batch_hash": str(readiness["source_batch_hash"]),
            "read_only_corpus": READ_ONLY_CORPUS,
            "research_execution_allowed": RESEARCH_EXECUTION_ALLOWED,
            "execution_allowed": EXECUTION_ALLOWED,
            "alerts_allowed": ALERTS_ALLOWED,
            "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,
            "signals_allowed": SIGNALS_ALLOWED,
            "trading_recommendations_allowed": TRADING_RECOMMENDATIONS_ALLOWED,
            "source_mutation_allowed": SOURCE_MUTATION_ALLOWED,
            "market_order_creation_allowed": MARKET_ORDER_CREATION_ALLOWED,
            "funds_movement_allowed": FUNDS_MOVEMENT_ALLOWED,
            "portfolio_mutation_allowed": PORTFOLIO_MUTATION_ALLOWED,
            "certification_artifact_persistence_allowed": CERTIFICATION_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        certification = OracleQualifiedResearchWorkerSessionCertification(
            **body,
            certification_hash=stable_hash(body),
        )
        if persist:
            payload = dict(certification.to_dict())
            _atomic_write(self._certification_directory / "current.json", payload)
            _atomic_write(
                self._certification_directory
                / "certifications"
                / f"{certification.certification_id}-{certification.certification_hash}.json",
                payload,
            )
            _atomic_write(
                self._certification_directory
                / "workers"
                / worker_id
                / f"{certification.certification_id}.json",
                payload,
            )
        return certification


def format_certification(
    certification: OracleQualifiedResearchWorkerSessionCertification,
) -> str:
    return "\n".join(
        [
            "=" * 154,
            "ORACLE QUALIFIED RESEARCH WORKER SESSION CERTIFICATION",
            "=" * 154,
            f"Certified at:         {certification.certified_at.isoformat()}",
            f"Certification ID:     {certification.certification_id}",
            f"Certification status: {certification.certification_status}",
            f"Worker ID:            {certification.worker_id}",
            f"Certified entries:     {certification.certification_entry_count}",
            f"Source readiness hash: {certification.source_readiness_hash}",
            f"Certification hash:    {certification.certification_hash}",
            "Read-only corpus:      YES",
            "Research execution:    DISABLED",
            "Q Series handoff:      DISABLED",
            "Trading authority:     DISABLED",
        ]
    )
