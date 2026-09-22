from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA036 = ANALYTICS / "oracle_certified_research_evidence_read_execution_invocation_manifest_builder.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_invocation_activation_gate.py"
TEST = ROOT / "test_oia_037_oracle_certified_research_evidence_read_execution_invocation_activation_gate.py"
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

from .oracle_certified_research_evidence_read_execution_invocation_manifest_builder import (
    DEFAULT_EVIDENCE_READ_EXECUTION_INVOCATION_DIRECTORY,
    EVIDENCE_READ_EXECUTION_INVOCATION_MANIFEST_ISSUED,
    EVIDENCE_READ_EXECUTION_INVOCATION_POLICY_ID,
    EVIDENCE_READ_EXECUTION_INVOCATION_READY,
)

SCHEMA_VERSION = "OIA-037"
ENGINE_ID = "OIA-037"
EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-invocation-activation.v1"
)
EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_ISSUED = (
    "evidence_read_execution_invocation_activation_issued"
)
EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVE = (
    "evidence_read_execution_invocation_active"
)

DEFAULT_ACTIVE_EVIDENCE_READ_EXECUTION_INVOCATION_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_active_evidence_read_execution_invocations"
)

READ_ONLY_CORPUS = True
EVIDENCE_COLLECTION_ALLOWED = True
CORPUS_READ_REQUESTS_ALLOWED = True
CORPUS_READ_EXECUTION_ALLOWED = False
READ_EXECUTION_READINESS_ALLOWED = True
READ_EXECUTION_AUTHORIZATION_ALLOWED = True
READ_EXECUTION_INVOCATION_ALLOWED = True
READ_EXECUTION_INVOCATION_ACTIVATION_ALLOWED = True
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
ACTIVATION_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionInvocationActivationError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
    CertifiedResearchEvidenceReadExecutionInvocationActivationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
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


def _activation_id(source_manifest_hash: str) -> str:
    seed = {
        "source_evidence_read_execution_invocation_manifest_hash":
            source_manifest_hash,
        "policy": EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID,
    }
    return f"oia037-read-invocation-activation-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchActiveEvidenceReadExecutionInvocation:
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
    active_read_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    activation_status: str
    source_evidence_read_request_hash: str
    source_active_evidence_read_request_hash: str
    source_readiness_entry_hash: str
    source_authorization_entry_hash: str
    source_invocation_hash: str
    active_invocation_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionInvocationActivation:
    schema_version: str
    engine_id: str
    activated_at: datetime
    evidence_read_execution_invocation_activation_id: str
    activation_status: str
    worker_id: str
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
    active_invocation_count: int
    evidence_read_execution_invocation_policy_id: str
    evidence_read_execution_invocation_activation_policy_id: str
    invocations: tuple[OracleCertifiedResearchActiveEvidenceReadExecutionInvocation, ...]
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
    activation_artifact_persistence_allowed: bool
    evidence_read_execution_invocation_activation_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionInvocationActivationGate:
    def __init__(
        self,
        *,
        invocation_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_INVOCATION_DIRECTORY
        ),
        active_invocation_directory: Path | str = (
            DEFAULT_ACTIVE_EVIDENCE_READ_EXECUTION_INVOCATION_DIRECTORY
        ),
    ) -> None:
        self._invocation_directory = Path(invocation_directory)
        self._active_invocation_directory = Path(active_invocation_directory)

    def _load_manifest(self) -> dict[str, Any]:
        path = self._invocation_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                f"OIA-036 current invocation manifest is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                "OIA-036 invocation manifest is invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                "OIA-036 invocation manifest must be a JSON object."
            )

        manifest_hash = payload.pop(
            "evidence_read_execution_invocation_manifest_hash", None
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                "OIA-036 invocation manifest hash verification failed."
            )
        payload["evidence_read_execution_invocation_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-036",
            "engine_id": "OIA-036",
            "invocation_manifest_status":
                EVIDENCE_READ_EXECUTION_INVOCATION_MANIFEST_ISSUED,
            "evidence_read_execution_invocation_policy_id":
                EVIDENCE_READ_EXECUTION_INVOCATION_POLICY_ID,
            "read_only_corpus": True,
            "evidence_collection_allowed": True,
            "corpus_read_requests_allowed": True,
            "corpus_read_execution_allowed": False,
            "read_execution_readiness_allowed": True,
            "read_execution_authorization_allowed": True,
            "read_execution_invocation_allowed": True,
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
            "invocation_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                    f"OIA-036 invocation invariant failed: {key}."
                )

        invocations = payload.get("invocations")
        if (
            not isinstance(invocations, list)
            or not invocations
            or payload.get("invocation_count") != len(invocations)
        ):
            raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                "OIA-036 invocation records are invalid."
            )

        for invocation in invocations:
            if not isinstance(invocation, dict):
                raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                    "OIA-036 invocation must be an object."
                )
            invocation_hash = invocation.pop("invocation_hash", None)
            if (
                not _valid_hash(invocation_hash)
                or stable_hash(invocation) != invocation_hash
            ):
                raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                    "OIA-036 invocation hash verification failed."
                )
            invocation["invocation_hash"] = invocation_hash
            if (
                invocation.get("invocation_status")
                != EVIDENCE_READ_EXECUTION_INVOCATION_READY
            ):
                raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                    "OIA-036 invocation is not ready."
                )
            operations = invocation.get("read_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                    "OIA-036 invocation has no read operations."
                )
            if any(
                not isinstance(operation, str)
                or not operation.startswith("read_")
                for operation in operations
            ):
                raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                    "OIA-036 invocation contains a non-read operation."
                )

        for name in (
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
                raise CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError(
                    f"OIA-036 lineage hash invalid: {name}."
                )
        return payload

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionInvocationActivation:
        activated_at = _aware_utc(activated_at, "activated_at")
        source = self._load_manifest()

        active_invocations = []
        for sequence, invocation in enumerate(source["invocations"], start=1):
            body = {
                "activation_sequence": sequence,
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
                "active_read_operations": tuple(invocation["read_operations"]),
                "prohibited_operations": tuple(invocation["prohibited_operations"]),
                "completion_requirements": tuple(
                    invocation["completion_requirements"]
                ),
                "activation_status":
                    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVE,
                "source_evidence_read_request_hash":
                    invocation["source_evidence_read_request_hash"],
                "source_active_evidence_read_request_hash":
                    invocation["source_active_evidence_read_request_hash"],
                "source_readiness_entry_hash":
                    invocation["source_readiness_entry_hash"],
                "source_authorization_entry_hash":
                    invocation["source_authorization_entry_hash"],
                "source_invocation_hash": invocation["invocation_hash"],
            }
            active_invocations.append(
                OracleCertifiedResearchActiveEvidenceReadExecutionInvocation(
                    **body,
                    active_invocation_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at,
            "evidence_read_execution_invocation_activation_id": _activation_id(
                source["evidence_read_execution_invocation_manifest_hash"]
            ),
            "activation_status":
                EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_read_execution_invocation_manifest_id":
                source["evidence_read_execution_invocation_manifest_id"],
            "source_evidence_read_execution_authorization_id":
                source["source_evidence_read_execution_authorization_id"],
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
            "active_invocation_count": len(active_invocations),
            "evidence_read_execution_invocation_policy_id":
                source["evidence_read_execution_invocation_policy_id"],
            "evidence_read_execution_invocation_activation_policy_id":
                EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID,
            "invocations": tuple(active_invocations),
            "source_evidence_read_execution_invocation_manifest_hash":
                source["evidence_read_execution_invocation_manifest_hash"],
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
            "read_execution_readiness_allowed": READ_EXECUTION_READINESS_ALLOWED,
            "read_execution_authorization_allowed":
                READ_EXECUTION_AUTHORIZATION_ALLOWED,
            "read_execution_invocation_allowed":
                READ_EXECUTION_INVOCATION_ALLOWED,
            "read_execution_invocation_activation_allowed":
                READ_EXECUTION_INVOCATION_ACTIVATION_ALLOWED,
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
            "activation_artifact_persistence_allowed":
                ACTIVATION_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = OracleCertifiedResearchEvidenceReadExecutionInvocationActivation(
            **body,
            evidence_read_execution_invocation_activation_hash=stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(
                self._active_invocation_directory / "current.json",
                payload,
            )
            _atomic_write(
                self._active_invocation_directory
                / "activations"
                / f"{result.evidence_read_execution_invocation_activation_id}.json",
                payload,
            )
            _atomic_write(
                self._active_invocation_directory
                / "workers"
                / result.worker_id
                / f"{result.evidence_read_execution_invocation_activation_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_invocation_manifest_builder import (
    EVIDENCE_READ_EXECUTION_INVOCATION_MANIFEST_ISSUED,
    EVIDENCE_READ_EXECUTION_INVOCATION_POLICY_ID,
    EVIDENCE_READ_EXECUTION_INVOCATION_READY,
    stable_hash as invocation_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_invocation_activation_gate import (
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVE,
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_ISSUED,
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID,
    CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionInvocationActivationGate,
    stable_hash,
)

H = [f"{index:064x}" for index in range(1, 60)]


def seed(directory: Path) -> dict:
    invocation_body = {
        "invocation_sequence": 1,
        "authorization_sequence": 1,
        "readiness_sequence": 1,
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
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "invocation_status": EVIDENCE_READ_EXECUTION_INVOCATION_READY,
        "source_evidence_read_request_hash": H[1],
        "source_active_evidence_read_request_hash": H[2],
        "source_readiness_entry_hash": H[3],
        "source_authorization_entry_hash": H[4],
    }
    invocation = dict(invocation_body)
    invocation["invocation_hash"] = invocation_hash(invocation_body)

    body = {
        "schema_version": "OIA-036",
        "engine_id": "OIA-036",
        "generated_at": "2026-07-21T18:00:00+00:00",
        "evidence_read_execution_invocation_manifest_id": "oia036-test",
        "invocation_manifest_status":
            EVIDENCE_READ_EXECUTION_INVOCATION_MANIFEST_ISSUED,
        "worker_id": "oracle-worker-test",
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
        "invocation_count": 1,
        "evidence_read_execution_authorization_policy_id": "oia035-policy",
        "evidence_read_execution_invocation_policy_id":
            EVIDENCE_READ_EXECUTION_INVOCATION_POLICY_ID,
        "invocations": [invocation],
        "source_evidence_read_execution_authorization_hash": H[5],
        "source_evidence_read_execution_readiness_hash": H[6],
        "source_evidence_read_request_activation_hash": H[7],
        "source_evidence_read_request_manifest_hash": H[8],
        "source_evidence_task_activation_hash": H[9],
        "source_evidence_task_manifest_hash": H[10],
        "source_evidence_batch_activation_hash": H[11],
        "source_evidence_batch_hash": H[12],
        "source_evidence_session_hash": H[13],
        "source_evidence_manifest_hash": H[14],
        "source_certification_hash": H[15],
        "source_readiness_hash": H[16],
        "source_session_hash": H[17],
        "source_activation_hash": H[18],
        "source_claim_hash": H[19],
        "source_dispatch_manifest_hash": H[20],
        "source_batch_hash": H[21],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
        "corpus_read_requests_allowed": True,
        "corpus_read_execution_allowed": False,
        "read_execution_readiness_allowed": True,
        "read_execution_authorization_allowed": True,
        "read_execution_invocation_allowed": True,
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
        "invocation_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_execution_invocation_manifest_hash"] = (
        invocation_hash(body)
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-037 TEST")
    print(" EVIDENCE READ INVOCATION ACTIVATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        invocation_directory = root / "invocation"
        active_directory = root / "active"
        source = seed(invocation_directory)

        gate = OracleCertifiedResearchEvidenceReadExecutionInvocationActivationGate(
            invocation_directory=invocation_directory,
            active_invocation_directory=active_directory,
        )
        fixed = datetime(2026, 7, 21, 19, 0, tzinfo=timezone.utc)
        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-037"
        assert first.engine_id == "OIA-037"
        assert first.activation_status == (
            EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_ISSUED
        )
        assert first.evidence_read_execution_invocation_activation_policy_id == (
            EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID
        )
        assert first.active_invocation_count == 1
        assert first.invocations[0].activation_status == (
            EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVE
        )
        assert first.source_evidence_read_execution_invocation_manifest_hash == (
            source["evidence_read_execution_invocation_manifest_hash"]
        )
        assert first.invocations[0].source_invocation_hash == (
            source["invocations"][0]["invocation_hash"]
        )
        assert all(
            operation.startswith("read_")
            for operation in first.invocations[0].active_read_operations
        )
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_invocation_activation_allowed is True

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
        activation_hash = body.pop(
            "evidence_read_execution_invocation_activation_hash"
        )
        assert activation_hash == stable_hash(body)

        invocation_body = dict(first.invocations[0].to_dict())
        active_hash = invocation_body.pop("active_invocation_hash")
        assert active_hash == stable_hash(invocation_body)

        assert (active_directory / "current.json").exists()
        assert list((active_directory / "activations").glob("*.json"))
        assert list(
            (active_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (invocation_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["invocations"][0]["read_operations"].append("create_order")
        (invocation_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.activate(activated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionInvocationActivationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-036 invocation manifest accepted.")

    print("[PASS] Actual OIA-036 invocation manifest contract consumed")
    print("[PASS] Activation and active-invocation hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-036 lineage preserved")
    print("[PASS] Only bounded read-prefixed invocations activated")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered invocation manifest rejected")
    print("[PASS] Atomic active-invocation artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

INIT_BLOCK = r"""
from .oracle_certified_research_evidence_read_execution_invocation_activation_gate import (
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVE,
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_ISSUED,
    EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID,
    OracleCertifiedResearchActiveEvidenceReadExecutionInvocation,
    OracleCertifiedResearchEvidenceReadExecutionInvocationActivation,
    OracleCertifiedResearchEvidenceReadExecutionInvocationActivationGate,
)

__all__ = [
    "EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVE",
    "EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_ISSUED",
    "EVIDENCE_READ_EXECUTION_INVOCATION_ACTIVATION_POLICY_ID",
    "OracleCertifiedResearchActiveEvidenceReadExecutionInvocation",
    "OracleCertifiedResearchEvidenceReadExecutionInvocationActivation",
    "OracleCertifiedResearchEvidenceReadExecutionInvocationActivationGate",
] + __all__
"""


def verify_oia036() -> None:
    if not OIA036.exists():
        raise RuntimeError(f"Actual OIA-036 production module missing: {OIA036}")
    text = OIA036.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION = "OIA-036"',
        'ENGINE_ID = "OIA-036"',
        "EVIDENCE_READ_EXECUTION_INVOCATION_POLICY_ID",
        "EVIDENCE_READ_EXECUTION_INVOCATION_MANIFEST_ISSUED",
        "EVIDENCE_READ_EXECUTION_INVOCATION_READY",
        "evidence_read_execution_invocation_manifest_hash",
        "invocation_hash",
        "read_operations",
        "corpus_read_execution_allowed",
        "read_execution_invocation_allowed",
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
        raise RuntimeError(f"Actual OIA-036 production contract mismatch: {missing}")


def write_full(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "from .oracle_certified_research_evidence_read_execution_invocation_activation_gate "
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
    print(" OIA-037 INSTALLER")
    print(" EVIDENCE READ INVOCATION ACTIVATION")
    print(" READ-ONLY INVOCATION AUTHORITY BOUNDARY")
    print("=" * 40)

    verify_oia036()
    print("[OK] Actual OIA-036 invocation manifest contract verified")

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

    print("[OK] OIA-037 test executed automatically")
    print()
    print(
        "[DONE] OIA-037 certified research evidence read execution "
        "invocation activation gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
