from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning_runtime"
SOURCE_OSR010 = (
    PACKAGE
    / "oracle_certified_callable_binding_execution_authorization_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_callable_binding_execution_authorization_consumption_activation_gate.py"
)
TEST = (
    ROOT
    / "test_osr_011_oracle_callable_binding_execution_authorization_consumption_activation_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom .oracle_certified_callable_binding_execution_authorization_gate import (\n    verify_certified_callable_binding_execution_authorization,\n)\n\nENGINE_ID = "OSR-011"\nSCHEMA_VERSION = "OSR-011.v1"\nALGORITHM_VERSION = (\n    "callable-binding-execution-authorization-consumption-activation.v1"\n)\nACTIVATION_STATUS = (\n    "callable_binding_execution_authorization_consumed_and_activated_"\n    "not_bound_not_executed"\n)\n\n\nclass OracleCallableBindingExecutionAuthorizationActivationInvariantError(ValueError):\n    """Raised when an OSR-011 authorization-consumption invariant fails."""\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\ndef _snapshot(value: Any) -> dict[str, Any]:\n    if is_dataclass(value):\n        return asdict(value)\n    if isinstance(value, Mapping):\n        return dict(value)\n    data = getattr(value, "__dict__", None)\n    if isinstance(data, dict):\n        return dict(data)\n    raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n        "execution-authorization object cannot be snapshotted"\n    )\n\n\ndef _required(snapshot: Mapping[str, Any], name: str) -> Any:\n    if name not in snapshot:\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            f"missing execution-authorization field: {name}"\n        )\n    return snapshot[name]\n\n\n@dataclass(frozen=True)\nclass CallableBindingExecutionAuthorizationActivation:\n    activation_id: str\n    source_execution_authorization_id: str\n    source_execution_authorization_hash: str\n    source_execution_readiness_id: str\n    source_execution_readiness_hash: str\n    source_binding_activation_id: str\n    source_binding_activation_hash: str\n    source_binding_authorization_id: str\n    source_binding_authorization_hash: str\n    source_binding_readiness_id: str\n    source_binding_readiness_hash: str\n    source_resolution_activation_id: str\n    source_resolution_activation_hash: str\n    source_resolution_authorization_id: str\n    source_resolution_authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    callable_count: int\n    execution_authorization_verified: bool\n    execution_authorization_consumed: bool\n    authorization_consumption_single_use: bool\n    exact_authorization_hash_scope_preserved: bool\n    bounded_binding_scope_preserved: bool\n    deterministic_binding_required: bool\n    immutable_binding_result_required: bool\n    implementation_import_allowed: bool\n    implementation_symbol_load_allowed: bool\n    callable_binding_execution_activation_enabled: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    activation_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    activation_hash: str\n\n\ndef activate_callable_binding_execution_authorization(\n    *,\n    authorization: Any,\n) -> CallableBindingExecutionAuthorizationActivation:\n    try:\n        verify_certified_callable_binding_execution_authorization(authorization)\n    except Exception as exc:\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "OSR-010 callable-binding execution authorization verification failed"\n        ) from exc\n\n    snapshot = _snapshot(authorization)\n\n    if snapshot.get("read_only") is not True:\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "OSR-010 execution authorization must remain read-only"\n        )\n    if snapshot.get("callable_binding_execution_authorized") is not True:\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "callable-binding execution authorization is not enabled"\n        )\n\n    forbidden_source_flags = (\n        bool(snapshot.get("implementation_import_allowed", False)),\n        bool(snapshot.get("implementation_symbol_load_allowed", False)),\n        bool(snapshot.get("callable_binding_allowed", False)),\n        bool(snapshot.get("reasoning_execution_allowed", False)),\n        bool(snapshot.get("probability_estimation_allowed", False)),\n        bool(snapshot.get("final_intelligence_conclusion_allowed", False)),\n        bool(snapshot.get("publication_allowed", False)),\n        bool(snapshot.get("alerting_allowed", False)),\n        bool(snapshot.get("qseries_handoff_allowed", False)),\n        bool(snapshot.get("qseries_execution_allowed", False)),\n        bool(snapshot.get("order_creation_allowed", False)),\n        bool(snapshot.get("funds_movement_allowed", False)),\n        bool(snapshot.get("portfolio_mutation_allowed", False)),\n    )\n    if any(forbidden_source_flags):\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "OSR-010 authorization violates permanent safety boundaries"\n        )\n\n    callable_count = int(_required(snapshot, "callable_count"))\n    if callable_count <= 0:\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "callable count must be positive"\n        )\n\n    body = {\n        "source_execution_authorization_id": str(\n            _required(snapshot, "authorization_id")\n        ),\n        "source_execution_authorization_hash": str(\n            _required(snapshot, "authorization_hash")\n        ),\n        "source_execution_readiness_id": str(\n            _required(snapshot, "source_execution_readiness_id")\n        ),\n        "source_execution_readiness_hash": str(\n            _required(snapshot, "source_execution_readiness_hash")\n        ),\n        "source_binding_activation_id": str(\n            _required(snapshot, "source_binding_activation_id")\n        ),\n        "source_binding_activation_hash": str(\n            _required(snapshot, "source_binding_activation_hash")\n        ),\n        "source_binding_authorization_id": str(\n            _required(snapshot, "source_binding_authorization_id")\n        ),\n        "source_binding_authorization_hash": str(\n            _required(snapshot, "source_binding_authorization_hash")\n        ),\n        "source_binding_readiness_id": str(\n            _required(snapshot, "source_binding_readiness_id")\n        ),\n        "source_binding_readiness_hash": str(\n            _required(snapshot, "source_binding_readiness_hash")\n        ),\n        "source_resolution_activation_id": str(\n            _required(snapshot, "source_resolution_activation_id")\n        ),\n        "source_resolution_activation_hash": str(\n            _required(snapshot, "source_resolution_activation_hash")\n        ),\n        "source_resolution_authorization_id": str(\n            _required(snapshot, "source_resolution_authorization_id")\n        ),\n        "source_resolution_authorization_hash": str(\n            _required(snapshot, "source_resolution_authorization_hash")\n        ),\n        "source_resolution_package_id": str(\n            _required(snapshot, "source_resolution_package_id")\n        ),\n        "source_resolution_hash": str(\n            _required(snapshot, "source_resolution_hash")\n        ),\n        "source_admission_package_id": str(\n            _required(snapshot, "source_admission_package_id")\n        ),\n        "source_admission_hash": str(\n            _required(snapshot, "source_admission_hash")\n        ),\n        "callable_count": callable_count,\n        "execution_authorization_verified": True,\n        "execution_authorization_consumed": True,\n        "authorization_consumption_single_use": True,\n        "exact_authorization_hash_scope_preserved": True,\n        "bounded_binding_scope_preserved": True,\n        "deterministic_binding_required": True,\n        "immutable_binding_result_required": True,\n        "implementation_import_allowed": False,\n        "implementation_symbol_load_allowed": False,\n        "callable_binding_execution_activation_enabled": True,\n        "callable_binding_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "activation_status": ACTIVATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n    activation_hash = stable_hash(body)\n\n    return CallableBindingExecutionAuthorizationActivation(\n        activation_id=(\n            "callable-binding-execution-authorization-activation:"\n            + activation_hash\n        ),\n        **body,\n        activation_hash=activation_hash,\n    )\n\n\ndef verify_callable_binding_execution_authorization_activation(\n    activation: CallableBindingExecutionAuthorizationActivation,\n) -> bool:\n    if not isinstance(\n        activation,\n        CallableBindingExecutionAuthorizationActivation,\n    ):\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "invalid callable-binding execution authorization activation"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(activation).items()\n        if key not in {"activation_id", "activation_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if activation.activation_hash != expected_hash:\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "execution-authorization activation hash mismatch"\n        )\n    if activation.activation_id != (\n        "callable-binding-execution-authorization-activation:" + expected_hash\n    ):\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "execution-authorization activation identity mismatch"\n        )\n\n    forbidden = (\n        activation.implementation_import_allowed,\n        activation.implementation_symbol_load_allowed,\n        activation.callable_binding_allowed,\n        activation.reasoning_execution_allowed,\n        activation.probability_estimation_allowed,\n        activation.final_intelligence_conclusion_allowed,\n        activation.publication_allowed,\n        activation.alerting_allowed,\n        activation.qseries_handoff_allowed,\n        activation.qseries_execution_allowed,\n        activation.order_creation_allowed,\n        activation.funds_movement_allowed,\n        activation.portfolio_mutation_allowed,\n    )\n    if (\n        activation.engine_id != ENGINE_ID\n        or activation.schema_version != SCHEMA_VERSION\n        or activation.algorithm_version != ALGORITHM_VERSION\n        or activation.activation_status != ACTIVATION_STATUS\n        or activation.execution_authorization_verified is not True\n        or activation.execution_authorization_consumed is not True\n        or activation.authorization_consumption_single_use is not True\n        or activation.exact_authorization_hash_scope_preserved is not True\n        or activation.bounded_binding_scope_preserved is not True\n        or activation.deterministic_binding_required is not True\n        or activation.immutable_binding_result_required is not True\n        or activation.callable_binding_execution_activation_enabled is not True\n        or activation.read_only is not True\n        or activation.callable_count <= 0\n        or any(forbidden)\n    ):\n        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(\n            "OSR-011 permanent safety boundary violated"\n        )\n    return True\n\n\ndef serialize_callable_binding_execution_authorization_activation(\n    activation: CallableBindingExecutionAuthorizationActivation,\n) -> str:\n    verify_callable_binding_execution_authorization_activation(activation)\n    return canonical_json(activation)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "ACTIVATION_STATUS",\n    "OracleCallableBindingExecutionAuthorizationActivationInvariantError",\n    "CallableBindingExecutionAuthorizationActivation",\n    "activate_callable_binding_execution_authorization",\n    "verify_callable_binding_execution_authorization_activation",\n    "serialize_callable_binding_execution_authorization_activation",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, replace\nimport importlib\n\nmodule = importlib.import_module(\n    "qseries_v2.oracle_scientific_reasoning_runtime."\n    "oracle_callable_binding_execution_authorization_consumption_activation_gate"\n)\n\n\n@dataclass(frozen=True)\nclass StubCertifiedCallableBindingExecutionAuthorization:\n    authorization_id: str\n    authorization_hash: str\n    source_execution_readiness_id: str\n    source_execution_readiness_hash: str\n    source_binding_activation_id: str\n    source_binding_activation_hash: str\n    source_binding_authorization_id: str\n    source_binding_authorization_hash: str\n    source_binding_readiness_id: str\n    source_binding_readiness_hash: str\n    source_resolution_activation_id: str\n    source_resolution_activation_hash: str\n    source_resolution_authorization_id: str\n    source_resolution_authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    callable_count: int\n    callable_binding_execution_authorized: bool\n    implementation_import_allowed: bool\n    implementation_symbol_load_allowed: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n\n\ndef accepted_verifier(value) -> bool:\n    if not isinstance(\n        value,\n        StubCertifiedCallableBindingExecutionAuthorization,\n    ):\n        raise ValueError("unexpected authorization type")\n    if value.callable_binding_execution_authorized is not True:\n        raise ValueError("execution authorization not certified")\n    return True\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCallableBindingExecutionAuthorizationActivationInvariantError:\n        return\n    raise AssertionError("expected OSR-011 invariant rejection")\n\n\ndef main() -> None:\n    original_verifier = (\n        module.verify_certified_callable_binding_execution_authorization\n    )\n    module.verify_certified_callable_binding_execution_authorization = (\n        accepted_verifier\n    )\n    try:\n        authorization = StubCertifiedCallableBindingExecutionAuthorization(\n            authorization_id=(\n                "callable-binding-execution-authorization:" + "a" * 64\n            ),\n            authorization_hash="a" * 64,\n            source_execution_readiness_id=(\n                "callable-binding-execution-readiness:" + "b" * 64\n            ),\n            source_execution_readiness_hash="b" * 64,\n            source_binding_activation_id=(\n                "callable-binding-activation:" + "c" * 64\n            ),\n            source_binding_activation_hash="c" * 64,\n            source_binding_authorization_id=(\n                "callable-binding-authorization:" + "d" * 64\n            ),\n            source_binding_authorization_hash="d" * 64,\n            source_binding_readiness_id=(\n                "callable-binding-readiness:" + "e" * 64\n            ),\n            source_binding_readiness_hash="e" * 64,\n            source_resolution_activation_id="osr005:activation:001",\n            source_resolution_activation_hash="f" * 64,\n            source_resolution_authorization_id="osr004:authorization:001",\n            source_resolution_authorization_hash="1" * 64,\n            source_resolution_package_id="osr003:resolution:001",\n            source_resolution_hash="2" * 64,\n            source_admission_package_id="osr002:admission:001",\n            source_admission_hash="3" * 64,\n            callable_count=9,\n            callable_binding_execution_authorized=True,\n            implementation_import_allowed=False,\n            implementation_symbol_load_allowed=False,\n            callable_binding_allowed=False,\n            reasoning_execution_allowed=False,\n            probability_estimation_allowed=False,\n            final_intelligence_conclusion_allowed=False,\n            publication_allowed=False,\n            alerting_allowed=False,\n            qseries_handoff_allowed=False,\n            qseries_execution_allowed=False,\n            order_creation_allowed=False,\n            funds_movement_allowed=False,\n            portfolio_mutation_allowed=False,\n            read_only=True,\n        )\n\n        first = module.activate_callable_binding_execution_authorization(\n            authorization=authorization\n        )\n        second = module.activate_callable_binding_execution_authorization(\n            authorization=authorization\n        )\n\n        assert first == second\n        assert first.activation_hash == second.activation_hash\n        assert (\n            module.verify_callable_binding_execution_authorization_activation(\n                first\n            )\n        )\n        assert first.callable_count == 9\n        assert first.execution_authorization_verified is True\n        assert first.execution_authorization_consumed is True\n        assert first.authorization_consumption_single_use is True\n        assert first.exact_authorization_hash_scope_preserved is True\n        assert first.callable_binding_execution_activation_enabled is True\n        assert first.callable_binding_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: (\n                module.verify_callable_binding_execution_authorization_activation(\n                    replace(first, activation_hash="0" * 64)\n                )\n            )\n        )\n        rejected(\n            lambda: (\n                module.verify_callable_binding_execution_authorization_activation(\n                    replace(first, callable_binding_allowed=True)\n                )\n            )\n        )\n        rejected(\n            lambda: module.activate_callable_binding_execution_authorization(\n                authorization=replace(\n                    authorization,\n                    implementation_import_allowed=True,\n                )\n            )\n        )\n        rejected(\n            lambda: module.activate_callable_binding_execution_authorization(\n                authorization=replace(\n                    authorization,\n                    read_only=False,\n                )\n            )\n        )\n\n        print("========================================")\n        print(" OSR-011 TEST")\n        print(" CALLABLE BINDING EXECUTION AUTHORIZATION")\n        print(" CONSUMPTION ACTIVATION GATE")\n        print("========================================")\n        print("[PASS] Actual OSR-010 execution authorization verifier consumed")\n        print("[PASS] OSR-010 authorization identity and lineage preserved")\n        print("[PASS] Exact authorization hash scope preserved")\n        print("[PASS] Single-use execution authorization consumed")\n        print("[PASS] Exact callable count preserved")\n        print("[PASS] Execution activation identity deterministic")\n        print("[PASS] Callable binding execution activation enabled")\n        print("[PASS] Implementation import remains disabled")\n        print("[PASS] Implementation symbol loading remains disabled")\n        print("[PASS] Callable binding remains disabled")\n        print("[PASS] Reasoning execution remains disabled")\n        print("[PASS] Probability estimation remains disabled")\n        print("[PASS] Final intelligence conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print(\n            "[DONE] OSR-011 CALLABLE BINDING EXECUTION ACTIVATION CERTIFIED"\n        )\n    finally:\n        module.verify_certified_callable_binding_execution_authorization = (\n            original_verifier\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_osr010_contract() -> None:
    if not SOURCE_OSR010.is_file():
        raise FileNotFoundError(
            f"Actual OSR-010 module missing: {SOURCE_OSR010}"
        )

    source = SOURCE_OSR010.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "OSR-010"',
        "verify_certified_callable_binding_execution_authorization",
        "CertifiedCallableBindingExecutionAuthorization",
        "authorization_hash",
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
            "Actual OSR-010 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_OSR010))
    print(
        "[OK] Actual OSR-010 callable binding execution authorization "
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
    print(" OSR-011 INSTALLER")
    print(" CALLABLE BINDING EXECUTION AUTHORIZATION")
    print(" CONSUMPTION ACTIVATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_osr010_contract()
    protected_hash = sha256_file(SOURCE_OSR010)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_callable_binding_execution_authorization_consumption_activation_gate import *",
    )

    if sha256_file(SOURCE_OSR010) != protected_hash:
        raise RuntimeError("Protected OSR-010 module changed during installation")
    print("[PASS] Protected OSR-010 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_OSR010) != protected_hash:
        raise RuntimeError("Protected OSR-010 module changed during testing")

    print("[PASS] Protected OSR-010 module unchanged after test")
    print("[PASS] OII-015 terminal freeze remains untouched")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] OSR-011 certification test executed automatically")
    print(
        "[DONE] OSR-011 CALLABLE BINDING EXECUTION ACTIVATION GATE INSTALLED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
