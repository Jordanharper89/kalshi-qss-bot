from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA031 = ANALYTICS / "oracle_certified_research_evidence_collection_task_activation_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_request_manifest_builder.py"
TEST = ROOT / "test_oia_032_oracle_certified_research_evidence_read_request_manifest_builder.py"
INIT = ANALYTICS / "__init__.py"

PRODUCTION_SOURCE = r"""from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .oracle_certified_research_evidence_collection_task_activation_gate import (
    DEFAULT_ACTIVE_EVIDENCE_TASK_DIRECTORY,
    EVIDENCE_TASK_ACTIVATION_ISSUED,
    EVIDENCE_TASK_ACTIVATION_POLICY_ID,
    EVIDENCE_TASK_ACTIVE,
)

SCHEMA_VERSION = "OIA-032"
ENGINE_ID = "OIA-032"
EVIDENCE_READ_REQUEST_POLICY_ID = (
    "oracle.certified-research-evidence-read-request-manifest.v1"
)
EVIDENCE_READ_REQUEST_MANIFEST_ISSUED = "evidence_read_request_manifest_issued"
EVIDENCE_READ_REQUEST_READY = "evidence_read_request_ready"

DEFAULT_EVIDENCE_READ_REQUEST_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_evidence_read_requests"
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
READ_REQUEST_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadRequestManifestError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadRequestManifestInvariantError(
    CertifiedResearchEvidenceReadRequestManifestError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
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


def _manifest_id(source_activation_hash: str) -> str:
    seed = {
        "source_evidence_task_activation_hash": source_activation_hash,
        "policy": EVIDENCE_READ_REQUEST_POLICY_ID,
    }
    return f"oia032-evidence-read-request-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadRequest:
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
    requested_read_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    request_status: str
    source_task_hash: str
    source_active_task_hash: str
    evidence_read_request_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadRequestManifest:
    schema_version: str
    engine_id: str
    generated_at: datetime
    evidence_read_request_manifest_id: str
    manifest_status: str
    worker_id: str
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
    request_count: int
    evidence_task_manifest_policy_id: str
    evidence_task_activation_policy_id: str
    evidence_read_request_policy_id: str
    requests: tuple[OracleCertifiedResearchEvidenceReadRequest, ...]
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
    read_request_artifact_persistence_allowed: bool
    evidence_read_request_manifest_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadRequestManifestBuilder:
    def __init__(
        self,
        *,
        active_task_directory: Path | str = DEFAULT_ACTIVE_EVIDENCE_TASK_DIRECTORY,
        read_request_directory: Path | str = DEFAULT_EVIDENCE_READ_REQUEST_DIRECTORY,
    ) -> None:
        self._active_task_directory = Path(active_task_directory)
        self._read_request_directory = Path(read_request_directory)

    def _load_activation(self) -> dict[str, Any]:
        path = self._active_task_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                f"OIA-031 current task activation is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                f"OIA-031 current task activation is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                "OIA-031 task activation must be a JSON object."
            )

        activation_hash = payload.pop("evidence_task_activation_hash", None)
        if not _valid_hash(activation_hash) or stable_hash(payload) != activation_hash:
            raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                "OIA-031 task activation hash verification failed."
            )
        payload["evidence_task_activation_hash"] = activation_hash

        expected = {
            "schema_version": "OIA-031",
            "engine_id": "OIA-031",
            "task_activation_status": EVIDENCE_TASK_ACTIVATION_ISSUED,
            "evidence_task_activation_policy_id": EVIDENCE_TASK_ACTIVATION_POLICY_ID,
            "read_only_corpus": True,
            "evidence_collection_allowed": True,
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
            "active_task_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                    f"OIA-031 task activation invariant failed: {key}."
                )

        tasks = payload.get("tasks")
        if (
            not isinstance(tasks, list)
            or not tasks
            or payload.get("active_task_count") != len(tasks)
        ):
            raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                "OIA-031 active tasks are invalid."
            )

        for task in tasks:
            if not isinstance(task, dict):
                raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                    "OIA-031 active task must be an object."
                )
            task_hash = task.pop("active_task_hash", None)
            if not _valid_hash(task_hash) or stable_hash(task) != task_hash:
                raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                    "OIA-031 active task hash verification failed."
                )
            task["active_task_hash"] = task_hash
            if task.get("active_task_status") != EVIDENCE_TASK_ACTIVE:
                raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                    "OIA-031 evidence task is not active."
                )
            operations = task.get("authorized_evidence_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                    "OIA-031 active task has no authorized read operations."
                )
            if any(not str(operation).startswith("read_") for operation in operations):
                raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                    "OIA-031 active task contains a non-read operation."
                )

        for name in (
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
                raise CertifiedResearchEvidenceReadRequestManifestInvariantError(
                    f"OIA-031 {name} is invalid."
                )
        return payload

    def build(
        self,
        *,
        generated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadRequestManifest:
        generated_at = _aware_utc(generated_at, "generated_at")
        source = self._load_activation()

        requests = []
        for sequence, task in enumerate(source["tasks"], start=1):
            body = {
                "request_sequence": sequence,
                "task_sequence": task["task_sequence"],
                "work_item_id": task["work_item_id"],
                "worker_id": task["worker_id"],
                "dimension": task["dimension"],
                "key": task["key"],
                "tier": task["tier"],
                "priority_score": task["priority_score"],
                "research_objective": task["research_objective"],
                "evidence_scope_id": task["evidence_scope_id"],
                "requested_read_operations": tuple(
                    task["authorized_evidence_operations"]
                ),
                "prohibited_operations": tuple(task["prohibited_operations"]),
                "completion_requirements": tuple(
                    task["completion_requirements"]
                ),
                "request_status": EVIDENCE_READ_REQUEST_READY,
                "source_task_hash": task["source_task_hash"],
                "source_active_task_hash": task["active_task_hash"],
            }
            requests.append(
                OracleCertifiedResearchEvidenceReadRequest(
                    **body,
                    evidence_read_request_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "evidence_read_request_manifest_id": _manifest_id(
                source["evidence_task_activation_hash"]
            ),
            "manifest_status": EVIDENCE_READ_REQUEST_MANIFEST_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_task_activation_id": source[
                "evidence_task_activation_id"
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
            "request_count": len(requests),
            "evidence_task_manifest_policy_id": source[
                "evidence_task_manifest_policy_id"
            ],
            "evidence_task_activation_policy_id": source[
                "evidence_task_activation_policy_id"
            ],
            "evidence_read_request_policy_id": EVIDENCE_READ_REQUEST_POLICY_ID,
            "requests": tuple(requests),
            "source_evidence_task_activation_hash": source[
                "evidence_task_activation_hash"
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
            "read_request_artifact_persistence_allowed": (
                READ_REQUEST_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }
        result = OracleCertifiedResearchEvidenceReadRequestManifest(
            **body,
            evidence_read_request_manifest_hash=stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._read_request_directory / "current.json", payload)
            _atomic_write(
                self._read_request_directory
                / "manifests"
                / f"{result.evidence_read_request_manifest_id}.json",
                payload,
            )
            _atomic_write(
                self._read_request_directory
                / "workers"
                / result.worker_id
                / f"{result.evidence_read_request_manifest_id}.json",
                payload,
            )
        return result
"""

TEST_SOURCE = r"""from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_task_activation_gate import (
    EVIDENCE_TASK_ACTIVATION_ISSUED,
    EVIDENCE_TASK_ACTIVATION_POLICY_ID,
    EVIDENCE_TASK_ACTIVE,
    stable_hash as activation_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_request_manifest_builder import (
    EVIDENCE_READ_REQUEST_MANIFEST_ISSUED,
    EVIDENCE_READ_REQUEST_POLICY_ID,
    EVIDENCE_READ_REQUEST_READY,
    CertifiedResearchEvidenceReadRequestManifestInvariantError,
    OracleCertifiedResearchEvidenceReadRequestManifestBuilder,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 40)]


def write_activation(directory: Path) -> dict:
    task_body = {
        "activation_sequence": 1,
        "task_sequence": 1,
        "work_item_id": "work.test",
        "worker_id": "oracle-worker-test",
        "dimension": "market_microstructure",
        "key": "spread-regime",
        "tier": "qualified",
        "priority_score": "0.990000",
        "research_objective": "Collect bounded canonical evidence.",
        "evidence_scope_id": "scope.test",
        "authorized_evidence_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "active_task_status": EVIDENCE_TASK_ACTIVE,
        "source_certification_entry_hash": HASHES[1],
        "source_evidence_entry_hash": HASHES[2],
        "source_session_entry_hash": HASHES[3],
        "source_batch_entry_hash": HASHES[4],
        "source_active_entry_hash": HASHES[5],
        "source_task_hash": HASHES[6],
    }
    task = dict(task_body)
    task["active_task_hash"] = activation_stable_hash(task_body)

    body = {
        "schema_version": "OIA-031",
        "engine_id": "OIA-031",
        "activated_at": "2026-07-21T13:00:00+00:00",
        "evidence_task_activation_id": "oia031-task-activation-test",
        "task_activation_status": EVIDENCE_TASK_ACTIVATION_ISSUED,
        "worker_id": "oracle-worker-test",
        "source_evidence_task_manifest_id": "oia030-task-manifest-test",
        "source_evidence_batch_activation_id": "oia029-active-test",
        "source_evidence_batch_id": "oia028-batch-test",
        "source_evidence_session_id": "oia027-session-test",
        "source_evidence_manifest_id": "oia026-manifest-test",
        "source_certification_id": "oia025-cert-test",
        "source_readiness_id": "oia024-ready-test",
        "source_session_id": "oia023-session-test",
        "source_activation_id": "oia022-activation-test",
        "source_claim_id": "oia021-claim-test",
        "dispatch_manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "active_task_count": 1,
        "evidence_task_manifest_policy_id": "task-manifest-policy-test",
        "evidence_task_activation_policy_id": EVIDENCE_TASK_ACTIVATION_POLICY_ID,
        "tasks": [task],
        "source_evidence_task_manifest_hash": HASHES[7],
        "source_evidence_batch_activation_hash": HASHES[8],
        "source_evidence_batch_hash": HASHES[9],
        "source_evidence_session_hash": HASHES[10],
        "source_evidence_manifest_hash": HASHES[11],
        "source_certification_hash": HASHES[12],
        "source_readiness_hash": HASHES[13],
        "source_session_hash": HASHES[14],
        "source_activation_hash": HASHES[15],
        "source_claim_hash": HASHES[16],
        "source_dispatch_manifest_hash": HASHES[17],
        "source_batch_hash": HASHES[18],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
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
        "active_task_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_task_activation_hash"] = activation_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-032 TEST")
    print(" EVIDENCE READ REQUEST MANIFEST")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        active_directory = root / "active"
        request_directory = root / "requests"
        source = write_activation(active_directory)

        builder = OracleCertifiedResearchEvidenceReadRequestManifestBuilder(
            active_task_directory=active_directory,
            read_request_directory=request_directory,
        )
        fixed = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)
        first = builder.build(generated_at=fixed, persist=True)
        second = builder.build(generated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-032"
        assert first.engine_id == "OIA-032"
        assert first.manifest_status == EVIDENCE_READ_REQUEST_MANIFEST_ISSUED
        assert first.evidence_read_request_policy_id == EVIDENCE_READ_REQUEST_POLICY_ID
        assert (
            first.source_evidence_task_activation_hash
            == source["evidence_task_activation_hash"]
        )
        assert first.request_count == 1
        assert first.requests[0].request_status == EVIDENCE_READ_REQUEST_READY
        assert (
            first.requests[0].source_active_task_hash
            == source["tasks"][0]["active_task_hash"]
        )
        assert all(
            operation.startswith("read_")
            for operation in first.requests[0].requested_read_operations
        )
        assert first.read_only_corpus is True
        assert first.evidence_collection_allowed is True
        assert first.corpus_read_requests_allowed is True
        assert first.corpus_read_execution_allowed is False

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
        manifest_hash = body.pop("evidence_read_request_manifest_hash")
        assert manifest_hash == stable_hash(body)

        request_body = dict(first.requests[0].to_dict())
        request_hash = request_body.pop("evidence_read_request_hash")
        assert request_hash == stable_hash(request_body)

        assert (request_directory / "current.json").exists()
        assert list((request_directory / "manifests").glob("*.json"))
        assert list(
            (request_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (active_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["tasks"][0]["authorized_evidence_operations"].append(
            "create_order"
        )
        (active_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            builder.build(generated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadRequestManifestInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-031 task activation was accepted.")

    print("[PASS] Actual OIA-031 active-task contract consumed")
    print("[PASS] Read-request manifest and request hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-031 lineage preserved")
    print("[PASS] Only bounded read-prefixed corpus requests issued")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered active-task activation rejected")
    print("[PASS] Atomic read-request artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

INIT_BLOCK = r"""
from .oracle_certified_research_evidence_read_request_manifest_builder import (
    EVIDENCE_READ_REQUEST_MANIFEST_ISSUED,
    EVIDENCE_READ_REQUEST_POLICY_ID,
    EVIDENCE_READ_REQUEST_READY,
    OracleCertifiedResearchEvidenceReadRequest,
    OracleCertifiedResearchEvidenceReadRequestManifest,
    OracleCertifiedResearchEvidenceReadRequestManifestBuilder,
)

__all__ = [
    "EVIDENCE_READ_REQUEST_MANIFEST_ISSUED",
    "EVIDENCE_READ_REQUEST_POLICY_ID",
    "EVIDENCE_READ_REQUEST_READY",
    "OracleCertifiedResearchEvidenceReadRequest",
    "OracleCertifiedResearchEvidenceReadRequestManifest",
    "OracleCertifiedResearchEvidenceReadRequestManifestBuilder",
] + __all__
"""


def verify_oia031() -> None:
    if not OIA031.exists():
        raise RuntimeError(f"Actual OIA-031 production module missing: {OIA031}")
    source = OIA031.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION = "OIA-031"',
        'ENGINE_ID = "OIA-031"',
        "EVIDENCE_TASK_ACTIVATION_POLICY_ID",
        "EVIDENCE_TASK_ACTIVATION_ISSUED",
        "EVIDENCE_TASK_ACTIVE",
        "evidence_task_activation_hash",
        "active_task_hash",
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
        "authorized_evidence_operations",
        "prohibited_operations",
        "completion_requirements",
        "read_only_corpus",
        "evidence_collection_allowed",
        "research_execution_allowed",
        "analytic_conclusion_allowed",
        "forecast_creation_allowed",
        "qseries_handoff_allowed",
        "market_order_creation_allowed",
        "funds_movement_allowed",
        "portfolio_mutation_allowed",
    ]
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(f"Actual OIA-031 production contract mismatch: {missing}")


def write_full_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.rstrip() + "\n", encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    source = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "from .oracle_certified_research_evidence_read_request_manifest_builder "
        "import ("
    )
    if marker not in source:
        source = source.rstrip() + "\n" + INIT_BLOCK
        INIT.write_text(source.rstrip() + "\n", encoding="utf-8")
        print(f"[OK] PACKAGE UPDATED: {INIT}")
    else:
        print(f"[OK] PACKAGE ALREADY CURRENT: {INIT}")


def main() -> int:
    print("=" * 40)
    print(" OIA-032 INSTALLER")
    print(" EVIDENCE READ REQUEST MANIFEST")
    print(" READ-ONLY CORPUS REQUEST BOUNDARY")
    print("=" * 40)

    verify_oia031()
    print("[OK] Actual OIA-031 active evidence task contract verified")

    write_full_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_full_replacement(TEST, TEST_SOURCE)
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
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print("[OK] OIA-032 test executed automatically")
    print()
    print(
        "[DONE] OIA-032 certified research evidence read request "
        "manifest builder installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
