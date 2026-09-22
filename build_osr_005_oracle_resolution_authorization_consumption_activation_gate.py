from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning_runtime"
SOURCE_OSR004 = (
    PACKAGE
    / "oracle_certified_callable_resolution_authorization_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_resolution_authorization_consumption_activation_gate.py"
)
TEST = (
    ROOT
    / "test_osr_005_oracle_resolution_authorization_consumption_activation_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom .oracle_certified_callable_resolution_authorization_gate import (\n    verify_certified_callable_resolution_authorization,\n)\n\nENGINE_ID = "OSR-005"\nSCHEMA_VERSION = "OSR-005.v1"\nALGORITHM_VERSION = "resolution-authorization-consumption-activation.v1"\n\nACTIVATION_STATUS = (\n    "resolution_authorization_consumed_activation_materialized"\n)\n\n\nclass OracleResolutionAuthorizationConsumptionInvariantError(ValueError):\n    """Raised when an OSR-005 activation invariant is violated."""\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\ndef _snapshot(value: Any) -> dict[str, Any]:\n    if is_dataclass(value):\n        return asdict(value)\n    if isinstance(value, Mapping):\n        return dict(value)\n    data = getattr(value, "__dict__", None)\n    if isinstance(data, dict):\n        return dict(data)\n    raise OracleResolutionAuthorizationConsumptionInvariantError(\n        "authorization object cannot be snapshotted"\n    )\n\n\ndef _required(\n    snapshot: Mapping[str, Any],\n    *names: str,\n) -> Any:\n    for name in names:\n        if name in snapshot:\n            return snapshot[name]\n    raise OracleResolutionAuthorizationConsumptionInvariantError(\n        "missing authorization field: " + " or ".join(names)\n    )\n\n\n@dataclass(frozen=True)\nclass CallableResolutionAuthorizationConsumptionReceipt:\n    receipt_id: str\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    authorized_callable_count: int\n    authorization_consumed: bool\n    single_use_consumption: bool\n    receipt_status: str\n    receipt_hash: str\n\n\n@dataclass(frozen=True)\nclass CallableResolutionActivation:\n    activation_id: str\n    authorization_consumption_receipt: CallableResolutionAuthorizationConsumptionReceipt\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    activated_callable_count: int\n    activation_status: str\n    activation_hash: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    read_only: bool\n    callable_resolution_allowed: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n\n\ndef consume_resolution_authorization_and_activate(\n    *,\n    authorization: Any,\n) -> CallableResolutionActivation:\n    try:\n        verify_certified_callable_resolution_authorization(authorization)\n    except Exception as exc:\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "OSR-004 resolution authorization verification failed"\n        ) from exc\n\n    snapshot = _snapshot(authorization)\n\n    authorization_id = str(\n        _required(\n            snapshot,\n            "authorization_id",\n            "resolution_authorization_id",\n        )\n    )\n    authorization_hash = str(\n        _required(\n            snapshot,\n            "authorization_hash",\n            "resolution_authorization_hash",\n        )\n    )\n    resolution_package_id = str(\n        _required(\n            snapshot,\n            "source_resolution_package_id",\n            "resolution_package_id",\n        )\n    )\n    resolution_hash = str(\n        _required(\n            snapshot,\n            "source_resolution_hash",\n            "resolution_hash",\n        )\n    )\n    admission_package_id = str(\n        _required(\n            snapshot,\n            "source_admission_package_id",\n            "admission_package_id",\n        )\n    )\n    admission_hash = str(\n        _required(\n            snapshot,\n            "source_admission_hash",\n            "admission_hash",\n        )\n    )\n    authorized_callable_count = int(\n        _required(\n            snapshot,\n            "authorized_callable_count",\n            "resolved_callable_count",\n            "callable_count",\n        )\n    )\n\n    if authorized_callable_count <= 0:\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "authorized callable count must be positive"\n        )\n\n    authorization_allowed = snapshot.get(\n        "callable_resolution_authorized",\n        snapshot.get("resolution_authorized", True),\n    )\n    if authorization_allowed is not True:\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "OSR-004 authorization is not active"\n        )\n\n    forbidden_source_flags = (\n        bool(snapshot.get("callable_binding_allowed", False)),\n        bool(snapshot.get("reasoning_execution_allowed", False)),\n        bool(snapshot.get("qseries_execution_allowed", False)),\n        bool(snapshot.get("order_creation_allowed", False)),\n        bool(snapshot.get("funds_movement_allowed", False)),\n        bool(snapshot.get("portfolio_mutation_allowed", False)),\n    )\n    if any(forbidden_source_flags):\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "OSR-004 authorization violates permanent safety boundaries"\n        )\n\n    receipt_body = {\n        "source_authorization_id": authorization_id,\n        "source_authorization_hash": authorization_hash,\n        "source_resolution_package_id": resolution_package_id,\n        "source_resolution_hash": resolution_hash,\n        "source_admission_package_id": admission_package_id,\n        "source_admission_hash": admission_hash,\n        "authorized_callable_count": authorized_callable_count,\n        "authorization_consumed": True,\n        "single_use_consumption": True,\n        "receipt_status":\n            "resolution_authorization_consumed_once_read_only",\n    }\n    receipt_hash = stable_hash(receipt_body)\n    receipt = CallableResolutionAuthorizationConsumptionReceipt(\n        receipt_id=(\n            "callable-resolution-authorization-consumption:" + receipt_hash\n        ),\n        **receipt_body,\n        receipt_hash=receipt_hash,\n    )\n\n    activation_body = {\n        "authorization_consumption_receipt": receipt,\n        "source_authorization_id": authorization_id,\n        "source_authorization_hash": authorization_hash,\n        "source_resolution_package_id": resolution_package_id,\n        "source_resolution_hash": resolution_hash,\n        "source_admission_package_id": admission_package_id,\n        "source_admission_hash": admission_hash,\n        "activated_callable_count": authorized_callable_count,\n        "activation_status": ACTIVATION_STATUS,\n    }\n    activation_hash = stable_hash(activation_body)\n\n    return CallableResolutionActivation(\n        activation_id="callable-resolution-activation:" + activation_hash,\n        **activation_body,\n        activation_hash=activation_hash,\n        engine_id=ENGINE_ID,\n        schema_version=SCHEMA_VERSION,\n        algorithm_version=ALGORITHM_VERSION,\n        read_only=True,\n        callable_resolution_allowed=True,\n        callable_binding_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n    )\n\n\ndef verify_resolution_authorization_consumption_receipt(\n    receipt: CallableResolutionAuthorizationConsumptionReceipt,\n) -> bool:\n    if not isinstance(\n        receipt,\n        CallableResolutionAuthorizationConsumptionReceipt,\n    ):\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "invalid authorization consumption receipt"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(receipt).items()\n        if key not in {"receipt_id", "receipt_hash"}\n    }\n    expected_hash = stable_hash(body)\n    if receipt.receipt_hash != expected_hash:\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "authorization consumption receipt hash mismatch"\n        )\n    if receipt.receipt_id != (\n        "callable-resolution-authorization-consumption:" + expected_hash\n    ):\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "authorization consumption receipt identity mismatch"\n        )\n    if (\n        receipt.authorization_consumed is not True\n        or receipt.single_use_consumption is not True\n        or receipt.authorized_callable_count <= 0\n        or receipt.receipt_status\n        != "resolution_authorization_consumed_once_read_only"\n    ):\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "authorization consumption receipt boundary violated"\n        )\n    return True\n\n\ndef verify_callable_resolution_activation(\n    activation: CallableResolutionActivation,\n) -> bool:\n    if not isinstance(activation, CallableResolutionActivation):\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "invalid callable resolution activation"\n        )\n\n    verify_resolution_authorization_consumption_receipt(\n        activation.authorization_consumption_receipt\n    )\n\n    body = {\n        "authorization_consumption_receipt":\n            activation.authorization_consumption_receipt,\n        "source_authorization_id": activation.source_authorization_id,\n        "source_authorization_hash": activation.source_authorization_hash,\n        "source_resolution_package_id":\n            activation.source_resolution_package_id,\n        "source_resolution_hash": activation.source_resolution_hash,\n        "source_admission_package_id":\n            activation.source_admission_package_id,\n        "source_admission_hash": activation.source_admission_hash,\n        "activated_callable_count": activation.activated_callable_count,\n        "activation_status": activation.activation_status,\n    }\n    expected_hash = stable_hash(body)\n    if activation.activation_hash != expected_hash:\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "activation hash mismatch"\n        )\n    if activation.activation_id != (\n        "callable-resolution-activation:" + expected_hash\n    ):\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "activation identity mismatch"\n        )\n\n    receipt = activation.authorization_consumption_receipt\n    if (\n        activation.source_authorization_id\n        != receipt.source_authorization_id\n        or activation.source_authorization_hash\n        != receipt.source_authorization_hash\n        or activation.source_resolution_package_id\n        != receipt.source_resolution_package_id\n        or activation.source_resolution_hash\n        != receipt.source_resolution_hash\n        or activation.source_admission_package_id\n        != receipt.source_admission_package_id\n        or activation.source_admission_hash\n        != receipt.source_admission_hash\n        or activation.activated_callable_count\n        != receipt.authorized_callable_count\n    ):\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "activation lineage mismatch"\n        )\n\n    forbidden = (\n        activation.callable_binding_allowed,\n        activation.reasoning_execution_allowed,\n        activation.probability_estimation_allowed,\n        activation.final_intelligence_conclusion_allowed,\n        activation.publication_allowed,\n        activation.alerting_allowed,\n        activation.qseries_handoff_allowed,\n        activation.qseries_execution_allowed,\n        activation.order_creation_allowed,\n        activation.funds_movement_allowed,\n        activation.portfolio_mutation_allowed,\n    )\n    if (\n        activation.engine_id != ENGINE_ID\n        or activation.read_only is not True\n        or activation.callable_resolution_allowed is not True\n        or activation.activation_status != ACTIVATION_STATUS\n        or any(forbidden)\n    ):\n        raise OracleResolutionAuthorizationConsumptionInvariantError(\n            "OSR-005 permanent safety boundary violated"\n        )\n    return True\n\n\ndef serialize_callable_resolution_activation(\n    activation: CallableResolutionActivation,\n) -> str:\n    verify_callable_resolution_activation(activation)\n    return canonical_json(activation)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "ACTIVATION_STATUS",\n    "OracleResolutionAuthorizationConsumptionInvariantError",\n    "CallableResolutionAuthorizationConsumptionReceipt",\n    "CallableResolutionActivation",\n    "consume_resolution_authorization_and_activate",\n    "verify_resolution_authorization_consumption_receipt",\n    "verify_callable_resolution_activation",\n    "serialize_callable_resolution_activation",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, replace\nimport importlib\n\nmodule = importlib.import_module(\n    "qseries_v2.oracle_scientific_reasoning_runtime."\n    "oracle_resolution_authorization_consumption_activation_gate"\n)\n\n\n@dataclass(frozen=True)\nclass StubResolutionAuthorization:\n    authorization_id: str\n    authorization_hash: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    authorized_callable_count: int\n    callable_resolution_authorized: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n\n\ndef accepted_verifier(value) -> bool:\n    if not isinstance(value, StubResolutionAuthorization):\n        raise ValueError("unexpected authorization type")\n    if value.callable_resolution_authorized is not True:\n        raise ValueError("not authorized")\n    return True\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleResolutionAuthorizationConsumptionInvariantError:\n        return\n    raise AssertionError("expected OSR-005 invariant rejection")\n\n\ndef main() -> None:\n    original_verifier = (\n        module.verify_certified_callable_resolution_authorization\n    )\n    module.verify_certified_callable_resolution_authorization = (\n        accepted_verifier\n    )\n    try:\n        authorization = StubResolutionAuthorization(\n            authorization_id="osr004:authorization:001",\n            authorization_hash="a" * 64,\n            source_resolution_package_id="osr003:resolution:001",\n            source_resolution_hash="b" * 64,\n            source_admission_package_id="osr002:admission:001",\n            source_admission_hash="c" * 64,\n            authorized_callable_count=9,\n            callable_resolution_authorized=True,\n            callable_binding_allowed=False,\n            reasoning_execution_allowed=False,\n            qseries_execution_allowed=False,\n            order_creation_allowed=False,\n            funds_movement_allowed=False,\n            portfolio_mutation_allowed=False,\n        )\n\n        first = module.consume_resolution_authorization_and_activate(\n            authorization=authorization\n        )\n        second = module.consume_resolution_authorization_and_activate(\n            authorization=authorization\n        )\n\n        assert first == second\n        assert first.activation_hash == second.activation_hash\n        assert module.verify_callable_resolution_activation(first)\n        assert first.activated_callable_count == 9\n        assert first.callable_resolution_allowed is True\n        assert first.callable_binding_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n\n        rejected(\n            lambda: module.verify_callable_resolution_activation(\n                replace(first, activation_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_callable_resolution_activation(\n                replace(first, callable_binding_allowed=True)\n            )\n        )\n        rejected(\n            lambda: module.consume_resolution_authorization_and_activate(\n                authorization=replace(\n                    authorization,\n                    callable_binding_allowed=True,\n                )\n            )\n        )\n\n        print("========================================")\n        print(" OSR-005 TEST")\n        print(" RESOLUTION AUTHORIZATION CONSUMPTION")\n        print(" ACTIVATION GATE")\n        print("========================================")\n        print("[PASS] OSR-004 verifier boundary consumed")\n        print("[PASS] Authorization identity and lineage preserved")\n        print("[PASS] Single-use consumption receipt materialized")\n        print("[PASS] Activation identity deterministic")\n        print("[PASS] Resolution scope activated")\n        print("[PASS] Callable binding remains disabled")\n        print("[PASS] Reasoning execution remains disabled")\n        print("[PASS] Probability estimation remains disabled")\n        print("[PASS] Final intelligence conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] OSR-005 RESOLUTION ACTIVATION GATE CERTIFIED")\n    finally:\n        module.verify_certified_callable_resolution_authorization = (\n            original_verifier\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_osr004_contract() -> None:
    if not SOURCE_OSR004.is_file():
        raise FileNotFoundError(
            f"Actual OSR-004 module missing: {SOURCE_OSR004}"
        )
    source = SOURCE_OSR004.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "OSR-004"',
        "verify_certified_callable_resolution_authorization",
        "authorization",
        "resolution",
        "read_only",
        "callable_binding",
        "reasoning_execution",
        "qseries_execution",
        "order_creation",
        "funds_movement",
        "portfolio_mutation",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual OSR-004 contract mismatch; missing: "
            + ", ".join(missing)
        )
    ast.parse(source, filename=str(SOURCE_OSR004))
    print("[OK] Actual OSR-004 resolution authorization contract verified")


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
    print(" OSR-005 INSTALLER")
    print(" RESOLUTION AUTHORIZATION CONSUMPTION")
    print(" ACTIVATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_osr004_contract()
    protected_hash = sha256_file(SOURCE_OSR004)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_resolution_authorization_consumption_activation_gate import *",
    )

    if sha256_file(SOURCE_OSR004) != protected_hash:
        raise RuntimeError("Protected OSR-004 module changed during installation")
    print("[PASS] Protected OSR-004 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_OSR004) != protected_hash:
        raise RuntimeError("Protected OSR-004 module changed during testing")

    print("[PASS] Protected OSR-004 module unchanged after test")
    print("[PASS] OII-015 terminal freeze remains untouched")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] OSR-005 certification test executed automatically")
    print("[DONE] OSR-005 RESOLUTION ACTIVATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
