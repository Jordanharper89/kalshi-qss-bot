from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA030 = ANALYTICS / "oracle_certified_research_evidence_collection_task_manifest_builder.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_collection_task_activation_gate.py"
TEST = ROOT / "test_oia_031_oracle_certified_research_evidence_collection_task_activation_gate.py"
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

from .oracle_certified_research_evidence_collection_task_manifest_builder import (
    DEFAULT_EVIDENCE_TASK_MANIFEST_DIRECTORY,
    EVIDENCE_TASK_MANIFEST_ISSUED,
    EVIDENCE_TASK_MANIFEST_POLICY_ID,
    EVIDENCE_TASK_READY,
)

SCHEMA_VERSION = "OIA-031"
ENGINE_ID = "OIA-031"
EVIDENCE_TASK_ACTIVATION_POLICY_ID = (
    "oracle.certified-research-evidence-collection-task-activation.v1"
)
EVIDENCE_TASK_ACTIVATION_ISSUED = "evidence_collection_task_activation_issued"
EVIDENCE_TASK_ACTIVE = "evidence_collection_task_active"

DEFAULT_ACTIVE_EVIDENCE_TASK_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_active_evidence_tasks"
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
ACTIVE_TASK_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceCollectionTaskActivationError(RuntimeError):
    pass


class CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
    CertifiedResearchEvidenceCollectionTaskActivationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
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
        "source_evidence_task_manifest_hash": source_manifest_hash,
        "policy": EVIDENCE_TASK_ACTIVATION_POLICY_ID,
    }
    return f"oia031-evidence-task-activation-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchActiveEvidenceCollectionTask:
    activation_sequence: int
    task_sequence: int
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
    active_task_status: str
    source_certification_entry_hash: str
    source_evidence_entry_hash: str
    source_session_entry_hash: str
    source_batch_entry_hash: str
    source_active_entry_hash: str
    source_task_hash: str
    active_task_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionTaskActivation:
    schema_version: str
    engine_id: str
    activated_at: datetime
    evidence_task_activation_id: str
    task_activation_status: str
    worker_id: str
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
    active_task_count: int
    evidence_task_manifest_policy_id: str
    evidence_task_activation_policy_id: str
    tasks: tuple[OracleCertifiedResearchActiveEvidenceCollectionTask, ...]
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
    active_task_artifact_persistence_allowed: bool
    evidence_task_activation_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceCollectionTaskActivationGate:
    def __init__(
        self,
        *,
        task_manifest_directory: Path | str = DEFAULT_EVIDENCE_TASK_MANIFEST_DIRECTORY,
        active_task_directory: Path | str = DEFAULT_ACTIVE_EVIDENCE_TASK_DIRECTORY,
    ) -> None:
        self._task_manifest_directory = Path(task_manifest_directory)
        self._active_task_directory = Path(active_task_directory)

    def _load_task_manifest(self) -> dict[str, Any]:
        path = self._task_manifest_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                f"OIA-030 current task manifest is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                f"OIA-030 current task manifest is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                "OIA-030 task manifest must be a JSON object."
            )

        manifest_hash = payload.pop("evidence_task_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                "OIA-030 task manifest hash verification failed."
            )
        payload["evidence_task_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-030",
            "engine_id": "OIA-030",
            "task_manifest_status": EVIDENCE_TASK_MANIFEST_ISSUED,
            "evidence_task_manifest_policy_id": EVIDENCE_TASK_MANIFEST_POLICY_ID,
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
            "task_manifest_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                    f"OIA-030 task manifest invariant failed: {key}."
                )

        tasks = payload.get("tasks")
        if (
            not isinstance(tasks, list)
            or not tasks
            or payload.get("task_count") != len(tasks)
        ):
            raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                "OIA-030 task manifest tasks are invalid."
            )

        for task in tasks:
            if not isinstance(task, dict):
                raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                    "OIA-030 evidence task must be an object."
                )
            task_hash = task.pop("task_hash", None)
            if not _valid_hash(task_hash) or stable_hash(task) != task_hash:
                raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                    "OIA-030 evidence task hash verification failed."
                )
            task["task_hash"] = task_hash
            if task.get("task_status") != EVIDENCE_TASK_READY:
                raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                    "OIA-030 evidence task is not ready."
                )
            operations = task.get("authorized_evidence_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                    "OIA-030 evidence task has no authorized read operations."
                )

        for name in (
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
                raise CertifiedResearchEvidenceCollectionTaskActivationInvariantError(
                    f"OIA-030 {name} is invalid."
                )
        return payload

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceCollectionTaskActivation:
        activated_at = _aware_utc(activated_at, "activated_at")
        source = self._load_task_manifest()

        active_tasks = []
        for sequence, task in enumerate(source["tasks"], start=1):
            body = {
                "activation_sequence": sequence,
                "task_sequence": task["task_sequence"],
                "work_item_id": task["work_item_id"],
                "worker_id": task["worker_id"],
                "dimension": task["dimension"],
                "key": task["key"],
                "tier": task["tier"],
                "priority_score": task["priority_score"],
                "research_objective": task["research_objective"],
                "evidence_scope_id": task["evidence_scope_id"],
                "authorized_evidence_operations": tuple(
                    task["authorized_evidence_operations"]
                ),
                "prohibited_operations": tuple(task["prohibited_operations"]),
                "completion_requirements": tuple(
                    task["completion_requirements"]
                ),
                "active_task_status": EVIDENCE_TASK_ACTIVE,
                "source_certification_entry_hash": task[
                    "source_certification_entry_hash"
                ],
                "source_evidence_entry_hash": task["source_evidence_entry_hash"],
                "source_session_entry_hash": task["source_session_entry_hash"],
                "source_batch_entry_hash": task["source_batch_entry_hash"],
                "source_active_entry_hash": task["source_active_entry_hash"],
                "source_task_hash": task["task_hash"],
            }
            active_tasks.append(
                OracleCertifiedResearchActiveEvidenceCollectionTask(
                    **body,
                    active_task_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at,
            "evidence_task_activation_id": _activation_id(
                source["evidence_task_manifest_hash"]
            ),
            "task_activation_status": EVIDENCE_TASK_ACTIVATION_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_task_manifest_id": source[
                "evidence_task_manifest_id"
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
            "active_task_count": len(active_tasks),
            "evidence_task_manifest_policy_id": source[
                "evidence_task_manifest_policy_id"
            ],
            "evidence_task_activation_policy_id": (
                EVIDENCE_TASK_ACTIVATION_POLICY_ID
            ),
            "tasks": tuple(active_tasks),
            "source_evidence_task_manifest_hash": source[
                "evidence_task_manifest_hash"
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
            "active_task_artifact_persistence_allowed": (
                ACTIVE_TASK_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }
        result = OracleCertifiedResearchEvidenceCollectionTaskActivation(
            **body,
            evidence_task_activation_hash=stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._active_task_directory / "current.json", payload)
            _atomic_write(
                self._active_task_directory
                / "activations"
                / f"{result.evidence_task_activation_id}.json",
                payload,
            )
            _atomic_write(
                self._active_task_directory
                / "workers"
                / result.worker_id
                / f"{result.evidence_task_activation_id}.json",
                payload,
            )
        return result
"""

TEST_SOURCE = r"""from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_task_manifest_builder import (
    EVIDENCE_TASK_MANIFEST_ISSUED,
    EVIDENCE_TASK_MANIFEST_POLICY_ID,
    EVIDENCE_TASK_READY,
    stable_hash as manifest_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_task_activation_gate import (
    EVIDENCE_TASK_ACTIVATION_ISSUED,
    EVIDENCE_TASK_ACTIVATION_POLICY_ID,
    EVIDENCE_TASK_ACTIVE,
    CertifiedResearchEvidenceCollectionTaskActivationInvariantError,
    OracleCertifiedResearchEvidenceCollectionTaskActivationGate,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 40)]


def write_task_manifest(directory: Path) -> dict:
    task_body = {
        "task_sequence": 1,
        "activation_sequence": 1,
        "batch_sequence": 1,
        "session_sequence": 1,
        "evidence_sequence": 1,
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
        "task_status": EVIDENCE_TASK_READY,
        "source_certification_entry_hash": HASHES[1],
        "source_evidence_entry_hash": HASHES[2],
        "source_session_entry_hash": HASHES[3],
        "source_batch_entry_hash": HASHES[4],
        "source_active_entry_hash": HASHES[5],
    }
    task = dict(task_body)
    task["task_hash"] = manifest_stable_hash(task_body)

    body = {
        "schema_version": "OIA-030",
        "engine_id": "OIA-030",
        "generated_at": "2026-07-21T12:00:00+00:00",
        "evidence_task_manifest_id": "oia030-task-manifest-test",
        "task_manifest_status": EVIDENCE_TASK_MANIFEST_ISSUED,
        "worker_id": "oracle-worker-test",
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
        "task_count": 1,
        "evidence_session_policy_id": "session-policy-test",
        "evidence_batch_policy_id": "batch-policy-test",
        "evidence_batch_activation_policy_id": "activation-policy-test",
        "evidence_task_manifest_policy_id": EVIDENCE_TASK_MANIFEST_POLICY_ID,
        "tasks": [task],
        "source_evidence_batch_activation_hash": HASHES[6],
        "source_evidence_batch_hash": HASHES[7],
        "source_evidence_session_hash": HASHES[8],
        "source_evidence_manifest_hash": HASHES[9],
        "source_certification_hash": HASHES[10],
        "source_readiness_hash": HASHES[11],
        "source_session_hash": HASHES[12],
        "source_activation_hash": HASHES[13],
        "source_claim_hash": HASHES[14],
        "source_dispatch_manifest_hash": HASHES[15],
        "source_batch_hash": HASHES[16],
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
        "task_manifest_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_task_manifest_hash"] = manifest_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-031 TEST")
    print(" EVIDENCE COLLECTION TASK ACTIVATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        manifest_directory = root / "manifests"
        active_directory = root / "active"
        source = write_task_manifest(manifest_directory)

        gate = OracleCertifiedResearchEvidenceCollectionTaskActivationGate(
            task_manifest_directory=manifest_directory,
            active_task_directory=active_directory,
        )
        fixed = datetime(2026, 7, 21, 13, 0, tzinfo=timezone.utc)
        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-031"
        assert first.engine_id == "OIA-031"
        assert first.task_activation_status == EVIDENCE_TASK_ACTIVATION_ISSUED
        assert (
            first.evidence_task_activation_policy_id
            == EVIDENCE_TASK_ACTIVATION_POLICY_ID
        )
        assert (
            first.source_evidence_task_manifest_hash
            == source["evidence_task_manifest_hash"]
        )
        assert first.active_task_count == 1
        assert first.tasks[0].active_task_status == EVIDENCE_TASK_ACTIVE
        assert first.tasks[0].source_task_hash == source["tasks"][0]["task_hash"]
        assert first.read_only_corpus is True
        assert first.evidence_collection_allowed is True

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
        activation_hash = body.pop("evidence_task_activation_hash")
        assert activation_hash == stable_hash(body)

        task_body = dict(first.tasks[0].to_dict())
        active_task_hash = task_body.pop("active_task_hash")
        assert active_task_hash == stable_hash(task_body)

        assert (active_directory / "current.json").exists()
        assert list((active_directory / "activations").glob("*.json"))
        assert list(
            (active_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (manifest_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["tasks"][0]["priority_score"] = "0.000000"
        (manifest_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.activate(activated_at=fixed, persist=False)
        except CertifiedResearchEvidenceCollectionTaskActivationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-030 task manifest was accepted.")

    print("[PASS] Actual OIA-030 evidence task manifest contract consumed")
    print("[PASS] Task activation and active-task hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-030 lineage preserved")
    print("[PASS] Bounded read-only evidence collection tasks activated")
    print("[PASS] Analytic conclusions and forecasts remained disabled")
    print("[PASS] Tampered evidence task manifest rejected")
    print("[PASS] Atomic active-task artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

INIT_BLOCK = r"""
from .oracle_certified_research_evidence_collection_task_activation_gate import (
    EVIDENCE_TASK_ACTIVATION_ISSUED,
    EVIDENCE_TASK_ACTIVATION_POLICY_ID,
    EVIDENCE_TASK_ACTIVE,
    OracleCertifiedResearchActiveEvidenceCollectionTask,
    OracleCertifiedResearchEvidenceCollectionTaskActivation,
    OracleCertifiedResearchEvidenceCollectionTaskActivationGate,
)

__all__ = [
    "EVIDENCE_TASK_ACTIVATION_ISSUED",
    "EVIDENCE_TASK_ACTIVATION_POLICY_ID",
    "EVIDENCE_TASK_ACTIVE",
    "OracleCertifiedResearchActiveEvidenceCollectionTask",
    "OracleCertifiedResearchEvidenceCollectionTaskActivation",
    "OracleCertifiedResearchEvidenceCollectionTaskActivationGate",
] + __all__
"""


def verify_oia030() -> None:
    if not OIA030.exists():
        raise RuntimeError(f"Actual OIA-030 production module missing: {OIA030}")
    source = OIA030.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION = "OIA-030"',
        'ENGINE_ID = "OIA-030"',
        "EVIDENCE_TASK_MANIFEST_POLICY_ID",
        "EVIDENCE_TASK_MANIFEST_ISSUED",
        "EVIDENCE_TASK_READY",
        "evidence_task_manifest_hash",
        "task_hash",
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
        raise RuntimeError(f"Actual OIA-030 production contract mismatch: {missing}")


def write_full_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.rstrip() + "\n", encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    source = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "from .oracle_certified_research_evidence_collection_task_activation_gate "
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
    print(" OIA-031 INSTALLER")
    print(" EVIDENCE COLLECTION TASK ACTIVATION")
    print(" READ-ONLY TASK AUTHORITY BOUNDARY")
    print("=" * 40)

    verify_oia030()
    print("[OK] Actual OIA-030 evidence task manifest contract verified")

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

    print("[OK] OIA-031 test executed automatically")
    print()
    print(
        "[DONE] OIA-031 certified research evidence collection "
        "task activation gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
