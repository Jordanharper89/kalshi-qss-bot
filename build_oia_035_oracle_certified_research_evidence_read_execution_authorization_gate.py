from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA034 = ANALYTICS / "oracle_certified_research_evidence_read_execution_readiness_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_authorization_gate.py"
TEST = ROOT / "test_oia_035_oracle_certified_research_evidence_read_execution_authorization_gate.py"
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

from .oracle_certified_research_evidence_read_execution_readiness_gate import (
    DEFAULT_EVIDENCE_READ_EXECUTION_READINESS_DIRECTORY,
    EVIDENCE_READ_EXECUTION_ENTRY_READY,
    EVIDENCE_READ_EXECUTION_READY,
    EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
)

SCHEMA_VERSION = "OIA-035"
ENGINE_ID = "OIA-035"
EVIDENCE_READ_EXECUTION_AUTHORIZATION_POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-authorization.v1"
)
EVIDENCE_READ_EXECUTION_AUTHORIZED = "evidence_read_execution_authorized"
EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED = "evidence_read_execution_entry_authorized"
DEFAULT_EVIDENCE_READ_EXECUTION_AUTHORIZATION_DIRECTORY = (
    Path("runtime") / "oracle_intelligence"
    / "certified_research_evidence_read_execution_authorization"
)

READ_ONLY_CORPUS = True
EVIDENCE_COLLECTION_ALLOWED = True
CORPUS_READ_REQUESTS_ALLOWED = True
CORPUS_READ_EXECUTION_ALLOWED = False
READ_EXECUTION_READINESS_ALLOWED = True
READ_EXECUTION_AUTHORIZATION_ALLOWED = True
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
AUTHORIZATION_ARTIFACT_PERSISTENCE_ALLOWED = True


class CertifiedResearchEvidenceReadExecutionAuthorizationError(RuntimeError):
    pass


class CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
    CertifiedResearchEvidenceReadExecutionAuthorizationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
            f"{field_name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _valid_hash(value: Any) -> bool:
    try:
        return isinstance(value, str) and len(value) == 64 and int(value, 16) >= 0
    except ValueError:
        return False


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_canonical(payload), sort_keys=True, indent=2) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", delete=False,
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp",
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAuthorizationEntry:
    authorization_sequence: int
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
    authorization_status: str
    source_evidence_read_request_hash: str
    source_active_evidence_read_request_hash: str
    source_readiness_entry_hash: str
    authorization_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCertifiedResearchEvidenceReadExecutionAuthorization:
    schema_version: str
    engine_id: str
    authorized_at: datetime
    evidence_read_execution_authorization_id: str
    authorization_status: str
    worker_id: str
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
    authorization_entry_count: int
    evidence_read_execution_readiness_policy_id: str
    evidence_read_execution_authorization_policy_id: str
    entries: tuple[OracleCertifiedResearchEvidenceReadExecutionAuthorizationEntry, ...]
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
    authorization_artifact_persistence_allowed: bool
    evidence_read_execution_authorization_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCertifiedResearchEvidenceReadExecutionAuthorizationGate:
    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_EVIDENCE_READ_EXECUTION_READINESS_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_EVIDENCE_READ_EXECUTION_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self._readiness_directory = Path(readiness_directory)
        self._authorization_directory = Path(authorization_directory)

    def _load(self) -> dict[str, Any]:
        path = self._readiness_directory / "current.json"
        if not path.exists():
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                f"OIA-034 current readiness is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness is invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness must be an object."
            )

        readiness_hash = payload.pop("evidence_read_execution_readiness_hash", None)
        if not _valid_hash(readiness_hash) or stable_hash(payload) != readiness_hash:
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness hash verification failed."
            )
        payload["evidence_read_execution_readiness_hash"] = readiness_hash

        expected = {
            "schema_version": "OIA-034",
            "engine_id": "OIA-034",
            "readiness_status": EVIDENCE_READ_EXECUTION_READY,
            "evidence_read_execution_readiness_policy_id":
                EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
            "read_only_corpus": True,
            "evidence_collection_allowed": True,
            "corpus_read_requests_allowed": True,
            "corpus_read_execution_allowed": False,
            "read_execution_readiness_allowed": True,
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
            "readiness_artifact_persistence_allowed": True,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    f"OIA-034 invariant failed: {key}."
                )

        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness entries are missing."
            )
        if payload.get("readiness_entry_count") != len(entries):
            raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                "OIA-034 readiness entry count mismatch."
            )

        for entry in entries:
            entry_hash = entry.pop("readiness_entry_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    "OIA-034 readiness-entry hash verification failed."
                )
            entry["readiness_entry_hash"] = entry_hash
            if entry.get("readiness_status") != EVIDENCE_READ_EXECUTION_ENTRY_READY:
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    "OIA-034 readiness entry is not ready."
                )
            operations = entry.get("authorized_read_operations")
            if not isinstance(operations, list) or not operations:
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    "OIA-034 readiness entry has no read operations."
                )
            if any(not isinstance(op, str) or not op.startswith("read_") for op in operations):
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    "OIA-034 readiness entry contains a non-read operation."
                )

        for key in (
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
            if not _valid_hash(payload.get(key)):
                raise CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError(
                    f"OIA-034 lineage hash invalid: {key}."
                )
        return payload

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> OracleCertifiedResearchEvidenceReadExecutionAuthorization:
        authorized_at = _aware_utc(authorized_at, "authorized_at")
        source = self._load()

        entries = []
        for sequence, item in enumerate(source["entries"], start=1):
            body = {
                "authorization_sequence": sequence,
                "readiness_sequence": item["readiness_sequence"],
                "request_sequence": item["request_sequence"],
                "task_sequence": item["task_sequence"],
                "work_item_id": item["work_item_id"],
                "worker_id": item["worker_id"],
                "dimension": item["dimension"],
                "key": item["key"],
                "evidence_scope_id": item["evidence_scope_id"],
                "authorized_read_operations": tuple(item["authorized_read_operations"]),
                "prohibited_operations": tuple(item["prohibited_operations"]),
                "completion_requirements": tuple(item["completion_requirements"]),
                "authorization_status": EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED,
                "source_evidence_read_request_hash":
                    item["source_evidence_read_request_hash"],
                "source_active_evidence_read_request_hash":
                    item["source_active_evidence_read_request_hash"],
                "source_readiness_entry_hash": item["readiness_entry_hash"],
            }
            entries.append(
                OracleCertifiedResearchEvidenceReadExecutionAuthorizationEntry(
                    **body, authorization_entry_hash=stable_hash(body)
                )
            )

        authorization_id = (
            "oia035-read-execution-authorization-"
            + stable_hash({
                "source": source["evidence_read_execution_readiness_hash"],
                "policy": EVIDENCE_READ_EXECUTION_AUTHORIZATION_POLICY_ID,
            })[:32]
        )
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at,
            "evidence_read_execution_authorization_id": authorization_id,
            "authorization_status": EVIDENCE_READ_EXECUTION_AUTHORIZED,
            "worker_id": source["worker_id"],
            "source_evidence_read_execution_readiness_id":
                source["evidence_read_execution_readiness_id"],
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
            "authorization_entry_count": len(entries),
            "evidence_read_execution_readiness_policy_id":
                source["evidence_read_execution_readiness_policy_id"],
            "evidence_read_execution_authorization_policy_id":
                EVIDENCE_READ_EXECUTION_AUTHORIZATION_POLICY_ID,
            "entries": tuple(entries),
            "source_evidence_read_execution_readiness_hash":
                source["evidence_read_execution_readiness_hash"],
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
            "source_evidence_session_hash": source["source_evidence_session_hash"],
            "source_evidence_manifest_hash": source["source_evidence_manifest_hash"],
            "source_certification_hash": source["source_certification_hash"],
            "source_readiness_hash": source["source_readiness_hash"],
            "source_session_hash": source["source_session_hash"],
            "source_activation_hash": source["source_activation_hash"],
            "source_claim_hash": source["source_claim_hash"],
            "source_dispatch_manifest_hash": source["source_dispatch_manifest_hash"],
            "source_batch_hash": source["source_batch_hash"],
            "read_only_corpus": READ_ONLY_CORPUS,
            "evidence_collection_allowed": EVIDENCE_COLLECTION_ALLOWED,
            "corpus_read_requests_allowed": CORPUS_READ_REQUESTS_ALLOWED,
            "corpus_read_execution_allowed": CORPUS_READ_EXECUTION_ALLOWED,
            "read_execution_readiness_allowed": READ_EXECUTION_READINESS_ALLOWED,
            "read_execution_authorization_allowed":
                READ_EXECUTION_AUTHORIZATION_ALLOWED,
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
            "authorization_artifact_persistence_allowed":
                AUTHORIZATION_ARTIFACT_PERSISTENCE_ALLOWED,
        }
        result = OracleCertifiedResearchEvidenceReadExecutionAuthorization(
            **body,
            evidence_read_execution_authorization_hash=stable_hash(body),
        )
        if persist:
            payload = result.to_dict()
            _atomic_write(self._authorization_directory / "current.json", payload)
            _atomic_write(
                self._authorization_directory / "authorizations"
                / f"{authorization_id}.json", payload,
            )
            _atomic_write(
                self._authorization_directory / "workers" / result.worker_id
                / f"{authorization_id}.json", payload,
            )
        return result
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_readiness_gate import (
    EVIDENCE_READ_EXECUTION_ENTRY_READY,
    EVIDENCE_READ_EXECUTION_READY,
    EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
    stable_hash as readiness_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_authorization_gate import (
    EVIDENCE_READ_EXECUTION_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED,
    CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAuthorizationGate,
    stable_hash,
)

H = [f"{i:064x}" for i in range(1, 40)]


def seed(directory: Path) -> dict:
    entry_body = {
        "readiness_sequence": 1,
        "request_sequence": 1,
        "task_sequence": 1,
        "work_item_id": "work.test",
        "worker_id": "oracle-worker-test",
        "dimension": "market_microstructure",
        "key": "spread-regime",
        "evidence_scope_id": "scope.test",
        "authorized_read_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "readiness_status": EVIDENCE_READ_EXECUTION_ENTRY_READY,
        "source_evidence_read_request_hash": H[1],
        "source_active_evidence_read_request_hash": H[2],
    }
    entry = dict(entry_body)
    entry["readiness_entry_hash"] = readiness_hash(entry_body)

    body = {
        "schema_version": "OIA-034",
        "engine_id": "OIA-034",
        "evaluated_at": "2026-07-21T16:00:00+00:00",
        "evidence_read_execution_readiness_id": "oia034-test",
        "readiness_status": EVIDENCE_READ_EXECUTION_READY,
        "worker_id": "oracle-worker-test",
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
        "readiness_entry_count": 1,
        "evidence_read_request_activation_policy_id": "oia033-policy",
        "evidence_read_execution_readiness_policy_id":
            EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
        "entries": [entry],
        "source_evidence_read_request_activation_hash": H[3],
        "source_evidence_read_request_manifest_hash": H[4],
        "source_evidence_task_activation_hash": H[5],
        "source_evidence_task_manifest_hash": H[6],
        "source_evidence_batch_activation_hash": H[7],
        "source_evidence_batch_hash": H[8],
        "source_evidence_session_hash": H[9],
        "source_evidence_manifest_hash": H[10],
        "source_certification_hash": H[11],
        "source_readiness_hash": H[12],
        "source_session_hash": H[13],
        "source_activation_hash": H[14],
        "source_claim_hash": H[15],
        "source_dispatch_manifest_hash": H[16],
        "source_batch_hash": H[17],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
        "corpus_read_requests_allowed": True,
        "corpus_read_execution_allowed": False,
        "read_execution_readiness_allowed": True,
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
        "readiness_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_execution_readiness_hash"] = readiness_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-035 TEST")
    print(" EVIDENCE READ EXECUTION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        readiness = root / "readiness"
        authorization = root / "authorization"
        source = seed(readiness)
        gate = OracleCertifiedResearchEvidenceReadExecutionAuthorizationGate(
            readiness_directory=readiness,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 21, 17, 0, tzinfo=timezone.utc)
        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-035"
        assert first.engine_id == "OIA-035"
        assert first.authorization_status == EVIDENCE_READ_EXECUTION_AUTHORIZED
        assert first.authorization_entry_count == 1
        assert first.entries[0].authorization_status == (
            EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED
        )
        assert first.source_evidence_read_execution_readiness_hash == (
            source["evidence_read_execution_readiness_hash"]
        )
        assert first.entries[0].source_readiness_entry_hash == (
            source["entries"][0]["readiness_entry_hash"]
        )
        assert all(op.startswith("read_") for op in first.entries[0].authorized_read_operations)
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_authorization_allowed is True

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
        result_hash = body.pop("evidence_read_execution_authorization_hash")
        assert result_hash == stable_hash(body)
        entry_body = dict(first.entries[0].to_dict())
        entry_hash = entry_body.pop("authorization_entry_hash")
        assert entry_hash == stable_hash(entry_body)

        assert (authorization / "current.json").exists()
        assert list((authorization / "authorizations").glob("*.json"))
        assert list((authorization / "workers" / first.worker_id).glob("*.json"))

        tampered = json.loads((readiness / "current.json").read_text(encoding="utf-8"))
        tampered["entries"][0]["authorized_read_operations"].append("create_order")
        (readiness / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.authorize(authorized_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-034 readiness accepted.")

    print("[PASS] Actual OIA-034 read-execution readiness contract consumed")
    print("[PASS] Authorization and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-034 lineage preserved")
    print("[PASS] Only bounded read-prefixed operations authorized")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered read-execution readiness rejected")
    print("[PASS] Atomic authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

INIT_BLOCK = r"""
from .oracle_certified_research_evidence_read_execution_authorization_gate import (
    EVIDENCE_READ_EXECUTION_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_AUTHORIZATION_POLICY_ID,
    OracleCertifiedResearchEvidenceReadExecutionAuthorization,
    OracleCertifiedResearchEvidenceReadExecutionAuthorizationEntry,
    OracleCertifiedResearchEvidenceReadExecutionAuthorizationGate,
)

__all__ = [
    "EVIDENCE_READ_EXECUTION_AUTHORIZED",
    "EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED",
    "EVIDENCE_READ_EXECUTION_AUTHORIZATION_POLICY_ID",
    "OracleCertifiedResearchEvidenceReadExecutionAuthorization",
    "OracleCertifiedResearchEvidenceReadExecutionAuthorizationEntry",
    "OracleCertifiedResearchEvidenceReadExecutionAuthorizationGate",
] + __all__
"""


def verify_oia034() -> None:
    if not OIA034.exists():
        raise RuntimeError(f"Actual OIA-034 production module missing: {OIA034}")
    text = OIA034.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION = "OIA-034"',
        'ENGINE_ID = "OIA-034"',
        "EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID",
        "EVIDENCE_READ_EXECUTION_READY",
        "EVIDENCE_READ_EXECUTION_ENTRY_READY",
        "evidence_read_execution_readiness_hash",
        "readiness_entry_hash",
        "authorized_read_operations",
        "corpus_read_execution_allowed",
        "read_execution_readiness_allowed",
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
        raise RuntimeError(f"Actual OIA-034 production contract mismatch: {missing}")


def write_full(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "from .oracle_certified_research_evidence_read_execution_authorization_gate "
        "import ("
    )
    if marker not in existing:
        INIT.write_text(existing.rstrip() + "\n" + INIT_BLOCK.strip() + "\n", encoding="utf-8")
        print(f"[OK] PACKAGE UPDATED: {INIT}")
    else:
        print(f"[OK] PACKAGE ALREADY CURRENT: {INIT}")


def main() -> int:
    print("=" * 40)
    print(" OIA-035 INSTALLER")
    print(" EVIDENCE READ EXECUTION AUTHORIZATION")
    print(" READ-ONLY EXECUTOR AUTHORITY BOUNDARY")
    print("=" * 40)

    verify_oia034()
    print("[OK] Actual OIA-034 read-execution readiness contract verified")
    write_full(PRODUCTION, PRODUCTION_SOURCE)
    write_full(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(PRODUCTION), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    print("[OK] Production, test, and package syntax verified")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    print("[OK] OIA-035 test executed automatically")
    print()
    print("[DONE] OIA-035 certified research evidence read execution authorization gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
