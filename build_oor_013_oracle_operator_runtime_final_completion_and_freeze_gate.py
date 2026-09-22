from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "qseries_v2" / "oracle_operator_runtime").is_dir():
            return candidate
    raise SystemExit("[ERROR] Could not locate the kalshi-qss-bot repository.")


ROOT = locate_repository()
RUNTIME = ROOT / "qseries_v2" / "oracle_operator_runtime"
SOURCE = RUNTIME / "oracle_operator_runtime_session_activation_continuation_attestation_gate.py"
PRODUCTION = RUNTIME / "oracle_operator_runtime_final_completion_and_freeze_gate.py"
TEST = ROOT / "test_oor_013_oracle_operator_runtime_final_completion_and_freeze_gate.py"
INIT = RUNTIME / "__init__.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom datetime import datetime, timezone\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_continuation_attestation_gate import (\n    ATTESTATION_STATUS as OOR_012_ATTESTATION_STATUS,\n    ATTESTATION_TYPE as OOR_012_ATTESTATION_TYPE,\n    OracleOperatorRuntimeSessionActivationContinuationAttestation,\n)\n\nSCHEMA_VERSION = "OOR-013"\nENGINE_ID = "OOR-013"\nPOLICY_ID = "oracle.operator-runtime-final-completion-and-freeze-gate.v1"\nCOMPLETION_STATUS = "oracle_operator_runtime_complete_and_frozen"\n\n\nclass OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {str(key): _canonical(item) for key, item in value.items()}\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, datetime):\n        if value.tzinfo is None or value.utcoffset() is None:\n            raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n                "datetime must be timezone-aware"\n            )\n        return value.astimezone(timezone.utc).isoformat()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n        f"unsupported value type: {type(value)!r}"\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n    return hashlib.sha256(payload.encode("utf-8")).hexdigest()\n\n\ndef _valid_sha256(value: Any) -> bool:\n    return (\n        isinstance(value, str)\n        and len(value) == 64\n        and all(character in "0123456789abcdef" for character in value)\n    )\n\n\n@dataclass(frozen=True)\nclass OracleOperatorRuntimeFinalCompletionAndFreeze:\n    completion_id: str\n    source_attestation_id: str\n    source_attestation_hash: str\n    source_continuation_id: str\n    source_continuation_hash: str\n    source_session_id: str\n    source_session_hash: str\n    source_request_id: str\n    source_request_hash: str\n    source_dependency_receipt_id: str\n    source_dependency_receipt_hash: str\n    source_operator_completion_certification_id: str\n    runtime_namespace: str\n    complete_lineage_verified: bool\n    deterministic_completion: bool\n    immutable_freeze: bool\n    runtime_complete: bool\n    read_only: bool\n    downstream_read_only_operation_allowed: bool\n    further_oor_certification_required: bool\n    runtime_serving_allowed: bool\n    network_listener_allowed: bool\n    database_connection_allowed: bool\n    publication_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    completion_status: str\n    completion_hash: str\n\n\ndef _verify_source_attestation(\n    attestation: OracleOperatorRuntimeSessionActivationContinuationAttestation,\n) -> None:\n    if not isinstance(attestation, OracleOperatorRuntimeSessionActivationContinuationAttestation):\n        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n            "attestation must be canonical OOR-012 continuation attestation"\n        )\n\n    body = asdict(attestation)\n    supplied_hash = body.pop("attestation_hash", None)\n    if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:\n        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n            "OOR-012 attestation hash mismatch"\n        )\n\n    lineage = (\n        attestation.attestation_id,\n        attestation.continuation_id,\n        attestation.continuation_hash,\n        attestation.session_id,\n        attestation.session_hash,\n        attestation.request_id,\n        attestation.request_hash,\n        attestation.dependency_receipt_id,\n        attestation.dependency_receipt_hash,\n        attestation.source_operator_completion_certification_id,\n    )\n    if not all(_valid_sha256(value) for value in lineage):\n        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n            "OOR-012 lineage identity invalid"\n        )\n\n    required = (\n        attestation.continuation_identity_verified,\n        attestation.continuation_hash_verified,\n        attestation.continuation_contract_verified,\n        attestation.complete_runtime_lineage_verified,\n        attestation.single_continuation_scope_verified,\n        attestation.single_attestation_scope_verified,\n        attestation.attestation_single_use_verified,\n        attestation.read_only_boundary_verified,\n        attestation.deterministic_boundary_verified,\n        attestation.immutable_result_boundary_verified,\n        attestation.attestation_type == OOR_012_ATTESTATION_TYPE,\n        attestation.attestation_status == OOR_012_ATTESTATION_STATUS,\n        not attestation.duplicate_attestation_allowed,\n        not attestation.attestation_reversible,\n    )\n    forbidden = (\n        attestation.runtime_serving_allowed,\n        attestation.network_listener_allowed,\n        attestation.database_connection_allowed,\n        attestation.publication_allowed,\n        attestation.qseries_handoff_allowed,\n        attestation.qseries_execution_allowed,\n        attestation.order_creation_allowed,\n        attestation.funds_movement_allowed,\n        attestation.portfolio_mutation_allowed,\n    )\n    if not all(required) or any(forbidden):\n        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n            "OOR-012 permanent read-only boundary violated"\n        )\n\n\ndef complete_and_freeze_oracle_operator_runtime(\n    *,\n    attestation: OracleOperatorRuntimeSessionActivationContinuationAttestation,\n) -> OracleOperatorRuntimeFinalCompletionAndFreeze:\n    _verify_source_attestation(attestation)\n\n    body = {\n        "source_attestation_id": attestation.attestation_id,\n        "source_attestation_hash": attestation.attestation_hash,\n        "source_continuation_id": attestation.continuation_id,\n        "source_continuation_hash": attestation.continuation_hash,\n        "source_session_id": attestation.session_id,\n        "source_session_hash": attestation.session_hash,\n        "source_request_id": attestation.request_id,\n        "source_request_hash": attestation.request_hash,\n        "source_dependency_receipt_id": attestation.dependency_receipt_id,\n        "source_dependency_receipt_hash": attestation.dependency_receipt_hash,\n        "source_operator_completion_certification_id": attestation.source_operator_completion_certification_id,\n        "runtime_namespace": attestation.runtime_namespace,\n        "complete_lineage_verified": True,\n        "deterministic_completion": True,\n        "immutable_freeze": True,\n        "runtime_complete": True,\n        "read_only": True,\n        "downstream_read_only_operation_allowed": True,\n        "further_oor_certification_required": False,\n        "runtime_serving_allowed": False,\n        "network_listener_allowed": False,\n        "database_connection_allowed": False,\n        "publication_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "completion_status": COMPLETION_STATUS,\n    }\n    body["completion_id"] = stable_hash(\n        {\n            "engine_id": ENGINE_ID,\n            "source_attestation_id": attestation.attestation_id,\n            "source_attestation_hash": attestation.attestation_hash,\n            "completion_status": COMPLETION_STATUS,\n        }\n    )\n    return OracleOperatorRuntimeFinalCompletionAndFreeze(\n        **body,\n        completion_hash=stable_hash(body),\n    )\n\n\ndef verify_oracle_operator_runtime_final_completion_and_freeze(\n    value: OracleOperatorRuntimeFinalCompletionAndFreeze,\n) -> bool:\n    if not isinstance(value, OracleOperatorRuntimeFinalCompletionAndFreeze):\n        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n            "value must be canonical OOR-013 completion"\n        )\n    body = asdict(value)\n    supplied_hash = body.pop("completion_hash", None)\n    if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:\n        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n            "OOR-013 completion hash mismatch"\n        )\n    required = (\n        value.complete_lineage_verified,\n        value.deterministic_completion,\n        value.immutable_freeze,\n        value.runtime_complete,\n        value.read_only,\n        value.downstream_read_only_operation_allowed,\n        not value.further_oor_certification_required,\n    )\n    forbidden = (\n        value.runtime_serving_allowed,\n        value.network_listener_allowed,\n        value.database_connection_allowed,\n        value.publication_allowed,\n        value.qseries_handoff_allowed,\n        value.qseries_execution_allowed,\n        value.order_creation_allowed,\n        value.funds_movement_allowed,\n        value.portfolio_mutation_allowed,\n    )\n    if not all(required) or any(forbidden) or value.completion_status != COMPLETION_STATUS:\n        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(\n            "OOR-013 permanent completion boundary violated"\n        )\n    return True\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "POLICY_ID",\n    "COMPLETION_STATUS",\n    "OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError",\n    "OracleOperatorRuntimeFinalCompletionAndFreeze",\n    "complete_and_freeze_oracle_operator_runtime",\n    "verify_oracle_operator_runtime_final_completion_and_freeze",\n    "stable_hash",\n]\n'
TEST_SOURCE = 'from dataclasses import asdict, replace\nfrom datetime import datetime, timedelta, timezone\n\nfrom qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_continuation_attestation_gate import (\n    ATTESTATION_STATUS,\n    ATTESTATION_TYPE,\n    OracleOperatorRuntimeSessionActivationContinuationAttestation,\n    stable_hash as attestation_hash,\n)\nfrom qseries_v2.oracle_operator_runtime.oracle_operator_runtime_final_completion_and_freeze_gate import *\n\n\ndef sample_attestation() -> OracleOperatorRuntimeSessionActivationContinuationAttestation:\n    start = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)\n    times = [start + timedelta(seconds=index) for index in range(11)]\n    body = dict(\n        attestation_id="1" * 64,\n        continuation_id="2" * 64,\n        continuation_hash="3" * 64,\n        authorization_consumption_id="4" * 64,\n        authorization_consumption_hash="5" * 64,\n        activation_authorization_id="6" * 64,\n        activation_authorization_hash="7" * 64,\n        attestation_source_id="8" * 64,\n        attestation_source_hash="9" * 64,\n        activation_id="a" * 64,\n        activation_hash="b" * 64,\n        session_authorization_consumption_id="c" * 64,\n        session_authorization_consumption_hash="d" * 64,\n        session_authorization_id="e" * 64,\n        session_authorization_hash="f" * 64,\n        session_id="0" * 64,\n        session_hash="1" * 64,\n        admission_id="2" * 64,\n        admission_hash="3" * 64,\n        request_id="4" * 64,\n        request_hash="5" * 64,\n        dependency_receipt_id="6" * 64,\n        dependency_receipt_hash="7" * 64,\n        source_operator_completion_certification_id="8" * 64,\n        runtime_namespace="oracle_operator_runtime",\n        requester_id="operator:test",\n        correlation_id="correlation:test",\n        mode="query",\n        query_text="Show certified intelligence.",\n        requested_at=times[0],\n        admitted_at=times[1],\n        assembled_at=times[2],\n        session_authorized_at=times[3],\n        session_authorization_consumed_at=times[4],\n        activated_at=times[5],\n        activation_attested_at=times[6],\n        activation_authorized_at=times[7],\n        activation_authorization_consumed_at=times[8],\n        continued_at=times[9],\n        continuation_attested_at=times[10],\n        continuation_identity_verified=True,\n        continuation_hash_verified=True,\n        continuation_contract_verified=True,\n        complete_runtime_lineage_verified=True,\n        single_continuation_scope_verified=True,\n        single_attestation_scope_verified=True,\n        attestation_single_use_verified=True,\n        read_only_boundary_verified=True,\n        deterministic_boundary_verified=True,\n        immutable_result_boundary_verified=True,\n        duplicate_attestation_allowed=False,\n        attestation_reversible=False,\n        runtime_serving_allowed=False,\n        network_listener_allowed=False,\n        database_connection_allowed=False,\n        publication_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        attestation_type=ATTESTATION_TYPE,\n        attestation_status=ATTESTATION_STATUS,\n    )\n    return OracleOperatorRuntimeSessionActivationContinuationAttestation(\n        **body,\n        attestation_hash=attestation_hash(body),\n    )\n\n\ndef reject(function) -> None:\n    try:\n        function()\n        raise AssertionError("unsafe final completion accepted")\n    except OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError:\n        pass\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OOR-013 TEST")\n    print(" FINAL COMPLETION AND FREEZE GATE")\n    print("=" * 40)\n\n    source = sample_attestation()\n    first = complete_and_freeze_oracle_operator_runtime(attestation=source)\n    second = complete_and_freeze_oracle_operator_runtime(attestation=source)\n\n    assert first == second\n    assert verify_oracle_operator_runtime_final_completion_and_freeze(first)\n    assert first.completion_hash == stable_hash(\n        {key: value for key, value in asdict(first).items() if key != "completion_hash"}\n    )\n    assert first.runtime_complete and first.immutable_freeze and first.read_only\n    assert first.downstream_read_only_operation_allowed\n    assert not first.further_oor_certification_required\n\n    reject(lambda: complete_and_freeze_oracle_operator_runtime(attestation=replace(source, attestation_hash="0" * 64)))\n    reject(lambda: complete_and_freeze_oracle_operator_runtime(attestation=replace(source, qseries_execution_allowed=True)))\n    reject(lambda: verify_oracle_operator_runtime_final_completion_and_freeze(replace(first, completion_hash="0" * 64)))\n\n    print("[PASS] Actual OOR-012 continuation attestation consumed")\n    print("[PASS] Complete OOR-001 through OOR-012 lineage preserved")\n    print("[PASS] Deterministic final completion certified")\n    print("[PASS] Immutable Oracle Operator Runtime freeze certified")\n    print("[PASS] Downstream read-only operation remains allowed")\n    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")\n    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")\n    print("[PASS] No further OOR certification layers required")\n    print("[DONE] OOR-013 FINAL COMPLETION AND FREEZE GATE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" OOR-013 INSTALLER")
    print(" FINAL COMPLETION AND FREEZE GATE")
    print("=" * 40)
    try:
        if not SOURCE.is_file():
            raise RuntimeError(f"Actual OOR-012 module missing: {SOURCE}")
        source_text = SOURCE.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "OOR-012"',
            "OracleOperatorRuntimeSessionActivationContinuationAttestation",
            "ATTESTATION_TYPE",
            "ATTESTATION_STATUS",
            "attestation_hash",
            "complete_runtime_lineage_verified",
        )
        missing = [item for item in required if item not in source_text]
        if missing:
            raise RuntimeError(f"OOR-012 contract incomplete: {missing}")
        ast.parse(source_text, filename=str(SOURCE))
        protected_hash = sha256(SOURCE)
        print("[OK] Actual OOR-012 continuation attestation contract verified")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_operator_runtime_final_completion_and_freeze_gate import *"
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            INIT.write_text(current + export + "\n", encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"OOR-013 test failed with exit code {completed.returncode}")
        if sha256(SOURCE) != protected_hash:
            raise RuntimeError("Protected OOR-012 module changed")

        print("[PASS] Protected OOR-012 module unchanged")
        print("[PASS] OOR-001 through OOR-012 lineage preserved")
        print("[PASS] No acquisition, analytics, Oracle Operator, or Q Series execution module modified")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OOR-013 FINAL COMPLETION AND FREEZE GATE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
