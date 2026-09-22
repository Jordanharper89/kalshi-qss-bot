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

from .oracle_certified_research_evidence_read_request_manifest_builder import (
    DEFAULT_EVIDENCE_READ_REQUEST_DIRECTORY,
    EVIDENCE_READ_REQUEST_MANIFEST_ISSUED,
    EVIDENCE_READ_REQUEST_POLICY_ID,
    EVIDENCE_READ_REQUEST_READY,
)

SCHEMA_VERSION = "OIA-033"
ENGINE_ID = "OIA-033"
EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID = (
    "oracle.certified-research-evidence-read-request-activation.v1"
)
EVIDENCE_READ_REQUEST_ACTIVATION_ISSUED = (
    "evidence_read_request_activation_issued"
)
EVIDENCE_READ_REQUEST_ACTIVE = "evidence_read_request_active"

DEFAULT_ACTIVE_EVIDENCE_READ_REQUEST_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_active_evidence_read_requests"
)

READ_ONLY_CORPUS = True
EVIDENCE_COLLECTION_ALLOWED = True
CORPUS_READ_REQUESTS_ALLOWED = True
CORPUS_READ_EXECUTION_ALLOWED = False
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
ACTIVE_READ_REQUEST_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadRequestActivationError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadRequestActivationInvariantError(
    CertifiedResearchEvidenceReadRequestActivationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
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
    rendered = (
        json.dumps(
            _canonical(payload),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
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
        "source_evidence_read_request_manifest_hash": source_manifest_hash,
        "policy": EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID,
    }
    return f"oia033-evidence-read-activation-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchActiveEvidenceReadRequest:
    activation_sequence: int
    request_sequence: int
    task_sequence: int
    work_item_id: str
    worker_id: str
    dimension: str
    key: str
    tier: str
    priority_score: str
    research_objective: str
    evidence_scope_id: str
    authorized_read_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    active_request_status: str
    source_task_hash: str
    source_active_task_hash: str
    source_evidence_read_request_hash: str
    active_evidence_read_request_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadRequestActivation:
    schema_version: str
    engine_id: str
    activated_at: datetime
    evidence_read_request_activation_id: str
    activation_status: str
    worker_id: str
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
    active_request_count: int
    evidence_task_manifest_policy_id: str
    evidence_task_activation_policy_id: str
    evidence_read_request_policy_id: str
    evidence_read_request_activation_policy_id: str
    requests: tuple[OracleCertifiedResearchActiveEvidenceReadRequest, ...]
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
    active_read_request_artifact_persistence_allowed: bool
    evidence_read_request_activation_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadRequestActivationGate:
    def __init__(
        self,
        *,
        read_request_directory: Path | str = DEFAULT_EVIDENCE_READ_REQUEST_DIRECTORY,
        active_read_request_directory: Path | str = (
            DEFAULT_ACTIVE_EVIDENCE_READ_REQUEST_DIRECTORY
        ),
    ) -> None:
        self._read_request_directory = Path(read_request_directory)
        self._active_read_request_directory = Path(active_read_request_directory)

    def _load_manifest(self) -> dict[str, Any]:
        path = self._read_request_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                f"OIA-032 current read-request manifest is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                f"OIA-032 current read-request manifest is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                "OIA-032 read-request manifest must be a JSON object."
            )

        manifest_hash = payload.pop("evidence_read_request_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                "OIA-032 read-request manifest hash verification failed."
            )
        payload["evidence_read_request_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-032",
            "engine_id": "OIA-032",
            "manifest_status": EVIDENCE_READ_REQUEST_MANIFEST_ISSUED,
            "evidence_read_request_policy_id": EVIDENCE_READ_REQUEST_POLICY_ID,
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
            "read_request_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                    f"OIA-032 read-request manifest invariant failed: {key}."
                )

        requests = payload.get("requests")
        if (
            not isinstance(requests, list)
            or not requests
            or payload.get("request_count") != len(requests)
        ):
            raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                "OIA-032 read requests are invalid."
            )

        for request in requests:
            if not isinstance(request, dict):
                raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                    "OIA-032 read request must be an object."
                )
            request_hash = request.pop("evidence_read_request_hash", None)
            if not _valid_hash(request_hash) or stable_hash(request) != request_hash:
                raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                    "OIA-032 read-request hash verification failed."
                )
            request["evidence_read_request_hash"] = request_hash
            if request.get("request_status") != EVIDENCE_READ_REQUEST_READY:
                raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                    "OIA-032 evidence read request is not ready."
                )
            operations = request.get("requested_read_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                    "OIA-032 evidence read request has no read operations."
                )
            if any(
                not isinstance(operation, str)
                or not operation.startswith("read_")
                for operation in operations
            ):
                raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                    "OIA-032 evidence request contains a non-read operation."
                )

        for name in (
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
                raise CertifiedResearchEvidenceReadRequestActivationInvariantError(
                    f"OIA-032 {name} is invalid."
                )
        return payload

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadRequestActivation:
        activated_at = _aware_utc(activated_at, "activated_at")
        source = self._load_manifest()

        active_requests = []
        for sequence, request in enumerate(source["requests"], start=1):
            body = {
                "activation_sequence": sequence,
                "request_sequence": request["request_sequence"],
                "task_sequence": request["task_sequence"],
                "work_item_id": request["work_item_id"],
                "worker_id": request["worker_id"],
                "dimension": request["dimension"],
                "key": request["key"],
                "tier": request["tier"],
                "priority_score": request["priority_score"],
                "research_objective": request["research_objective"],
                "evidence_scope_id": request["evidence_scope_id"],
                "authorized_read_operations": tuple(
                    request["requested_read_operations"]
                ),
                "prohibited_operations": tuple(
                    request["prohibited_operations"]
                ),
                "completion_requirements": tuple(
                    request["completion_requirements"]
                ),
                "active_request_status": EVIDENCE_READ_REQUEST_ACTIVE,
                "source_task_hash": request["source_task_hash"],
                "source_active_task_hash": request["source_active_task_hash"],
                "source_evidence_read_request_hash": request[
                    "evidence_read_request_hash"
                ],
            }
            active_requests.append(
                OracleCertifiedResearchActiveEvidenceReadRequest(
                    **body,
                    active_evidence_read_request_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at,
            "evidence_read_request_activation_id": _activation_id(
                source["evidence_read_request_manifest_hash"]
            ),
            "activation_status": EVIDENCE_READ_REQUEST_ACTIVATION_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_read_request_manifest_id": source[
                "evidence_read_request_manifest_id"
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
            "active_request_count": len(active_requests),
            "evidence_task_manifest_policy_id": source[
                "evidence_task_manifest_policy_id"
            ],
            "evidence_task_activation_policy_id": source[
                "evidence_task_activation_policy_id"
            ],
            "evidence_read_request_policy_id": source[
                "evidence_read_request_policy_id"
            ],
            "evidence_read_request_activation_policy_id": (
                EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID
            ),
            "requests": tuple(active_requests),
            "source_evidence_read_request_manifest_hash": source[
                "evidence_read_request_manifest_hash"
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
            "active_read_request_artifact_persistence_allowed": (
                ACTIVE_READ_REQUEST_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }
        result = OracleCertifiedResearchEvidenceReadRequestActivation(
            **body,
            evidence_read_request_activation_hash=stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(
                self._active_read_request_directory / "current.json",
                payload,
            )
            _atomic_write(
                self._active_read_request_directory
                / "activations"
                / f"{result.evidence_read_request_activation_id}.json",
                payload,
            )
            _atomic_write(
                self._active_read_request_directory
                / "workers"
                / result.worker_id
                / f"{result.evidence_read_request_activation_id}.json",
                payload,
            )
        return result
