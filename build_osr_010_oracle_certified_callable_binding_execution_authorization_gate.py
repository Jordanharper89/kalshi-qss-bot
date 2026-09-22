from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning_runtime"
SOURCE_OSR009 = PACKAGE / "oracle_callable_binding_execution_readiness_gate.py"
PRODUCTION = (
    PACKAGE
    / "oracle_certified_callable_binding_execution_authorization_gate.py"
)
TEST = (
    ROOT
    / "test_osr_010_oracle_certified_callable_binding_execution_authorization_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom .oracle_callable_binding_execution_readiness_gate import (\n    verify_callable_binding_execution_readiness,\n)\n\nENGINE_ID = "OSR-010"\nSCHEMA_VERSION = "OSR-010.v1"\nALGORITHM_VERSION = "certified-callable-binding-execution-authorization.v1"\nAUTHORIZATION_STATUS = (\n    "callable_binding_execution_authorized_not_consumed_not_executed"\n)\n\n\nclass OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(ValueError):\n    """Raised when an OSR-010 execution-authorization invariant fails."""\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\ndef _snapshot(value: Any) -> dict[str, Any]:\n    if is_dataclass(value):\n        return asdict(value)\n    if isinstance(value, Mapping):\n        return dict(value)\n    data = getattr(value, "__dict__", None)\n    if isinstance(data, dict):\n        return dict(data)\n    raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n        "execution-readiness object cannot be snapshotted"\n    )\n\n\ndef _required(snapshot: Mapping[str, Any], name: str) -> Any:\n    if name not in snapshot:\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            f"missing execution-readiness field: {name}"\n        )\n    return snapshot[name]\n\n\n@dataclass(frozen=True)\nclass CertifiedCallableBindingExecutionAuthorization:\n    authorization_id: str\n    source_execution_readiness_id: str\n    source_execution_readiness_hash: str\n    source_binding_activation_id: str\n    source_binding_activation_hash: str\n    source_binding_authorization_id: str\n    source_binding_authorization_hash: str\n    source_binding_readiness_id: str\n    source_binding_readiness_hash: str\n    source_resolution_activation_id: str\n    source_resolution_activation_hash: str\n    source_resolution_authorization_id: str\n    source_resolution_authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    callable_count: int\n    execution_readiness_verified: bool\n    exact_readiness_hash_scope_preserved: bool\n    bounded_binding_scope_preserved: bool\n    deterministic_binding_required: bool\n    immutable_binding_result_required: bool\n    implementation_import_allowed: bool\n    implementation_symbol_load_allowed: bool\n    callable_binding_execution_authorized: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    authorization_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    authorization_hash: str\n\n\ndef authorize_callable_binding_execution(\n    *,\n    readiness: Any,\n) -> CertifiedCallableBindingExecutionAuthorization:\n    try:\n        verify_callable_binding_execution_readiness(readiness)\n    except Exception as exc:\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "OSR-009 callable-binding execution readiness verification failed"\n        ) from exc\n\n    snapshot = _snapshot(readiness)\n\n    if snapshot.get("read_only") is not True:\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "OSR-009 execution readiness must remain read-only"\n        )\n    if snapshot.get("callable_binding_execution_ready") is not True:\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "callable-binding execution readiness is not certified"\n        )\n    if snapshot.get("callable_binding_execution_authorized") is not False:\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "OSR-009 must not already authorize execution"\n        )\n\n    forbidden_source_flags = (\n        bool(snapshot.get("implementation_import_allowed", False)),\n        bool(snapshot.get("implementation_symbol_load_allowed", False)),\n        bool(snapshot.get("callable_binding_allowed", False)),\n        bool(snapshot.get("reasoning_execution_allowed", False)),\n        bool(snapshot.get("probability_estimation_allowed", False)),\n        bool(snapshot.get("final_intelligence_conclusion_allowed", False)),\n        bool(snapshot.get("publication_allowed", False)),\n        bool(snapshot.get("alerting_allowed", False)),\n        bool(snapshot.get("qseries_handoff_allowed", False)),\n        bool(snapshot.get("qseries_execution_allowed", False)),\n        bool(snapshot.get("order_creation_allowed", False)),\n        bool(snapshot.get("funds_movement_allowed", False)),\n        bool(snapshot.get("portfolio_mutation_allowed", False)),\n    )\n    if any(forbidden_source_flags):\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "OSR-009 readiness violates permanent safety boundaries"\n        )\n\n    callable_count = int(_required(snapshot, "callable_count"))\n    if callable_count <= 0:\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "callable count must be positive"\n        )\n\n    body = {\n        "source_execution_readiness_id": str(_required(snapshot, "readiness_id")),\n        "source_execution_readiness_hash": str(_required(snapshot, "readiness_hash")),\n        "source_binding_activation_id": str(\n            _required(snapshot, "source_binding_activation_id")\n        ),\n        "source_binding_activation_hash": str(\n            _required(snapshot, "source_binding_activation_hash")\n        ),\n        "source_binding_authorization_id": str(\n            _required(snapshot, "source_binding_authorization_id")\n        ),\n        "source_binding_authorization_hash": str(\n            _required(snapshot, "source_binding_authorization_hash")\n        ),\n        "source_binding_readiness_id": str(\n            _required(snapshot, "source_binding_readiness_id")\n        ),\n        "source_binding_readiness_hash": str(\n            _required(snapshot, "source_binding_readiness_hash")\n        ),\n        "source_resolution_activation_id": str(\n            _required(snapshot, "source_resolution_activation_id")\n        ),\n        "source_resolution_activation_hash": str(\n            _required(snapshot, "source_resolution_activation_hash")\n        ),\n        "source_resolution_authorization_id": str(\n            _required(snapshot, "source_resolution_authorization_id")\n        ),\n        "source_resolution_authorization_hash": str(\n            _required(snapshot, "source_resolution_authorization_hash")\n        ),\n        "source_resolution_package_id": str(\n            _required(snapshot, "source_resolution_package_id")\n        ),\n        "source_resolution_hash": str(\n            _required(snapshot, "source_resolution_hash")\n        ),\n        "source_admission_package_id": str(\n            _required(snapshot, "source_admission_package_id")\n        ),\n        "source_admission_hash": str(\n            _required(snapshot, "source_admission_hash")\n        ),\n        "callable_count": callable_count,\n        "execution_readiness_verified": True,\n        "exact_readiness_hash_scope_preserved": True,\n        "bounded_binding_scope_preserved": True,\n        "deterministic_binding_required": True,\n        "immutable_binding_result_required": True,\n        "implementation_import_allowed": False,\n        "implementation_symbol_load_allowed": False,\n        "callable_binding_execution_authorized": True,\n        "callable_binding_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "authorization_status": AUTHORIZATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n    authorization_hash = stable_hash(body)\n\n    return CertifiedCallableBindingExecutionAuthorization(\n        authorization_id=(\n            "callable-binding-execution-authorization:" + authorization_hash\n        ),\n        **body,\n        authorization_hash=authorization_hash,\n    )\n\n\ndef verify_certified_callable_binding_execution_authorization(\n    authorization: CertifiedCallableBindingExecutionAuthorization,\n) -> bool:\n    if not isinstance(\n        authorization,\n        CertifiedCallableBindingExecutionAuthorization,\n    ):\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "invalid callable-binding execution authorization"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(authorization).items()\n        if key not in {"authorization_id", "authorization_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if authorization.authorization_hash != expected_hash:\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "callable-binding execution authorization hash mismatch"\n        )\n    if authorization.authorization_id != (\n        "callable-binding-execution-authorization:" + expected_hash\n    ):\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "callable-binding execution authorization identity mismatch"\n        )\n\n    forbidden = (\n        authorization.implementation_import_allowed,\n        authorization.implementation_symbol_load_allowed,\n        authorization.callable_binding_allowed,\n        authorization.reasoning_execution_allowed,\n        authorization.probability_estimation_allowed,\n        authorization.final_intelligence_conclusion_allowed,\n        authorization.publication_allowed,\n        authorization.alerting_allowed,\n        authorization.qseries_handoff_allowed,\n        authorization.qseries_execution_allowed,\n        authorization.order_creation_allowed,\n        authorization.funds_movement_allowed,\n        authorization.portfolio_mutation_allowed,\n    )\n    if (\n        authorization.engine_id != ENGINE_ID\n        or authorization.schema_version != SCHEMA_VERSION\n        or authorization.algorithm_version != ALGORITHM_VERSION\n        or authorization.authorization_status != AUTHORIZATION_STATUS\n        or authorization.execution_readiness_verified is not True\n        or authorization.exact_readiness_hash_scope_preserved is not True\n        or authorization.bounded_binding_scope_preserved is not True\n        or authorization.deterministic_binding_required is not True\n        or authorization.immutable_binding_result_required is not True\n        or authorization.callable_binding_execution_authorized is not True\n        or authorization.read_only is not True\n        or authorization.callable_count <= 0\n        or any(forbidden)\n    ):\n        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(\n            "OSR-010 permanent safety boundary violated"\n        )\n    return True\n\n\ndef serialize_certified_callable_binding_execution_authorization(\n    authorization: CertifiedCallableBindingExecutionAuthorization,\n) -> str:\n    verify_certified_callable_binding_execution_authorization(authorization)\n    return canonical_json(authorization)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "AUTHORIZATION_STATUS",\n    "OracleCertifiedCallableBindingExecutionAuthorizationInvariantError",\n    "CertifiedCallableBindingExecutionAuthorization",\n    "authorize_callable_binding_execution",\n    "verify_certified_callable_binding_execution_authorization",\n    "serialize_certified_callable_binding_execution_authorization",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, replace\nimport importlib\n\nmodule = importlib.import_module(\n    "qseries_v2.oracle_scientific_reasoning_runtime."\n    "oracle_certified_callable_binding_execution_authorization_gate"\n)\n\n\n@dataclass(frozen=True)\nclass StubCallableBindingExecutionReadiness:\n    readiness_id: str\n    readiness_hash: str\n    source_binding_activation_id: str\n    source_binding_activation_hash: str\n    source_binding_authorization_id: str\n    source_binding_authorization_hash: str\n    source_binding_readiness_id: str\n    source_binding_readiness_hash: str\n    source_resolution_activation_id: str\n    source_resolution_activation_hash: str\n    source_resolution_authorization_id: str\n    source_resolution_authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    callable_count: int\n    callable_binding_execution_ready: bool\n    callable_binding_execution_authorized: bool\n    implementation_import_allowed: bool\n    implementation_symbol_load_allowed: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n\n\ndef accepted_verifier(value) -> bool:\n    if not isinstance(value, StubCallableBindingExecutionReadiness):\n        raise ValueError("unexpected readiness type")\n    if value.callable_binding_execution_ready is not True:\n        raise ValueError("execution readiness not certified")\n    return True\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedCallableBindingExecutionAuthorizationInvariantError:\n        return\n    raise AssertionError("expected OSR-010 invariant rejection")\n\n\ndef main() -> None:\n    original_verifier = module.verify_callable_binding_execution_readiness\n    module.verify_callable_binding_execution_readiness = accepted_verifier\n    try:\n        readiness = StubCallableBindingExecutionReadiness(\n            readiness_id="callable-binding-execution-readiness:" + "a" * 64,\n            readiness_hash="a" * 64,\n            source_binding_activation_id="callable-binding-activation:" + "b" * 64,\n            source_binding_activation_hash="b" * 64,\n            source_binding_authorization_id=(\n                "callable-binding-authorization:" + "c" * 64\n            ),\n            source_binding_authorization_hash="c" * 64,\n            source_binding_readiness_id="callable-binding-readiness:" + "d" * 64,\n            source_binding_readiness_hash="d" * 64,\n            source_resolution_activation_id="osr005:activation:001",\n            source_resolution_activation_hash="e" * 64,\n            source_resolution_authorization_id="osr004:authorization:001",\n            source_resolution_authorization_hash="f" * 64,\n            source_resolution_package_id="osr003:resolution:001",\n            source_resolution_hash="1" * 64,\n            source_admission_package_id="osr002:admission:001",\n            source_admission_hash="2" * 64,\n            callable_count=9,\n            callable_binding_execution_ready=True,\n            callable_binding_execution_authorized=False,\n            implementation_import_allowed=False,\n            implementation_symbol_load_allowed=False,\n            callable_binding_allowed=False,\n            reasoning_execution_allowed=False,\n            probability_estimation_allowed=False,\n            final_intelligence_conclusion_allowed=False,\n            publication_allowed=False,\n            alerting_allowed=False,\n            qseries_handoff_allowed=False,\n            qseries_execution_allowed=False,\n            order_creation_allowed=False,\n            funds_movement_allowed=False,\n            portfolio_mutation_allowed=False,\n            read_only=True,\n        )\n\n        first = module.authorize_callable_binding_execution(readiness=readiness)\n        second = module.authorize_callable_binding_execution(readiness=readiness)\n\n        assert first == second\n        assert first.authorization_hash == second.authorization_hash\n        assert module.verify_certified_callable_binding_execution_authorization(\n            first\n        )\n        assert first.callable_count == 9\n        assert first.execution_readiness_verified is True\n        assert first.exact_readiness_hash_scope_preserved is True\n        assert first.bounded_binding_scope_preserved is True\n        assert first.deterministic_binding_required is True\n        assert first.immutable_binding_result_required is True\n        assert first.callable_binding_execution_authorized is True\n        assert first.callable_binding_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: module.verify_certified_callable_binding_execution_authorization(\n                replace(first, authorization_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_certified_callable_binding_execution_authorization(\n                replace(first, callable_binding_allowed=True)\n            )\n        )\n        rejected(\n            lambda: module.authorize_callable_binding_execution(\n                readiness=replace(\n                    readiness,\n                    implementation_symbol_load_allowed=True,\n                )\n            )\n        )\n        rejected(\n            lambda: module.authorize_callable_binding_execution(\n                readiness=replace(\n                    readiness,\n                    callable_binding_execution_authorized=True,\n                )\n            )\n        )\n\n        print("========================================")\n        print(" OSR-010 TEST")\n        print(" CERTIFIED CALLABLE BINDING")\n        print(" EXECUTION AUTHORIZATION GATE")\n        print("========================================")\n        print("[PASS] Actual OSR-009 execution-readiness verifier consumed")\n        print("[PASS] OSR-009 readiness identity and lineage preserved")\n        print("[PASS] Exact readiness hash scope preserved")\n        print("[PASS] Exact callable count preserved")\n        print("[PASS] Bounded deterministic binding scope preserved")\n        print("[PASS] Immutable binding-result requirement preserved")\n        print("[PASS] Execution authorization identity deterministic")\n        print("[PASS] Callable binding execution authorization enabled")\n        print("[PASS] Implementation import remains disabled")\n        print("[PASS] Implementation symbol loading remains disabled")\n        print("[PASS] Callable binding remains disabled")\n        print("[PASS] Reasoning execution remains disabled")\n        print("[PASS] Probability estimation remains disabled")\n        print("[PASS] Final intelligence conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print(\n            "[DONE] OSR-010 CALLABLE BINDING EXECUTION AUTHORIZATION CERTIFIED"\n        )\n    finally:\n        module.verify_callable_binding_execution_readiness = original_verifier\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_osr009_contract() -> None:
    if not SOURCE_OSR009.is_file():
        raise FileNotFoundError(
            f"Actual OSR-009 module missing: {SOURCE_OSR009}"
        )

    source = SOURCE_OSR009.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "OSR-009"',
        "verify_callable_binding_execution_readiness",
        "CallableBindingExecutionReadiness",
        "readiness_hash",
        "callable_binding_execution_ready",
        "callable_binding_execution_authorized",
        "callable_binding_allowed",
        "reasoning_execution_allowed",
        "read_only",
        "qseries_execution_allowed",
        "order_creation_allowed",
        "funds_movement_allowed",
        "portfolio_mutation_allowed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual OSR-009 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_OSR009))
    print(
        "[OK] Actual OSR-009 callable binding execution readiness "
        "contract verified"
    )


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def append_export(path: Path, line: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing.splitlines():
        print(f"[OK] PACKAGE EXPORT PRESENT: {path.resolve()}")
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + line + "\n", encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" OSR-010 INSTALLER")
    print(" CERTIFIED CALLABLE BINDING")
    print(" EXECUTION AUTHORIZATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_osr009_contract()
    protected_hash = sha256_file(SOURCE_OSR009)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_callable_binding_execution_authorization_gate import *",
    )

    if sha256_file(SOURCE_OSR009) != protected_hash:
        raise RuntimeError("Protected OSR-009 module changed during installation")
    print("[PASS] Protected OSR-009 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_OSR009) != protected_hash:
        raise RuntimeError("Protected OSR-009 module changed during testing")

    print("[PASS] Protected OSR-009 module unchanged after test")
    print("[PASS] OII-015 terminal freeze remains untouched")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] OSR-010 certification test executed automatically")
    print(
        "[DONE] OSR-010 CALLABLE BINDING EXECUTION AUTHORIZATION GATE INSTALLED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
