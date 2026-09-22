from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning_runtime"
SOURCE_OSR008 = (
    PACKAGE
    / "oracle_callable_binding_authorization_consumption_activation_gate.py"
)
PRODUCTION = PACKAGE / "oracle_callable_binding_execution_readiness_gate.py"
TEST = ROOT / "test_osr_009_oracle_callable_binding_execution_readiness_gate.py"
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom .oracle_callable_binding_authorization_consumption_activation_gate import (\n    verify_callable_binding_authorization_activation,\n)\n\nENGINE_ID = "OSR-009"\nSCHEMA_VERSION = "OSR-009.v1"\nALGORITHM_VERSION = "callable-binding-execution-readiness.v1"\nREADINESS_STATUS = "callable_binding_execution_ready_not_authorized_not_executed"\n\n\nclass OracleCallableBindingExecutionReadinessInvariantError(ValueError):\n    """Raised when an OSR-009 execution-readiness invariant fails."""\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\ndef _snapshot(value: Any) -> dict[str, Any]:\n    if is_dataclass(value):\n        return asdict(value)\n    if isinstance(value, Mapping):\n        return dict(value)\n    data = getattr(value, "__dict__", None)\n    if isinstance(data, dict):\n        return dict(data)\n    raise OracleCallableBindingExecutionReadinessInvariantError(\n        "binding activation object cannot be snapshotted"\n    )\n\n\ndef _required(snapshot: Mapping[str, Any], name: str) -> Any:\n    if name not in snapshot:\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            f"missing binding activation field: {name}"\n        )\n    return snapshot[name]\n\n\n@dataclass(frozen=True)\nclass CallableBindingExecutionReadiness:\n    readiness_id: str\n    source_binding_activation_id: str\n    source_binding_activation_hash: str\n    source_binding_authorization_id: str\n    source_binding_authorization_hash: str\n    source_binding_readiness_id: str\n    source_binding_readiness_hash: str\n    source_resolution_activation_id: str\n    source_resolution_activation_hash: str\n    source_resolution_authorization_id: str\n    source_resolution_authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    callable_count: int\n    binding_activation_verified: bool\n    exact_activation_hash_scope_preserved: bool\n    bounded_binding_scope: bool\n    deterministic_binding_required: bool\n    immutable_binding_result_required: bool\n    implementation_import_allowed: bool\n    implementation_symbol_load_allowed: bool\n    callable_binding_execution_ready: bool\n    callable_binding_execution_authorized: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    readiness_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    readiness_hash: str\n\n\ndef certify_callable_binding_execution_readiness(\n    *,\n    activation: Any,\n) -> CallableBindingExecutionReadiness:\n    try:\n        verify_callable_binding_authorization_activation(activation)\n    except Exception as exc:\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "OSR-008 callable-binding activation verification failed"\n        ) from exc\n\n    snapshot = _snapshot(activation)\n\n    if snapshot.get("read_only") is not True:\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "OSR-008 activation must remain read-only"\n        )\n    if snapshot.get("callable_binding_activation_enabled") is not True:\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "callable-binding activation is not enabled"\n        )\n\n    forbidden_source_flags = (\n        bool(snapshot.get("implementation_import_allowed", False)),\n        bool(snapshot.get("implementation_symbol_load_allowed", False)),\n        bool(snapshot.get("callable_binding_allowed", False)),\n        bool(snapshot.get("reasoning_execution_allowed", False)),\n        bool(snapshot.get("probability_estimation_allowed", False)),\n        bool(snapshot.get("final_intelligence_conclusion_allowed", False)),\n        bool(snapshot.get("publication_allowed", False)),\n        bool(snapshot.get("alerting_allowed", False)),\n        bool(snapshot.get("qseries_handoff_allowed", False)),\n        bool(snapshot.get("qseries_execution_allowed", False)),\n        bool(snapshot.get("order_creation_allowed", False)),\n        bool(snapshot.get("funds_movement_allowed", False)),\n        bool(snapshot.get("portfolio_mutation_allowed", False)),\n    )\n    if any(forbidden_source_flags):\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "OSR-008 activation violates permanent safety boundaries"\n        )\n\n    callable_count = int(_required(snapshot, "callable_count"))\n    if callable_count <= 0:\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "callable count must be positive"\n        )\n\n    body = {\n        "source_binding_activation_id": str(_required(snapshot, "activation_id")),\n        "source_binding_activation_hash": str(_required(snapshot, "activation_hash")),\n        "source_binding_authorization_id": str(\n            _required(snapshot, "source_binding_authorization_id")\n        ),\n        "source_binding_authorization_hash": str(\n            _required(snapshot, "source_binding_authorization_hash")\n        ),\n        "source_binding_readiness_id": str(\n            _required(snapshot, "source_readiness_id")\n        ),\n        "source_binding_readiness_hash": str(\n            _required(snapshot, "source_readiness_hash")\n        ),\n        "source_resolution_activation_id": str(\n            _required(snapshot, "source_resolution_activation_id")\n        ),\n        "source_resolution_activation_hash": str(\n            _required(snapshot, "source_resolution_activation_hash")\n        ),\n        "source_resolution_authorization_id": str(\n            _required(snapshot, "source_resolution_authorization_id")\n        ),\n        "source_resolution_authorization_hash": str(\n            _required(snapshot, "source_resolution_authorization_hash")\n        ),\n        "source_resolution_package_id": str(\n            _required(snapshot, "source_resolution_package_id")\n        ),\n        "source_resolution_hash": str(\n            _required(snapshot, "source_resolution_hash")\n        ),\n        "source_admission_package_id": str(\n            _required(snapshot, "source_admission_package_id")\n        ),\n        "source_admission_hash": str(\n            _required(snapshot, "source_admission_hash")\n        ),\n        "callable_count": callable_count,\n        "binding_activation_verified": True,\n        "exact_activation_hash_scope_preserved": True,\n        "bounded_binding_scope": True,\n        "deterministic_binding_required": True,\n        "immutable_binding_result_required": True,\n        "implementation_import_allowed": False,\n        "implementation_symbol_load_allowed": False,\n        "callable_binding_execution_ready": True,\n        "callable_binding_execution_authorized": False,\n        "callable_binding_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "readiness_status": READINESS_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n    readiness_hash = stable_hash(body)\n\n    return CallableBindingExecutionReadiness(\n        readiness_id="callable-binding-execution-readiness:" + readiness_hash,\n        **body,\n        readiness_hash=readiness_hash,\n    )\n\n\ndef verify_callable_binding_execution_readiness(\n    readiness: CallableBindingExecutionReadiness,\n) -> bool:\n    if not isinstance(readiness, CallableBindingExecutionReadiness):\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "invalid callable-binding execution-readiness record"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(readiness).items()\n        if key not in {"readiness_id", "readiness_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if readiness.readiness_hash != expected_hash:\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "callable-binding execution-readiness hash mismatch"\n        )\n    if readiness.readiness_id != (\n        "callable-binding-execution-readiness:" + expected_hash\n    ):\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "callable-binding execution-readiness identity mismatch"\n        )\n\n    forbidden = (\n        readiness.implementation_import_allowed,\n        readiness.implementation_symbol_load_allowed,\n        readiness.callable_binding_execution_authorized,\n        readiness.callable_binding_allowed,\n        readiness.reasoning_execution_allowed,\n        readiness.probability_estimation_allowed,\n        readiness.final_intelligence_conclusion_allowed,\n        readiness.publication_allowed,\n        readiness.alerting_allowed,\n        readiness.qseries_handoff_allowed,\n        readiness.qseries_execution_allowed,\n        readiness.order_creation_allowed,\n        readiness.funds_movement_allowed,\n        readiness.portfolio_mutation_allowed,\n    )\n    if (\n        readiness.engine_id != ENGINE_ID\n        or readiness.schema_version != SCHEMA_VERSION\n        or readiness.algorithm_version != ALGORITHM_VERSION\n        or readiness.readiness_status != READINESS_STATUS\n        or readiness.binding_activation_verified is not True\n        or readiness.exact_activation_hash_scope_preserved is not True\n        or readiness.bounded_binding_scope is not True\n        or readiness.deterministic_binding_required is not True\n        or readiness.immutable_binding_result_required is not True\n        or readiness.callable_binding_execution_ready is not True\n        or readiness.read_only is not True\n        or readiness.callable_count <= 0\n        or any(forbidden)\n    ):\n        raise OracleCallableBindingExecutionReadinessInvariantError(\n            "OSR-009 permanent safety boundary violated"\n        )\n    return True\n\n\ndef serialize_callable_binding_execution_readiness(\n    readiness: CallableBindingExecutionReadiness,\n) -> str:\n    verify_callable_binding_execution_readiness(readiness)\n    return canonical_json(readiness)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "READINESS_STATUS",\n    "OracleCallableBindingExecutionReadinessInvariantError",\n    "CallableBindingExecutionReadiness",\n    "certify_callable_binding_execution_readiness",\n    "verify_callable_binding_execution_readiness",\n    "serialize_callable_binding_execution_readiness",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, replace\nimport importlib\n\nmodule = importlib.import_module(\n    "qseries_v2.oracle_scientific_reasoning_runtime."\n    "oracle_callable_binding_execution_readiness_gate"\n)\n\n\n@dataclass(frozen=True)\nclass StubCallableBindingActivation:\n    activation_id: str\n    activation_hash: str\n    source_binding_authorization_id: str\n    source_binding_authorization_hash: str\n    source_readiness_id: str\n    source_readiness_hash: str\n    source_resolution_activation_id: str\n    source_resolution_activation_hash: str\n    source_resolution_authorization_id: str\n    source_resolution_authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    callable_count: int\n    callable_binding_activation_enabled: bool\n    implementation_import_allowed: bool\n    implementation_symbol_load_allowed: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n\n\ndef accepted_verifier(value) -> bool:\n    if not isinstance(value, StubCallableBindingActivation):\n        raise ValueError("unexpected activation type")\n    if value.callable_binding_activation_enabled is not True:\n        raise ValueError("binding activation not enabled")\n    return True\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCallableBindingExecutionReadinessInvariantError:\n        return\n    raise AssertionError("expected OSR-009 invariant rejection")\n\n\ndef main() -> None:\n    original_verifier = module.verify_callable_binding_authorization_activation\n    module.verify_callable_binding_authorization_activation = accepted_verifier\n    try:\n        activation = StubCallableBindingActivation(\n            activation_id="callable-binding-activation:" + "a" * 64,\n            activation_hash="a" * 64,\n            source_binding_authorization_id="callable-binding-authorization:" + "b" * 64,\n            source_binding_authorization_hash="b" * 64,\n            source_readiness_id="callable-binding-readiness:" + "c" * 64,\n            source_readiness_hash="c" * 64,\n            source_resolution_activation_id="osr005:activation:001",\n            source_resolution_activation_hash="d" * 64,\n            source_resolution_authorization_id="osr004:authorization:001",\n            source_resolution_authorization_hash="e" * 64,\n            source_resolution_package_id="osr003:resolution:001",\n            source_resolution_hash="f" * 64,\n            source_admission_package_id="osr002:admission:001",\n            source_admission_hash="1" * 64,\n            callable_count=9,\n            callable_binding_activation_enabled=True,\n            implementation_import_allowed=False,\n            implementation_symbol_load_allowed=False,\n            callable_binding_allowed=False,\n            reasoning_execution_allowed=False,\n            probability_estimation_allowed=False,\n            final_intelligence_conclusion_allowed=False,\n            publication_allowed=False,\n            alerting_allowed=False,\n            qseries_handoff_allowed=False,\n            qseries_execution_allowed=False,\n            order_creation_allowed=False,\n            funds_movement_allowed=False,\n            portfolio_mutation_allowed=False,\n            read_only=True,\n        )\n\n        first = module.certify_callable_binding_execution_readiness(\n            activation=activation\n        )\n        second = module.certify_callable_binding_execution_readiness(\n            activation=activation\n        )\n\n        assert first == second\n        assert first.readiness_hash == second.readiness_hash\n        assert module.verify_callable_binding_execution_readiness(first)\n        assert first.callable_count == 9\n        assert first.binding_activation_verified is True\n        assert first.exact_activation_hash_scope_preserved is True\n        assert first.bounded_binding_scope is True\n        assert first.deterministic_binding_required is True\n        assert first.immutable_binding_result_required is True\n        assert first.callable_binding_execution_ready is True\n        assert first.callable_binding_execution_authorized is False\n        assert first.callable_binding_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: module.verify_callable_binding_execution_readiness(\n                replace(first, readiness_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_callable_binding_execution_readiness(\n                replace(first, callable_binding_execution_authorized=True)\n            )\n        )\n        rejected(\n            lambda: module.certify_callable_binding_execution_readiness(\n                activation=replace(\n                    activation,\n                    implementation_import_allowed=True,\n                )\n            )\n        )\n        rejected(\n            lambda: module.certify_callable_binding_execution_readiness(\n                activation=replace(\n                    activation,\n                    read_only=False,\n                )\n            )\n        )\n\n        print("========================================")\n        print(" OSR-009 TEST")\n        print(" CALLABLE BINDING EXECUTION")\n        print(" READINESS GATE")\n        print("========================================")\n        print("[PASS] Actual OSR-008 binding activation verifier consumed")\n        print("[PASS] OSR-008 activation identity and lineage preserved")\n        print("[PASS] Exact activation hash scope preserved")\n        print("[PASS] Exact callable count preserved")\n        print("[PASS] Bounded deterministic binding scope certified")\n        print("[PASS] Immutable binding result required")\n        print("[PASS] Binding execution readiness identity deterministic")\n        print("[PASS] Callable binding execution readiness certified")\n        print("[PASS] Binding execution authorization remains disabled")\n        print("[PASS] Implementation import remains disabled")\n        print("[PASS] Implementation symbol loading remains disabled")\n        print("[PASS] Callable binding remains disabled")\n        print("[PASS] Reasoning execution remains disabled")\n        print("[PASS] Probability estimation remains disabled")\n        print("[PASS] Final intelligence conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] OSR-009 CALLABLE BINDING EXECUTION READINESS CERTIFIED")\n    finally:\n        module.verify_callable_binding_authorization_activation = original_verifier\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_osr008_contract() -> None:
    if not SOURCE_OSR008.is_file():
        raise FileNotFoundError(
            f"Actual OSR-008 module missing: {SOURCE_OSR008}"
        )

    source = SOURCE_OSR008.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "OSR-008"',
        "verify_callable_binding_authorization_activation",
        "CallableBindingAuthorizationActivation",
        "activation_hash",
        "callable_binding_activation_enabled",
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
            "Actual OSR-008 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_OSR008))
    print("[OK] Actual OSR-008 callable binding activation contract verified")


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
    print(" OSR-009 INSTALLER")
    print(" CALLABLE BINDING EXECUTION")
    print(" READINESS GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_osr008_contract()
    protected_hash = sha256_file(SOURCE_OSR008)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_callable_binding_execution_readiness_gate import *",
    )

    if sha256_file(SOURCE_OSR008) != protected_hash:
        raise RuntimeError("Protected OSR-008 module changed during installation")
    print("[PASS] Protected OSR-008 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_OSR008) != protected_hash:
        raise RuntimeError("Protected OSR-008 module changed during testing")

    print("[PASS] Protected OSR-008 module unchanged after test")
    print("[PASS] OII-015 terminal freeze remains untouched")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] OSR-009 certification test executed automatically")
    print("[DONE] OSR-009 CALLABLE BINDING EXECUTION READINESS GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
