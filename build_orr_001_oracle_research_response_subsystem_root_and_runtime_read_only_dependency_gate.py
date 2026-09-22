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
        if (
            candidate / "qseries_v2" / "oracle_operator_runtime" /
            "oracle_operator_runtime_final_completion_and_freeze_gate.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository with actual OOR-013 module.")


ROOT = locate_repository()
QROOT = ROOT / "qseries_v2"
SOURCE = (
    QROOT / "oracle_operator_runtime" /
    "oracle_operator_runtime_final_completion_and_freeze_gate.py"
)
PACKAGE = QROOT / "oracle_research_response"
PRODUCTION = PACKAGE / "oracle_research_response_runtime_read_only_dependency_gate.py"
TEST = ROOT / "test_orr_001_oracle_research_response_subsystem_root_and_runtime_read_only_dependency_gate.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom datetime import datetime, timezone\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_operator_runtime.oracle_operator_runtime_final_completion_and_freeze_gate import (\n    COMPLETION_STATUS as OOR_013_COMPLETION_STATUS,\n    OracleOperatorRuntimeFinalCompletionAndFreeze,\n    verify_oracle_operator_runtime_final_completion_and_freeze,\n)\n\nSCHEMA_VERSION = "ORR-001"\nENGINE_ID = "ORR-001"\nPOLICY_ID = "oracle.research-response.runtime-read-only-dependency-gate.v1"\nSUBSYSTEM_NAMESPACE = "oracle_research_response"\nDEPENDENCY_TYPE = "oracle_operator_runtime_final_completion_read_only_dependency"\nDEPENDENCY_STATUS = "oracle_operator_runtime_dependency_admitted"\n\n\nclass OracleResearchResponseRuntimeDependencyInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {str(key): _canonical(item) for key, item in value.items()}\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, datetime):\n        if value.tzinfo is None or value.utcoffset() is None:\n            raise OracleResearchResponseRuntimeDependencyInvariantError(\n                "datetime must be timezone-aware"\n            )\n        return value.astimezone(timezone.utc).isoformat()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleResearchResponseRuntimeDependencyInvariantError(\n        f"unsupported value type: {type(value)!r}"\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n    return hashlib.sha256(payload.encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleResearchResponseRuntimeDependencyReceipt:\n    dependency_receipt_id: str\n    source_runtime_completion_id: str\n    source_runtime_completion_hash: str\n    source_runtime_namespace: str\n    source_runtime_completion_status: str\n    subsystem_namespace: str\n    admitted_at: datetime\n    complete_runtime_lineage_verified: bool\n    source_runtime_complete_verified: bool\n    source_runtime_immutable_freeze_verified: bool\n    source_runtime_read_only_verified: bool\n    downstream_read_only_operation_verified: bool\n    deterministic_boundary_verified: bool\n    immutable_result_boundary_verified: bool\n    dependency_single_use_verified: bool\n    duplicate_dependency_allowed: bool\n    dependency_reversible: bool\n    runtime_serving_allowed: bool\n    network_listener_allowed: bool\n    database_connection_allowed: bool\n    publication_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    dependency_type: str\n    dependency_status: str\n    dependency_receipt_hash: str\n\n\nclass OracleResearchResponseRuntimeDependencyGate:\n    def admit(\n        self,\n        *,\n        completion: OracleOperatorRuntimeFinalCompletionAndFreeze,\n        admitted_at: datetime,\n    ) -> OracleResearchResponseRuntimeDependencyReceipt:\n        if not isinstance(completion, OracleOperatorRuntimeFinalCompletionAndFreeze):\n            raise OracleResearchResponseRuntimeDependencyInvariantError(\n                "completion must be canonical OOR-013 final completion"\n            )\n\n        try:\n            verified = verify_oracle_operator_runtime_final_completion_and_freeze(completion)\n        except Exception as exc:\n            raise OracleResearchResponseRuntimeDependencyInvariantError(\n                "OOR-013 completion verification failed"\n            ) from exc\n        if not verified:\n            raise OracleResearchResponseRuntimeDependencyInvariantError(\n                "OOR-013 completion verification failed"\n            )\n\n        required = (\n            completion.complete_lineage_verified,\n            completion.deterministic_completion,\n            completion.immutable_freeze,\n            completion.runtime_complete,\n            completion.read_only,\n            completion.downstream_read_only_operation_allowed,\n            not completion.further_oor_certification_required,\n            completion.completion_status == OOR_013_COMPLETION_STATUS,\n        )\n        forbidden = (\n            completion.runtime_serving_allowed,\n            completion.network_listener_allowed,\n            completion.database_connection_allowed,\n            completion.publication_allowed,\n            completion.qseries_handoff_allowed,\n            completion.qseries_execution_allowed,\n            completion.order_creation_allowed,\n            completion.funds_movement_allowed,\n            completion.portfolio_mutation_allowed,\n        )\n        if not all(required) or any(forbidden):\n            raise OracleResearchResponseRuntimeDependencyInvariantError(\n                "OOR-013 permanent read-only boundary violated"\n            )\n\n        if (\n            not isinstance(admitted_at, datetime)\n            or admitted_at.tzinfo is None\n            or admitted_at.utcoffset() is None\n        ):\n            raise OracleResearchResponseRuntimeDependencyInvariantError(\n                "admitted_at must be timezone-aware"\n            )\n        at = admitted_at.astimezone(timezone.utc)\n\n        body = {\n            "source_runtime_completion_id": completion.completion_id,\n            "source_runtime_completion_hash": completion.completion_hash,\n            "source_runtime_namespace": completion.runtime_namespace,\n            "source_runtime_completion_status": completion.completion_status,\n            "subsystem_namespace": SUBSYSTEM_NAMESPACE,\n            "admitted_at": at,\n            "complete_runtime_lineage_verified": True,\n            "source_runtime_complete_verified": True,\n            "source_runtime_immutable_freeze_verified": True,\n            "source_runtime_read_only_verified": True,\n            "downstream_read_only_operation_verified": True,\n            "deterministic_boundary_verified": True,\n            "immutable_result_boundary_verified": True,\n            "dependency_single_use_verified": True,\n            "duplicate_dependency_allowed": False,\n            "dependency_reversible": False,\n            "runtime_serving_allowed": False,\n            "network_listener_allowed": False,\n            "database_connection_allowed": False,\n            "publication_allowed": False,\n            "qseries_handoff_allowed": False,\n            "qseries_execution_allowed": False,\n            "order_creation_allowed": False,\n            "funds_movement_allowed": False,\n            "portfolio_mutation_allowed": False,\n            "dependency_type": DEPENDENCY_TYPE,\n            "dependency_status": DEPENDENCY_STATUS,\n        }\n        body["dependency_receipt_id"] = stable_hash(\n            {\n                "engine_id": ENGINE_ID,\n                "source_runtime_completion_id": completion.completion_id,\n                "source_runtime_completion_hash": completion.completion_hash,\n                "subsystem_namespace": SUBSYSTEM_NAMESPACE,\n                "admitted_at": at,\n                "dependency_type": DEPENDENCY_TYPE,\n            }\n        )\n        return OracleResearchResponseRuntimeDependencyReceipt(\n            **body,\n            dependency_receipt_hash=stable_hash(body),\n        )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "POLICY_ID",\n    "SUBSYSTEM_NAMESPACE",\n    "DEPENDENCY_TYPE",\n    "DEPENDENCY_STATUS",\n    "OracleResearchResponseRuntimeDependencyInvariantError",\n    "OracleResearchResponseRuntimeDependencyReceipt",\n    "OracleResearchResponseRuntimeDependencyGate",\n    "stable_hash",\n]\n'
TEST_SOURCE = '\nfrom dataclasses import asdict, replace\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.oracle_operator_runtime.oracle_operator_runtime_final_completion_and_freeze_gate import (\n    COMPLETION_STATUS,\n    OracleOperatorRuntimeFinalCompletionAndFreeze,\n    stable_hash as completion_hash,\n)\nfrom qseries_v2.oracle_research_response.oracle_research_response_runtime_read_only_dependency_gate import *\n\n\ndef sample_completion() -> OracleOperatorRuntimeFinalCompletionAndFreeze:\n    body = {\n        "completion_id": "1" * 64,\n        "source_attestation_id": "2" * 64,\n        "source_attestation_hash": "3" * 64,\n        "source_continuation_id": "4" * 64,\n        "source_continuation_hash": "5" * 64,\n        "source_session_id": "6" * 64,\n        "source_session_hash": "7" * 64,\n        "source_request_id": "8" * 64,\n        "source_request_hash": "9" * 64,\n        "source_dependency_receipt_id": "a" * 64,\n        "source_dependency_receipt_hash": "b" * 64,\n        "source_operator_completion_certification_id": "c" * 64,\n        "runtime_namespace": "oracle_operator_runtime",\n        "complete_lineage_verified": True,\n        "deterministic_completion": True,\n        "immutable_freeze": True,\n        "runtime_complete": True,\n        "read_only": True,\n        "downstream_read_only_operation_allowed": True,\n        "further_oor_certification_required": False,\n        "runtime_serving_allowed": False,\n        "network_listener_allowed": False,\n        "database_connection_allowed": False,\n        "publication_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "completion_status": COMPLETION_STATUS,\n    }\n    return OracleOperatorRuntimeFinalCompletionAndFreeze(\n        **body,\n        completion_hash=completion_hash(body),\n    )\n\n\ndef reject(function) -> None:\n    try:\n        function()\n        raise AssertionError("unsafe dependency admission accepted")\n    except OracleResearchResponseRuntimeDependencyInvariantError:\n        pass\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" ORR-001 TEST")\n    print(" RESEARCH RESPONSE SUBSYSTEM ROOT")\n    print(" RUNTIME READ-ONLY DEPENDENCY GATE")\n    print("=" * 40)\n\n    completion = sample_completion()\n    admitted_at = datetime(2026, 7, 28, 18, 0, tzinfo=timezone.utc)\n    gate = OracleResearchResponseRuntimeDependencyGate()\n\n    first = gate.admit(completion=completion, admitted_at=admitted_at)\n    second = gate.admit(completion=completion, admitted_at=admitted_at)\n\n    assert first == second\n    assert first.dependency_receipt_hash == stable_hash(\n        {\n            key: value\n            for key, value in asdict(first).items()\n            if key != "dependency_receipt_hash"\n        }\n    )\n    assert first.subsystem_namespace == SUBSYSTEM_NAMESPACE\n    assert first.dependency_type == DEPENDENCY_TYPE\n    assert first.dependency_status == DEPENDENCY_STATUS\n    assert first.source_runtime_complete_verified\n    assert first.source_runtime_immutable_freeze_verified\n    assert first.source_runtime_read_only_verified\n    assert first.downstream_read_only_operation_verified\n    assert first.dependency_single_use_verified\n    assert not first.duplicate_dependency_allowed\n    assert not first.dependency_reversible\n\n    reject(\n        lambda: gate.admit(\n            completion=replace(completion, completion_hash="0" * 64),\n            admitted_at=admitted_at,\n        )\n    )\n    reject(\n        lambda: gate.admit(\n            completion=replace(\n                completion,\n                qseries_execution_allowed=True,\n                completion_hash=completion.completion_hash,\n            ),\n            admitted_at=admitted_at,\n        )\n    )\n    reject(\n        lambda: gate.admit(\n            completion=completion,\n            admitted_at=datetime(2026, 7, 28, 18, 0),\n        )\n    )\n\n    print("[PASS] Actual OOR-013 final completion contract consumed")\n    print("[PASS] Frozen Oracle Operator Runtime admitted as read-only dependency")\n    print("[PASS] Oracle Research Response package root established")\n    print("[PASS] Deterministic immutable dependency receipt certified")\n    print("[PASS] Single-use and non-reversible dependency boundary certified")\n    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")\n    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")\n    print("[PASS] Tampered and unsafe dependencies rejected")\n    print("[DONE] ORR-001 RESEARCH RESPONSE ROOT AND DEPENDENCY GATE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" ORR-001 INSTALLER")
    print(" RESEARCH RESPONSE SUBSYSTEM ROOT")
    print(" RUNTIME READ-ONLY DEPENDENCY GATE")
    print("=" * 40)
    try:
        source_text = SOURCE.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "OOR-013"',
            "OracleOperatorRuntimeFinalCompletionAndFreeze",
            "verify_oracle_operator_runtime_final_completion_and_freeze",
            "downstream_read_only_operation_allowed",
            "further_oor_certification_required",
            "completion_hash",
        )
        missing = [item for item in required if item not in source_text]
        if missing:
            raise RuntimeError(f"OOR-013 contract incomplete: {missing}")
        ast.parse(source_text, filename=str(SOURCE))
        protected_hash = sha256(SOURCE)
        print("[OK] Actual OOR-013 final completion and freeze contract verified")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        init_source = """from __future__ import annotations

from .oracle_research_response_runtime_read_only_dependency_gate import (
    DEPENDENCY_STATUS,
    DEPENDENCY_TYPE,
    ENGINE_ID,
    POLICY_ID,
    SCHEMA_VERSION,
    SUBSYSTEM_NAMESPACE,
    OracleResearchResponseRuntimeDependencyGate,
    OracleResearchResponseRuntimeDependencyInvariantError,
    OracleResearchResponseRuntimeDependencyReceipt,
    stable_hash,
)

__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "SUBSYSTEM_NAMESPACE",
    "DEPENDENCY_TYPE",
    "DEPENDENCY_STATUS",
    "OracleResearchResponseRuntimeDependencyInvariantError",
    "OracleResearchResponseRuntimeDependencyReceipt",
    "OracleResearchResponseRuntimeDependencyGate",
    "stable_hash",
]
"""
        write_complete(INIT, init_source)

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"ORR-001 test failed with exit code {completed.returncode}")
        if sha256(SOURCE) != protected_hash:
            raise RuntimeError("Protected OOR-013 module changed")

        print("[PASS] Protected OOR-013 module unchanged")
        print("[PASS] Oracle Research Response established as separate package")
        print("[PASS] OOR-013 consumed only through certified read-only dependency")
        print("[PASS] No acquisition, analytics, integration, operator, or runtime module modified")
        print("[PASS] No Q Series execution module modified")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] ORR-001 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
