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

from .oracle_certified_research_evidence_read_request_activation_gate import (
    DEFAULT_ACTIVE_EVIDENCE_READ_REQUEST_DIRECTORY,
    EVIDENCE_READ_REQUEST_ACTIVATION_ISSUED,
    EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID,
    EVIDENCE_READ_REQUEST_ACTIVE,
)

SCHEMA_VERSION = "OIA-034"
ENGINE_ID = "OIA-034"
EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-readiness.v1"
)
EVIDENCE_READ_EXECUTION_READY = "evidence_read_execution_ready"
EVIDENCE_READ_EXECUTION_ENTRY_READY = "evidence_read_execution_entry_ready"

DEFAULT_EVIDENCE_READ_EXECUTION_READINESS_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_evidence_read_execution_readiness"
)

READ_ONLY_CORPUS = True
EVIDENCE_COLLECTION_ALLOWED = True
CORPUS_READ_REQUESTS_ALLOWED = True
CORPUS_READ_EXECUTION_ALLOWED = False
READ_EXECUTION_READINESS_ALLOWED = True
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
READINESS_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionReadinessError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
    CertifiedResearchEvidenceReadExecutionReadinessError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
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


def _readiness_id(source_activation_hash: str) -> str:
    seed = {
        "source_evidence_read_request_activation_hash": source_activation_hash,
        "policy": EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
    }
    return f"oia034-read-execution-readiness-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionReadinessEntry:
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
    readiness_status: str
    source_evidence_read_request_hash: str
    source_active_evidence_read_request_hash: str
    readiness_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionReadiness:
    schema_version: str
    engine_id: str
    evaluated_at: datetime
    evidence_read_execution_readiness_id: str
    readiness_status: str
    worker_id: str
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
    readiness_entry_count: int
    evidence_read_request_activation_policy_id: str
    evidence_read_execution_readiness_policy_id: str
    entries: tuple[OracleCertifiedResearchEvidenceReadExecutionReadinessEntry, ...]
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
    readiness_artifact_persistence_allowed: bool
    evidence_read_execution_readiness_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionReadinessGate:
    def __init__(
        self,
        *,
        active_read_request_directory: Path | str = (
            DEFAULT_ACTIVE_EVIDENCE_READ_REQUEST_DIRECTORY
        ),
        readiness_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_READINESS_DIRECTORY
        ),
    ) -> None:
        self._active_read_request_directory = Path(active_read_request_directory)
        self._readiness_directory = Path(readiness_directory)

    def _load_activation(self) -> dict[str, Any]:
        path = self._active_read_request_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                f"OIA-033 current read-request activation is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                f"OIA-033 current read-request activation is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                "OIA-033 read-request activation must be a JSON object."
            )

        activation_hash = payload.pop("evidence_read_request_activation_hash", None)
        if not _valid_hash(activation_hash) or stable_hash(payload) != activation_hash:
            raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                "OIA-033 read-request activation hash verification failed."
            )
        payload["evidence_read_request_activation_hash"] = activation_hash

        expected = {
            "schema_version": "OIA-033",
            "engine_id": "OIA-033",
            "activation_status": EVIDENCE_READ_REQUEST_ACTIVATION_ISSUED,
            "evidence_read_request_activation_policy_id": (
                EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID
            ),
            "read_only_corpus": True,
            "evidence_collection_allowed": True,
            "corpus_read_requests_allowed": True,
            "corpus_read_execution_allowed": False,
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
            "active_read_request_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                    f"OIA-033 activation invariant failed: {key}."
                )

        requests = payload.get("requests")
        if (
            not isinstance(requests, list)
            or not requests
            or payload.get("active_request_count") != len(requests)
        ):
            raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                "OIA-033 active read requests are invalid."
            )

        for request in requests:
            if not isinstance(request, dict):
                raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                    "OIA-033 active read request must be an object."
                )
            request_hash = request.pop("active_evidence_read_request_hash", None)
            if not _valid_hash(request_hash) or stable_hash(request) != request_hash:
                raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                    "OIA-033 active read-request hash verification failed."
                )
            request["active_evidence_read_request_hash"] = request_hash
            if request.get("active_request_status") != EVIDENCE_READ_REQUEST_ACTIVE:
                raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                    "OIA-033 evidence read request is not active."
                )
            operations = request.get("authorized_read_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                    "OIA-033 active request has no authorized read operations."
                )
            if any(
                not isinstance(operation, str)
                or not operation.startswith("read_")
                for operation in operations
            ):
                raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                    "OIA-033 active request contains a non-read operation."
                )

        for name in (
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
                raise CertifiedResearchEvidenceReadExecutionReadinessInvariantError(
                    f"OIA-033 {name} is invalid."
                )
        return payload

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionReadiness:
        evaluated_at = _aware_utc(evaluated_at, "evaluated_at")
        source = self._load_activation()

        entries = []
        for sequence, request in enumerate(source["requests"], start=1):
            body = {
                "readiness_sequence": sequence,
                "request_sequence": request["request_sequence"],
                "task_sequence": request["task_sequence"],
                "work_item_id": request["work_item_id"],
                "worker_id": request["worker_id"],
                "dimension": request["dimension"],
                "key": request["key"],
                "evidence_scope_id": request["evidence_scope_id"],
                "authorized_read_operations": tuple(
                    request["authorized_read_operations"]
                ),
                "prohibited_operations": tuple(request["prohibited_operations"]),
                "completion_requirements": tuple(
                    request["completion_requirements"]
                ),
                "readiness_status": EVIDENCE_READ_EXECUTION_ENTRY_READY,
                "source_evidence_read_request_hash": request[
                    "source_evidence_read_request_hash"
                ],
                "source_active_evidence_read_request_hash": request[
                    "active_evidence_read_request_hash"
                ],
            }
            entries.append(
                OracleCertifiedResearchEvidenceReadExecutionReadinessEntry(
                    **body,
                    readiness_entry_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at,
            "evidence_read_execution_readiness_id": _readiness_id(
                source["evidence_read_request_activation_hash"]
            ),
            "readiness_status": EVIDENCE_READ_EXECUTION_READY,
            "worker_id": source["worker_id"],
            "source_evidence_read_request_activation_id": source[
                "evidence_read_request_activation_id"
            ],
            "source_evidence_read_request_manifest_id": source[
                "source_evidence_read_request_manifest_id"
            ],
            "source_evidence_task_activation_id": source[
                "source_evidence_task_activation_id"
            ],
            "source_evidence_task_manifest_id": source[
                "source_evidence_task_manifest_id"
            ],
            "source_evidence_batch_activation_id": source[
                "source_evidence_batch_activation_id"
            ],
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
            "readiness_entry_count": len(entries),
            "evidence_read_request_activation_policy_id": source[
                "evidence_read_request_activation_policy_id"
            ],
            "evidence_read_execution_readiness_policy_id": (
                EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID
            ),
            "entries": tuple(entries),
            "source_evidence_read_request_activation_hash": source[
                "evidence_read_request_activation_hash"
            ],
            "source_evidence_read_request_manifest_hash": source[
                "source_evidence_read_request_manifest_hash"
            ],
            "source_evidence_task_activation_hash": source[
                "source_evidence_task_activation_hash"
            ],
            "source_evidence_task_manifest_hash": source[
                "source_evidence_task_manifest_hash"
            ],
            "source_evidence_batch_activation_hash": source[
                "source_evidence_batch_activation_hash"
            ],
            "source_evidence_batch_hash": source["source_evidence_batch_hash"],
            "source_evidence_session_hash": source[
                "source_evidence_session_hash"
            ],
            "source_evidence_manifest_hash": source[
                "source_evidence_manifest_hash"
            ],
            "source_certification_hash": source["source_certification_hash"],
            "source_readiness_hash": source["source_readiness_hash"],
            "source_session_hash": source["source_session_hash"],
            "source_activation_hash": source["source_activation_hash"],
            "source_claim_hash": source["source_claim_hash"],
            "source_dispatch_manifest_hash": source[
                "source_dispatch_manifest_hash"
            ],
            "source_batch_hash": source["source_batch_hash"],
            "read_only_corpus": READ_ONLY_CORPUS,
            "evidence_collection_allowed": EVIDENCE_COLLECTION_ALLOWED,
            "corpus_read_requests_allowed": CORPUS_READ_REQUESTS_ALLOWED,
            "corpus_read_execution_allowed": CORPUS_READ_EXECUTION_ALLOWED,
            "read_execution_readiness_allowed": READ_EXECUTION_READINESS_ALLOWED,
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
            "readiness_artifact_persistence_allowed": (
                READINESS_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }
        result = OracleCertifiedResearchEvidenceReadExecutionReadiness(
            **body,
            evidence_read_execution_readiness_hash=stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._readiness_directory / "current.json", payload)
            _atomic_write(
                self._readiness_directory
                / "readiness"
                / f"{result.evidence_read_execution_readiness_id}.json",
                payload,
            )
            _atomic_write(
                self._readiness_directory
                / "workers"
                / result.worker_id
                / f"{result.evidence_read_execution_readiness_id}.json",
                payload,
            )
        return result
