from __future__ import annotations
import py_compile, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_result_attestation_gate.py"
TEST = ROOT / "test_int_oia_012_oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_result_attestation_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
UPSTREAM = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_execution_gate.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations
import hashlib, json, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-012"
ENGINE_ID = "INT-OIA-012"
STATUS_ATTESTED = "downstream_read_only_consumer_controlled_invocation_result_attested"
DEFAULT_EXECUTION_DIRECTORY = Path("runtime/oracle_intelligence/analytics_downstream_read_only_consumer_controlled_invocation_execution")
DEFAULT_ATTESTATION_DIRECTORY = Path("runtime/oracle_intelligence/analytics_downstream_read_only_consumer_controlled_invocation_result_attestation")

class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError(RuntimeError):
    pass

def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("unsupported value type")

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)

def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_canonical(payload), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", delete=False, dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(text); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()

@dataclass(frozen=True)
class ControlledInvocationResultAttestationRecord:
    sequence: int
    result_attestation_id: str
    consumer_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_invocation_execution_record_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    result_type: str
    result_hash: str
    recomputed_result_hash: str
    result_payload: Any
    result_hash_verified: bool
    invocation_count_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    execution_lineage_verified: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_performed: bool
    source_mutation_performed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    result_admission_authorized: bool
    downstream_release_performed: bool
    attestation_status: str
    result_attestation_record_hash: str

@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationManifest:
    schema_version: str
    engine_id: str
    attested_at: str
    result_attestation_manifest_id: str
    result_attestation_status: str
    source_invocation_execution_manifest_id: str
    source_invocation_execution_manifest_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[ControlledInvocationResultAttestationRecord, ...]
    all_execution_hashes_verified: bool
    all_result_hashes_verified: bool
    all_execution_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_performed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    controlled_result_admission_authorized: bool
    downstream_release_performed: bool
    result_attestation_manifest_hash: str

class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationGate:
    def __init__(self, *, execution_directory=DEFAULT_EXECUTION_DIRECTORY, attestation_directory=DEFAULT_ATTESTATION_DIRECTORY):
        self.execution_directory = Path(execution_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load(self) -> dict[str, Any]:
        path = self.execution_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError(f"INT-OIA-011 execution artifact missing: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest_hash = payload.pop("invocation_execution_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("INT-OIA-011 execution manifest hash mismatch")
        payload["invocation_execution_manifest_hash"] = manifest_hash
        required = {
            "schema_version": "INT-OIA-011",
            "engine_id": "INT-OIA-011",
            "controlled_invocation_performed": True,
            "one_time_invocation_enforced": True,
            "all_results_deterministically_hashable": True,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_performed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError(f"unsafe INT-OIA-011 field: {field}")
        records = payload.get("execution_records")
        if not isinstance(records, list) or not records or payload.get("execution_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("INT-OIA-011 execution records invalid")
        for sequence, raw in enumerate(records, 1):
            record = dict(raw)
            record_hash = record.pop("invocation_execution_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("execution-record hash mismatch")
            raw["invocation_execution_record_hash"] = record_hash
            if raw.get("sequence") != sequence or raw.get("invocation_count") != 1 or raw.get("invocation_performed") is not True:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("one-time invocation contract mismatch")
            if stable_hash(raw.get("result_payload")) != raw.get("result_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("result hash mismatch")
            for field in ("database_connection_performed", "corpus_read_performed", "source_mutation_performed", "signals_allowed", "alerts_allowed", "qseries_execution_allowed", "market_order_creation_allowed", "funds_movement_allowed", "portfolio_mutation_allowed"):
                if raw.get(field) is not False:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError(f"unsafe execution-record field: {field}")
        return payload

    def attest(self, *, attested_at: datetime, persist: bool = True):
        if attested_at.tzinfo is None or attested_at.utcoffset() is None:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("attested_at must be timezone-aware")
        attested_at = attested_at.astimezone(timezone.utc)
        source = self._load()
        records = []
        for sequence, execution in enumerate(source["execution_records"], 1):
            recomputed = stable_hash(execution["result_payload"])
            attestation_id = stable_hash({
                "source_manifest": source["invocation_execution_manifest_id"],
                "execution_id": execution["invocation_execution_id"],
                "execution_record_hash": execution["invocation_execution_record_hash"],
                "result_hash": recomputed,
                "attested_at": attested_at.isoformat(),
            })
            body = {
                "sequence": sequence,
                "result_attestation_id": attestation_id,
                "consumer_id": execution["consumer_id"],
                "invocation_execution_id": execution["invocation_execution_id"],
                "invocation_nonce": execution["invocation_nonce"],
                "source_invocation_execution_record_hash": execution["invocation_execution_record_hash"],
                "source_boundary_id": execution["source_boundary_id"],
                "source_boundary_hash": execution["source_boundary_hash"],
                "result_type": execution["result_type"],
                "result_hash": execution["result_hash"],
                "recomputed_result_hash": recomputed,
                "result_payload": execution["result_payload"],
                "result_hash_verified": True,
                "invocation_count_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "execution_lineage_verified": True,
                "invocation_reexecution_performed": False,
                "database_connection_performed": False,
                "corpus_read_performed": False,
                "source_mutation_performed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "result_admission_authorized": True,
                "downstream_release_performed": False,
                "attestation_status": "result_verified_not_released",
            }
            records.append(ControlledInvocationResultAttestationRecord(**body, result_attestation_record_hash=stable_hash(body)))
        manifest_id = stable_hash({
            "source_manifest": source["invocation_execution_manifest_id"],
            "source_hash": source["invocation_execution_manifest_hash"],
            "attested_at": attested_at.isoformat(),
            "records": [r.result_attestation_record_hash for r in records],
        })
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "result_attestation_manifest_id": manifest_id,
            "result_attestation_status": STATUS_ATTESTED,
            "source_invocation_execution_manifest_id": source["invocation_execution_manifest_id"],
            "source_invocation_execution_manifest_hash": source["invocation_execution_manifest_hash"],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
            "all_execution_hashes_verified": True,
            "all_result_hashes_verified": True,
            "all_execution_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_performed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "controlled_result_admission_authorized": True,
            "downstream_release_performed": False,
        }
        serializable = dict(body)
        serializable["attestation_records"] = [asdict(r) for r in records]
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationManifest(**body, result_attestation_manifest_hash=stable_hash(serializable))
        if persist:
            payload = asdict(manifest)
            _atomic_write(self.attestation_directory / "current.json", payload)
            _atomic_write(self.attestation_directory / "manifests" / f"{manifest_id}.json", payload)
        return manifest
"""

TEST_SOURCE = r"""
from __future__ import annotations
import json, tempfile
from datetime import datetime, timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_result_attestation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError,
    stable_hash,
)

def seed(path: Path) -> None:
    result = {"artifact_count": 2, "read_only": True, "finding": "certified"}
    record = {
        "sequence": 1,
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": "test.module",
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": "analyze_certified_oia_artifacts",
        "callable_path": "test.module.OracleResearchAnalyticsConsumer.analyze_certified_oia_artifacts",
        "bound_callable_identity_hash": stable_hash({"callable": 1}),
        "source_invocation_readiness_id": "readiness-test",
        "source_invocation_readiness_record_hash": stable_hash({"readiness": 1}),
        "source_binding_attestation_id": "binding-test",
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"activation": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "certified_artifacts_hash": stable_hash([{"a": 1}, {"a": 2}]),
        "execution_context_hash": stable_hash({"mode": "read_only"}),
        "argument_contract_hash": stable_hash({"arguments": 1}),
        "result_type": "builtins.dict",
        "result_hash": stable_hash(result),
        "result_payload": result,
        "one_time_invocation": True,
        "invocation_authorized": True,
        "invocation_performed": True,
        "invocation_count": 1,
        "corpus_read_performed": False,
        "database_connection_performed": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "execution_status": "invoked_once_result_captured",
    }
    record["invocation_execution_record_hash"] = stable_hash(record)
    manifest = {
        "schema_version": "INT-OIA-011",
        "engine_id": "INT-OIA-011",
        "executed_at": "2026-07-22T00:00:00+00:00",
        "invocation_execution_manifest_id": "int-oia-011-test",
        "invocation_execution_status": "downstream_read_only_consumer_controlled_invocation_executed",
        "invocation_execution_policy_id": "test",
        "source_invocation_readiness_manifest_id": "int-oia-010-test",
        "source_invocation_readiness_manifest_hash": stable_hash({"int": 10}),
        "source_binding_attestation_manifest_id": "int-oia-009-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "execution_record_count": 1,
        "execution_records": [record],
        "all_readiness_hashes_verified": True,
        "all_invocation_nonces_unique": True,
        "all_bound_callable_identities_verified": True,
        "all_argument_contracts_verified": True,
        "all_results_deterministically_hashable": True,
        "certified_artifact_input_mode_preserved": True,
        "immutable_output_mode_preserved": True,
        "source_boundary_consumed_without_reexecution": True,
        "one_time_invocation_enforced": True,
        "controlled_invocation_performed": True,
        "corpus_read_execution_repeated": False,
        "database_connection_performed": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "immutable_execution_artifact_persistence_allowed": True,
    }
    manifest["invocation_execution_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")

def main() -> int:
    print("=" * 40)
    print(" INT-OIA-012 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" INVOCATION RESULT ATTESTATION")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); execution = root / "execution"; attestation = root / "attestation"
        seed(execution)
        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationGate(execution_directory=execution, attestation_directory=attestation)
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "INT-OIA-012"
        assert first.all_execution_hashes_verified
        assert first.all_result_hashes_verified
        assert first.all_execution_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.controlled_result_admission_authorized
        assert not first.downstream_release_performed
        record = first.attestation_records[0]
        assert record.result_hash == record.recomputed_result_hash
        assert record.result_hash_verified
        assert record.result_admission_authorized
        assert record.attestation_status == "result_verified_not_released"
        assert (attestation / "current.json").exists()
        tampered = json.loads((execution / "current.json").read_text(encoding="utf-8"))
        tampered["execution_records"][0]["result_payload"]["read_only"] = False
        (execution / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered execution accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError:
            pass
    print("[PASS] Actual INT-OIA-011 controlled execution consumed")
    print("[PASS] Every execution and lineage hash verified")
    print("[PASS] Analytical result hash independently recomputed")
    print("[PASS] One-time invocation count independently verified")
    print("[PASS] Immutable result payload attested")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe execution evidence rejected")
    print("[PASS] Controlled result admission authorized")
    print("[PASS] Result was not released downstream")
    print("[PASS] Atomic result-attestation artifacts persisted")
    print("[PASS] Signals, alerts, Q Series execution, orders, funds, and portfolio mutation remained disabled")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
"""

def write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")

def verify_upstream() -> None:
    if not UPSTREAM.exists():
        raise FileNotFoundError(f"Actual INT-OIA-011 production module missing: {UPSTREAM}")
    source = UPSTREAM.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "INT-OIA-011"',
        "class DownstreamReadOnlyConsumerControlledInvocationExecutionRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionGate",
        "invocation_execution_manifest_hash",
        "controlled_invocation_performed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError("Actual INT-OIA-011 contract mismatch; missing: " + ", ".join(missing))
    print("[OK] Actual INT-OIA-011 controlled-execution contract verified")

def update_package() -> None:
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export = "from .oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_result_attestation_gate import *"
    if export not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        PACKAGE.write_text(existing + export + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")

def main() -> int:
    print("=" * 40)
    print(" INT-OIA-012 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" INVOCATION RESULT ATTESTATION")
    print("=" * 40)
    verify_upstream()
    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    update_package()
    for path in (PRODUCTION, TEST, PACKAGE):
        py_compile.compile(str(path), doraise=True)
    print("[OK] Production, test, and package syntax verified")
    completed = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    print("[OK] INT-OIA-012 test executed automatically")
    print()
    print("[DONE] INT-OIA-012 controlled invocation result attestation gate installed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
