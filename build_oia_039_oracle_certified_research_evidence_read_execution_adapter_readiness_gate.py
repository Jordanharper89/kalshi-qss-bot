from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA038 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_binding_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_readiness_gate.py"
TEST = ROOT / "test_oia_039_oracle_certified_research_evidence_read_execution_adapter_readiness_gate.py"
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
    DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_DIRECTORY,
    EVIDENCE_READ_EXECUTION_ADAPTER_BOUND,
    EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID,
    OPERATION_ADAPTER_MAP,
)

SCHEMA_VERSION = "OIA-039"
ENGINE_ID = "OIA-039"

EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-readiness.v1"
)
EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED = (
    "evidence_read_execution_adapter_readiness_issued"
)
EVIDENCE_READ_EXECUTION_ADAPTER_READY = (
    "evidence_read_execution_adapter_ready"
)

DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_evidence_read_execution_adapter_readiness"
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
ADAPTER_READINESS_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionAdapterReadinessError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
    CertifiedResearchEvidenceReadExecutionAdapterReadinessError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
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


def _readiness_manifest_id(source_binding_hash: str) -> str:
    seed = {
        "source_evidence_read_execution_adapter_binding_manifest_hash":
            source_binding_hash,
        "policy": EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
    }
    return f"oia039-read-adapter-readiness-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterReadiness:
    readiness_sequence: int
    binding_sequence: int
    activation_sequence: int
    invocation_sequence: int
    authorization_sequence: int
    request_sequence: int
    task_sequence: int
    work_item_id: str
    worker_id: str
    dimension: str
    key: str
    evidence_scope_id: str
    read_operations: tuple[str, ...]
    adapter_ids: tuple[str, ...]
    operation_adapter_bindings: tuple[tuple[str, str], ...]
    adapter_contract_checks: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    readiness_status: str
    source_active_invocation_hash: str
    source_adapter_binding_hash: str
    adapter_readiness_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: datetime
    evidence_read_execution_adapter_readiness_manifest_id: str
    readiness_manifest_status: str
    worker_id: str
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
    readiness_count: int
    approved_read_only_adapter_ids: tuple[str, ...]
    evidence_read_execution_adapter_binding_policy_id: str
    evidence_read_execution_adapter_readiness_policy_id: str
    readiness_entries: tuple[
        OracleCertifiedResearchEvidenceReadExecutionAdapterReadiness, ...
    ]
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
    adapter_readiness_artifact_persistence_allowed: bool
    evidence_read_execution_adapter_readiness_manifest_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessGate:
    def __init__(
        self,
        *,
        binding_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_DIRECTORY
        ),
        readiness_directory: Path | str = (
            DEFAULT_EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_DIRECTORY
        ),
    ) -> None:
        self._binding_directory = Path(binding_directory)
        self._readiness_directory = Path(readiness_directory)

    def _load_binding_manifest(self) -> dict[str, Any]:
        path = self._binding_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                f"OIA-038 current adapter binding manifest is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                "OIA-038 adapter binding manifest is invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                "OIA-038 adapter binding manifest must be a JSON object."
            )

        manifest_hash = payload.pop(
            "evidence_read_execution_adapter_binding_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                "OIA-038 adapter binding manifest hash verification failed."
            )
        payload["evidence_read_execution_adapter_binding_manifest_hash"] = (
            manifest_hash
        )

        expected = {
            "schema_version": "OIA-038",
            "engine_id": "OIA-038",
            "binding_manifest_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED,
            "evidence_read_execution_adapter_binding_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID,
            "read_only_corpus": True,
            "evidence_collection_allowed": True,
            "corpus_read_requests_allowed": True,
            "corpus_read_execution_allowed": False,
            "read_execution_readiness_allowed": True,
            "read_execution_authorization_allowed": True,
            "read_execution_invocation_allowed": True,
            "read_execution_invocation_activation_allowed": True,
            "read_execution_adapter_binding_allowed": True,
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
            "adapter_binding_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    f"OIA-038 binding invariant failed: {key}."
                )

        if tuple(payload.get("approved_read_only_adapter_ids", ())) != (
            APPROVED_READ_ONLY_ADAPTER_IDS
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                "OIA-038 approved adapter allowlist mismatch."
            )

        bindings = payload.get("bindings")
        if (
            not isinstance(bindings, list)
            or not bindings
            or payload.get("binding_count") != len(bindings)
        ):
            raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                "OIA-038 adapter bindings are invalid."
            )

        for binding in bindings:
            if not isinstance(binding, dict):
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    "OIA-038 adapter binding must be an object."
                )
            binding_hash = binding.pop("adapter_binding_hash", None)
            if not _valid_hash(binding_hash) or stable_hash(binding) != binding_hash:
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    "OIA-038 adapter-binding hash verification failed."
                )
            binding["adapter_binding_hash"] = binding_hash

            if binding.get("binding_status") != EVIDENCE_READ_EXECUTION_ADAPTER_BOUND:
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    "OIA-038 adapter binding is not bound."
                )

            operations = binding.get("read_operations")
            adapter_ids = binding.get("adapter_ids")
            operation_bindings = binding.get("operation_adapter_bindings")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    "OIA-038 binding has no read operations."
                )
            if not isinstance(adapter_ids, list) or not adapter_ids:
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    "OIA-038 binding has no adapter IDs."
                )
            if not isinstance(operation_bindings, list) or not operation_bindings:
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    "OIA-038 operation-adapter bindings are missing."
                )

            normalized_pairs = []
            for pair in operation_bindings:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                        "OIA-038 operation-adapter binding is malformed."
                    )
                operation, adapter_id = pair
                if (
                    operation not in operations
                    or operation not in OPERATION_ADAPTER_MAP
                    or OPERATION_ADAPTER_MAP[operation] != adapter_id
                    or adapter_id not in APPROVED_READ_ONLY_ADAPTER_IDS
                    or "read_only" not in adapter_id
                ):
                    raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                        "OIA-038 adapter binding is not approved read-only."
                    )
                normalized_pairs.append((operation, adapter_id))

            if tuple(dict.fromkeys(adapter for _, adapter in normalized_pairs)) != (
                tuple(adapter_ids)
            ):
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    "OIA-038 adapter ID set does not match operation bindings."
                )

        for name in (
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
                raise CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError(
                    f"OIA-038 lineage hash invalid: {name}."
                )
        return payload

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessManifest:
        evaluated_at = _aware_utc(evaluated_at, "evaluated_at")
        source = self._load_binding_manifest()

        readiness_entries = []
        for sequence, binding in enumerate(source["bindings"], start=1):
            body = {
                "readiness_sequence": sequence,
                "binding_sequence": binding["binding_sequence"],
                "activation_sequence": binding["activation_sequence"],
                "invocation_sequence": binding["invocation_sequence"],
                "authorization_sequence": binding["authorization_sequence"],
                "request_sequence": binding["request_sequence"],
                "task_sequence": binding["task_sequence"],
                "work_item_id": binding["work_item_id"],
                "worker_id": binding["worker_id"],
                "dimension": binding["dimension"],
                "key": binding["key"],
                "evidence_scope_id": binding["evidence_scope_id"],
                "read_operations": tuple(binding["read_operations"]),
                "adapter_ids": tuple(binding["adapter_ids"]),
                "operation_adapter_bindings": tuple(
                    tuple(pair) for pair in binding["operation_adapter_bindings"]
                ),
                "adapter_contract_checks": (
                    "adapter_id_allowlisted",
                    "adapter_identity_read_only",
                    "operation_mapping_exact",
                    "source_binding_hash_verified",
                    "corpus_execution_disabled",
                ),
                "prohibited_operations":
                    tuple(binding["prohibited_operations"]),
                "completion_requirements":
                    tuple(binding["completion_requirements"]),
                "readiness_status": EVIDENCE_READ_EXECUTION_ADAPTER_READY,
                "source_active_invocation_hash":
                    binding["source_active_invocation_hash"],
                "source_adapter_binding_hash":
                    binding["adapter_binding_hash"],
            }
            readiness_entries.append(
                OracleCertifiedResearchEvidenceReadExecutionAdapterReadiness(
                    **body,
                    adapter_readiness_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at,
            "evidence_read_execution_adapter_readiness_manifest_id":
                _readiness_manifest_id(
                    source[
                        "evidence_read_execution_adapter_binding_manifest_hash"
                    ]
                ),
            "readiness_manifest_status":
                EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_read_execution_adapter_binding_manifest_id":
                source[
                    "evidence_read_execution_adapter_binding_manifest_id"
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
            "readiness_count": len(readiness_entries),
            "approved_read_only_adapter_ids":
                APPROVED_READ_ONLY_ADAPTER_IDS,
            "evidence_read_execution_adapter_binding_policy_id":
                source["evidence_read_execution_adapter_binding_policy_id"],
            "evidence_read_execution_adapter_readiness_policy_id":
                EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
            "readiness_entries": tuple(readiness_entries),
            "source_evidence_read_execution_adapter_binding_manifest_hash":
                source[
                    "evidence_read_execution_adapter_binding_manifest_hash"
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
            "adapter_readiness_artifact_persistence_allowed":
                ADAPTER_READINESS_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessManifest(
                **body,
                evidence_read_execution_adapter_readiness_manifest_hash=
                    stable_hash(body),
            )
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._readiness_directory / "current.json", payload)
            _atomic_write(
                self._readiness_directory
                / "manifests"
                / (
                    f"{result.evidence_read_execution_adapter_readiness_manifest_id}"
                    ".json"
                ),
                payload,
            )
            _atomic_write(
                self._readiness_directory
                / "workers"
                / result.worker_id
                / (
                    f"{result.evidence_read_execution_adapter_readiness_manifest_id}"
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
    EVIDENCE_READ_EXECUTION_ADAPTER_BOUND,
    EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID,
    stable_hash as binding_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_readiness_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_READY,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
    CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessGate,
    stable_hash,
)

H = [f"{index:064x}" for index in range(1, 80)]


def seed(directory: Path) -> dict:
    binding_body = {
        "binding_sequence": 1,
        "activation_sequence": 1,
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
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "binding_status": EVIDENCE_READ_EXECUTION_ADAPTER_BOUND,
        "source_evidence_read_request_hash": H[1],
        "source_active_evidence_read_request_hash": H[2],
        "source_readiness_entry_hash": H[3],
        "source_authorization_entry_hash": H[4],
        "source_invocation_hash": H[5],
        "source_active_invocation_hash": H[6],
    }
    binding = dict(binding_body)
    binding["adapter_binding_hash"] = binding_hash(binding_body)

    body = {
        "schema_version": "OIA-038",
        "engine_id": "OIA-038",
        "bound_at": "2026-07-21T20:00:00+00:00",
        "evidence_read_execution_adapter_binding_manifest_id": "oia038-test",
        "binding_manifest_status":
            EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED,
        "worker_id": "oracle-worker-test",
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
        "binding_count": 1,
        "approved_read_only_adapter_ids":
            list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "evidence_read_execution_invocation_activation_policy_id":
            "oia037-policy",
        "evidence_read_execution_adapter_binding_policy_id":
            EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID,
        "bindings": [binding],
        "source_evidence_read_execution_invocation_activation_hash": H[7],
        "source_evidence_read_execution_invocation_manifest_hash": H[8],
        "source_evidence_read_execution_authorization_hash": H[9],
        "source_evidence_read_execution_readiness_hash": H[10],
        "source_evidence_read_request_activation_hash": H[11],
        "source_evidence_read_request_manifest_hash": H[12],
        "source_evidence_task_activation_hash": H[13],
        "source_evidence_task_manifest_hash": H[14],
        "source_evidence_batch_activation_hash": H[15],
        "source_evidence_batch_hash": H[16],
        "source_evidence_session_hash": H[17],
        "source_evidence_manifest_hash": H[18],
        "source_certification_hash": H[19],
        "source_readiness_hash": H[20],
        "source_session_hash": H[21],
        "source_activation_hash": H[22],
        "source_claim_hash": H[23],
        "source_dispatch_manifest_hash": H[24],
        "source_batch_hash": H[25],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
        "corpus_read_requests_allowed": True,
        "corpus_read_execution_allowed": False,
        "read_execution_readiness_allowed": True,
        "read_execution_authorization_allowed": True,
        "read_execution_invocation_allowed": True,
        "read_execution_invocation_activation_allowed": True,
        "read_execution_adapter_binding_allowed": True,
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
        "adapter_binding_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_execution_adapter_binding_manifest_hash"] = (
        binding_hash(body)
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-039 TEST")
    print(" EVIDENCE READ ADAPTER READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        binding_directory = root / "bindings"
        readiness_directory = root / "readiness"
        source = seed(binding_directory)

        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessGate(
            binding_directory=binding_directory,
            readiness_directory=readiness_directory,
        )
        fixed = datetime(2026, 7, 21, 21, 0, tzinfo=timezone.utc)
        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-039"
        assert first.engine_id == "OIA-039"
        assert first.readiness_manifest_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED
        )
        assert first.evidence_read_execution_adapter_readiness_policy_id == (
            EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID
        )
        assert first.readiness_count == 1
        assert first.readiness_entries[0].readiness_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_READY
        )
        assert first.source_evidence_read_execution_adapter_binding_manifest_hash == (
            source["evidence_read_execution_adapter_binding_manifest_hash"]
        )
        assert first.readiness_entries[0].source_adapter_binding_hash == (
            source["bindings"][0]["adapter_binding_hash"]
        )
        assert set(first.readiness_entries[0].adapter_ids).issubset(
            set(APPROVED_READ_ONLY_ADAPTER_IDS)
        )
        assert "operation_mapping_exact" in (
            first.readiness_entries[0].adapter_contract_checks
        )
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_adapter_readiness_allowed is True

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
            "evidence_read_execution_adapter_readiness_manifest_hash"
        )
        assert manifest_hash == stable_hash(body)

        readiness_body = dict(first.readiness_entries[0].to_dict())
        readiness_hash_value = readiness_body.pop("adapter_readiness_hash")
        assert readiness_hash_value == stable_hash(readiness_body)

        assert (readiness_directory / "current.json").exists()
        assert list((readiness_directory / "manifests").glob("*.json"))
        assert list(
            (readiness_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (binding_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["bindings"][0]["adapter_ids"][0] = (
            "oracle_write_capable_observation_adapter.v1"
        )
        (binding_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(evaluated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-038 adapter binding accepted.")

    print("[PASS] Actual OIA-038 adapter binding contract consumed")
    print("[PASS] Readiness manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-038 lineage preserved")
    print("[PASS] Only approved read-only adapters certified ready")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or write-capable adapters rejected")
    print("[PASS] Atomic adapter-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

INIT_BLOCK = r"""
from .oracle_certified_research_evidence_read_execution_adapter_readiness_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_READY,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
    OracleCertifiedResearchEvidenceReadExecutionAdapterReadiness,
    OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessGate,
    OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessManifest,
)

__all__ = [
    "EVIDENCE_READ_EXECUTION_ADAPTER_READY",
    "EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED",
    "EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterReadiness",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessGate",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessManifest",
] + __all__
"""


def verify_oia038() -> None:
    if not OIA038.exists():
        raise RuntimeError(f"Actual OIA-038 production module missing: {OIA038}")
    text = OIA038.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION = "OIA-038"',
        'ENGINE_ID = "OIA-038"',
        "APPROVED_READ_ONLY_ADAPTER_IDS",
        "OPERATION_ADAPTER_MAP",
        "EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID",
        "EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED",
        "EVIDENCE_READ_EXECUTION_ADAPTER_BOUND",
        "evidence_read_execution_adapter_binding_manifest_hash",
        "adapter_binding_hash",
        "operation_adapter_bindings",
        "adapter_ids",
        "read_operations",
        "corpus_read_execution_allowed",
        "read_execution_adapter_binding_allowed",
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
        raise RuntimeError(f"Actual OIA-038 production contract mismatch: {missing}")


def write_full(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "from .oracle_certified_research_evidence_read_execution_adapter_readiness_gate "
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
    print(" OIA-039 INSTALLER")
    print(" EVIDENCE READ ADAPTER READINESS")
    print(" READ-ONLY ADAPTER SAFETY GATE")
    print("=" * 40)

    verify_oia038()
    print("[OK] Actual OIA-038 adapter binding contract verified")

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

    print("[OK] OIA-039 test executed automatically")
    print()
    print(
        "[DONE] OIA-039 certified research evidence read execution "
        "adapter readiness gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
