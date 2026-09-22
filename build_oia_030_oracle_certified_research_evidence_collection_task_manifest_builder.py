from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA029 = ANALYTICS / "oracle_certified_research_evidence_collection_batch_activation_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_collection_task_manifest_builder.py"
TEST = ROOT / "test_oia_030_oracle_certified_research_evidence_collection_task_manifest_builder.py"
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

from .oracle_certified_research_evidence_collection_batch_activation_gate import (
    DEFAULT_ACTIVE_EVIDENCE_BATCH_DIRECTORY,
    EVIDENCE_BATCH_ACTIVE,
    EVIDENCE_BATCH_ENTRY_ACTIVE,
    EVIDENCE_BATCH_ACTIVATION_POLICY_ID,
)

SCHEMA_VERSION = "OIA-030"
ENGINE_ID = "OIA-030"
EVIDENCE_TASK_MANIFEST_POLICY_ID = "oracle.certified-research-evidence-collection-task-manifest.v1"
EVIDENCE_TASK_MANIFEST_ISSUED = "evidence_collection_task_manifest_issued"
EVIDENCE_TASK_READY = "evidence_collection_task_ready"
DEFAULT_EVIDENCE_TASK_MANIFEST_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "certified_research_evidence_collection_task_manifests"
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
TASK_MANIFEST_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceCollectionTaskManifestError(RuntimeError):
    pass


class CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
    CertifiedResearchEvidenceCollectionTaskManifestError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
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
        "source_evidence_batch_activation_hash": source_activation_hash,
        "policy": EVIDENCE_TASK_MANIFEST_POLICY_ID,
    }
    return f"oia030-evidence-task-manifest-{stable_hash(seed)[:32]}"


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionTask:
    task_sequence: int
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
    task_status: str
    source_certification_entry_hash: str
    source_evidence_entry_hash: str
    source_session_entry_hash: str
    source_batch_entry_hash: str
    source_active_entry_hash: str
    task_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceCollectionTaskManifest:
    schema_version: str
    engine_id: str
    generated_at: datetime
    evidence_task_manifest_id: str
    task_manifest_status: str
    worker_id: str
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
    task_count: int
    evidence_session_policy_id: str
    evidence_batch_policy_id: str
    evidence_batch_activation_policy_id: str
    evidence_task_manifest_policy_id: str
    tasks: tuple[OracleCertifiedResearchEvidenceCollectionTask, ...]
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
    task_manifest_artifact_persistence_allowed: bool
    evidence_task_manifest_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceCollectionTaskManifestBuilder:
    def __init__(
        self,
        *,
        active_batch_directory: Path | str = DEFAULT_ACTIVE_EVIDENCE_BATCH_DIRECTORY,
        task_manifest_directory: Path | str = DEFAULT_EVIDENCE_TASK_MANIFEST_DIRECTORY,
    ) -> None:
        self._active_batch_directory = Path(active_batch_directory)
        self._task_manifest_directory = Path(task_manifest_directory)

    def _load_active_batch(self) -> dict[str, Any]:
        path = self._active_batch_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                f"OIA-029 current active evidence batch is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                f"OIA-029 current active evidence batch is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                "OIA-029 active evidence batch must be a JSON object."
            )

        activation_hash = payload.pop("evidence_batch_activation_hash", None)
        if not _valid_hash(activation_hash) or stable_hash(payload) != activation_hash:
            raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                "OIA-029 active evidence batch hash verification failed."
            )
        payload["evidence_batch_activation_hash"] = activation_hash

        expected = {
            "schema_version": "OIA-029",
            "engine_id": "OIA-029",
            "active_batch_status": EVIDENCE_BATCH_ACTIVE,
            "evidence_batch_activation_policy_id": EVIDENCE_BATCH_ACTIVATION_POLICY_ID,
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
            "active_batch_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                    f"OIA-029 active evidence batch invariant failed: {key}."
                )

        entries = payload.get("entries")
        if (
            not isinstance(entries, list)
            or not entries
            or payload.get("active_entry_count") != len(entries)
        ):
            raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                "OIA-029 active evidence batch entries are invalid."
            )

        for entry in entries:
            if not isinstance(entry, dict):
                raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                    "OIA-029 active evidence entry must be an object."
                )
            entry_hash = entry.pop("active_entry_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                    "OIA-029 active evidence entry hash verification failed."
                )
            entry["active_entry_hash"] = entry_hash
            if entry.get("active_entry_status") != EVIDENCE_BATCH_ENTRY_ACTIVE:
                raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                    "OIA-029 evidence entry is not active."
                )
            operations = entry.get("authorized_evidence_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                    "OIA-029 evidence entry has no authorized read operations."
                )

        hash_fields = (
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
        )
        for name in hash_fields:
            if not _valid_hash(payload.get(name)):
                raise CertifiedResearchEvidenceCollectionTaskManifestInvariantError(
                    f"OIA-029 {name} is invalid."
                )
        return payload

    def build(
        self,
        *,
        generated_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceCollectionTaskManifest:
        generated_at = _aware_utc(generated_at, "generated_at")
        source = self._load_active_batch()

        tasks = []
        for sequence, source_entry in enumerate(source["entries"], start=1):
            body = {
                "task_sequence": sequence,
                "activation_sequence": source_entry["activation_sequence"],
                "batch_sequence": source_entry["batch_sequence"],
                "session_sequence": source_entry["session_sequence"],
                "evidence_sequence": source_entry["evidence_sequence"],
                "work_item_id": source_entry["work_item_id"],
                "worker_id": source_entry["worker_id"],
                "dimension": source_entry["dimension"],
                "key": source_entry["key"],
                "tier": source_entry["tier"],
                "priority_score": source_entry["priority_score"],
                "research_objective": source_entry["research_objective"],
                "evidence_scope_id": source_entry["evidence_scope_id"],
                "authorized_evidence_operations": tuple(
                    source_entry["authorized_evidence_operations"]
                ),
                "prohibited_operations": tuple(
                    source_entry["prohibited_operations"]
                ),
                "completion_requirements": tuple(
                    source_entry["completion_requirements"]
                ),
                "task_status": EVIDENCE_TASK_READY,
                "source_certification_entry_hash": source_entry[
                    "source_certification_entry_hash"
                ],
                "source_evidence_entry_hash": source_entry[
                    "source_evidence_entry_hash"
                ],
                "source_session_entry_hash": source_entry[
                    "source_session_entry_hash"
                ],
                "source_batch_entry_hash": source_entry[
                    "source_batch_entry_hash"
                ],
                "source_active_entry_hash": source_entry["active_entry_hash"],
            }
            tasks.append(
                OracleCertifiedResearchEvidenceCollectionTask(
                    **body,
                    task_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "evidence_task_manifest_id": _manifest_id(
                source["evidence_batch_activation_hash"]
            ),
            "task_manifest_status": EVIDENCE_TASK_MANIFEST_ISSUED,
            "worker_id": source["worker_id"],
            "source_evidence_batch_activation_id": source[
                "evidence_batch_activation_id"
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
            "task_count": len(tasks),
            "evidence_session_policy_id": source["evidence_session_policy_id"],
            "evidence_batch_policy_id": source["evidence_batch_policy_id"],
            "evidence_batch_activation_policy_id": source[
                "evidence_batch_activation_policy_id"
            ],
            "evidence_task_manifest_policy_id": EVIDENCE_TASK_MANIFEST_POLICY_ID,
            "tasks": tuple(tasks),
            "source_evidence_batch_activation_hash": source[
                "evidence_batch_activation_hash"
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
            "task_manifest_artifact_persistence_allowed": (
                TASK_MANIFEST_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }
        result = OracleCertifiedResearchEvidenceCollectionTaskManifest(
            **body,
            evidence_task_manifest_hash=stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._task_manifest_directory / "current.json", payload)
            _atomic_write(
                self._task_manifest_directory
                / "manifests"
                / f"{result.evidence_task_manifest_id}.json",
                payload,
            )
            _atomic_write(
                self._task_manifest_directory
                / "workers"
                / result.worker_id
                / f"{result.evidence_task_manifest_id}.json",
                payload,
            )
        return result
"""

TEST_SOURCE = r"""from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_batch_activation_gate import (
    EVIDENCE_BATCH_ACTIVE,
    EVIDENCE_BATCH_ENTRY_ACTIVE,
    EVIDENCE_BATCH_ACTIVATION_POLICY_ID,
    stable_hash as activation_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_task_manifest_builder import (
    EVIDENCE_TASK_MANIFEST_ISSUED,
    EVIDENCE_TASK_MANIFEST_POLICY_ID,
    EVIDENCE_TASK_READY,
    CertifiedResearchEvidenceCollectionTaskManifestInvariantError,
    OracleCertifiedResearchEvidenceCollectionTaskManifestBuilder,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 40)]


def write_active_batch(directory: Path) -> dict:
    entry_body = {
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
        "prohibited_operations": [
            "create_signal",
            "create_order",
        ],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "active_entry_status": EVIDENCE_BATCH_ENTRY_ACTIVE,
        "source_certification_entry_hash": HASHES[1],
        "source_evidence_entry_hash": HASHES[2],
        "source_session_entry_hash": HASHES[3],
        "source_batch_entry_hash": HASHES[4],
    }
    entry = dict(entry_body)
    entry["active_entry_hash"] = activation_stable_hash(entry_body)

    body = {
        "schema_version": "OIA-029",
        "engine_id": "OIA-029",
        "activated_at": "2026-07-21T11:00:00+00:00",
        "evidence_batch_activation_id": "oia029-active-batch-test",
        "active_batch_status": EVIDENCE_BATCH_ACTIVE,
        "batch_number": 1,
        "worker_id": "oracle-worker-test",
        "source_evidence_batch_id": "oia028-batch-test",
        "source_evidence_session_id": "oia027-session-test",
        "source_evidence_manifest_id": "oia026-manifest-test",
        "source_certification_id": "oia025-certification-test",
        "source_readiness_id": "oia024-readiness-test",
        "source_session_id": "oia023-session-test",
        "source_activation_id": "oia022-activation-test",
        "source_claim_id": "oia021-claim-test",
        "dispatch_manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "active_entry_count": 1,
        "evidence_session_policy_id": "session-policy-test",
        "evidence_batch_policy_id": "batch-policy-test",
        "evidence_batch_activation_policy_id": (
            EVIDENCE_BATCH_ACTIVATION_POLICY_ID
        ),
        "entries": [entry],
        "source_evidence_batch_hash": HASHES[5],
        "source_evidence_session_hash": HASHES[6],
        "source_evidence_manifest_hash": HASHES[7],
        "source_certification_hash": HASHES[8],
        "source_readiness_hash": HASHES[9],
        "source_session_hash": HASHES[10],
        "source_activation_hash": HASHES[11],
        "source_claim_hash": HASHES[12],
        "source_dispatch_manifest_hash": HASHES[13],
        "source_batch_hash": HASHES[14],
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
        "active_batch_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_batch_activation_hash"] = activation_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-030 TEST")
    print(" EVIDENCE COLLECTION TASK MANIFEST")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        active_directory = root / "active"
        task_directory = root / "tasks"
        source = write_active_batch(active_directory)

        builder = OracleCertifiedResearchEvidenceCollectionTaskManifestBuilder(
            active_batch_directory=active_directory,
            task_manifest_directory=task_directory,
        )
        fixed = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
        first = builder.build(generated_at=fixed, persist=True)
        second = builder.build(generated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-030"
        assert first.engine_id == "OIA-030"
        assert first.task_manifest_status == EVIDENCE_TASK_MANIFEST_ISSUED
        assert (
            first.evidence_task_manifest_policy_id
            == EVIDENCE_TASK_MANIFEST_POLICY_ID
        )
        assert (
            first.source_evidence_batch_activation_hash
            == source["evidence_batch_activation_hash"]
        )
        assert first.task_count == 1
        assert first.tasks[0].task_status == EVIDENCE_TASK_READY
        assert (
            first.tasks[0].source_active_entry_hash
            == source["entries"][0]["active_entry_hash"]
        )
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
        manifest_hash = body.pop("evidence_task_manifest_hash")
        assert manifest_hash == stable_hash(body)

        task_body = dict(first.tasks[0].to_dict())
        task_hash = task_body.pop("task_hash")
        assert task_hash == stable_hash(task_body)

        assert (task_directory / "current.json").exists()
        assert list((task_directory / "manifests").glob("*.json"))
        assert list(
            (task_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (active_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["entries"][0]["priority_score"] = "0.000000"
        (active_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            builder.build(generated_at=fixed, persist=False)
        except CertifiedResearchEvidenceCollectionTaskManifestInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-029 active batch was accepted.")

    print("[PASS] Actual OIA-029 active evidence batch contract consumed")
    print("[PASS] Evidence task manifest and task hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-029 lineage preserved")
    print("[PASS] Bounded read-only evidence collection tasks issued")
    print("[PASS] Analytic conclusions and forecasts remained disabled")
    print("[PASS] Tampered active evidence batch rejected")
    print("[PASS] Atomic task manifest artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

INIT_BLOCK = r"""
from .oracle_certified_research_evidence_collection_task_manifest_builder import (
    EVIDENCE_TASK_MANIFEST_ISSUED,
    EVIDENCE_TASK_MANIFEST_POLICY_ID,
    EVIDENCE_TASK_READY,
    OracleCertifiedResearchEvidenceCollectionTask,
    OracleCertifiedResearchEvidenceCollectionTaskManifest,
    OracleCertifiedResearchEvidenceCollectionTaskManifestBuilder,
)

__all__ = [
    "EVIDENCE_TASK_MANIFEST_ISSUED",
    "EVIDENCE_TASK_MANIFEST_POLICY_ID",
    "EVIDENCE_TASK_READY",
    "OracleCertifiedResearchEvidenceCollectionTask",
    "OracleCertifiedResearchEvidenceCollectionTaskManifest",
    "OracleCertifiedResearchEvidenceCollectionTaskManifestBuilder",
] + __all__
"""


def verify_oia029() -> None:
    if not OIA029.exists():
        raise RuntimeError(f"Actual OIA-029 production module missing: {OIA029}")
    source = OIA029.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION = "OIA-029"',
        'ENGINE_ID = "OIA-029"',
        "EVIDENCE_BATCH_ACTIVATION_POLICY_ID",
        "EVIDENCE_BATCH_ACTIVE",
        "EVIDENCE_BATCH_ENTRY_ACTIVE",
        "evidence_batch_activation_hash",
        "active_entry_hash",
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
        raise RuntimeError(f"Actual OIA-029 production contract mismatch: {missing}")


def write_full_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.rstrip() + "\n", encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    source = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "from .oracle_certified_research_evidence_collection_task_manifest_builder "
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
    print(" OIA-030 INSTALLER")
    print(" EVIDENCE COLLECTION TASK MANIFEST")
    print(" READ-ONLY TASK ISSUANCE BOUNDARY")
    print("=" * 40)

    verify_oia029()
    print("[OK] Actual OIA-029 active evidence batch contract verified")

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

    print("[OK] OIA-030 test executed automatically")
    print()
    print(
        "[DONE] OIA-030 certified research evidence collection "
        "task manifest builder installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
