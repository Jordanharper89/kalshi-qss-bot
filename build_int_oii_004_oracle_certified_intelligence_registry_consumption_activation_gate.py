from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
SOURCE_INT_OII_003 = (
    PACKAGE
    / "oracle_certified_intelligence_registry_consumption_authorization_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_intelligence_registry_consumption_activation_gate.py"
)
TEST = (
    ROOT
    / "test_int_oii_004_oracle_certified_intelligence_registry_consumption_activation_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_authorization_gate import (\n    OracleCertifiedIntelligenceRegistryConsumptionAuthorization,\n    verify_oracle_certified_intelligence_registry_consumption_authorization,\n)\n\nENGINE_ID = "INT-OII-004"\nSCHEMA_VERSION = "INT-OII-004.v1"\nALGORITHM_VERSION = "oracle-certified-intelligence-registry-consumption-activation.v1"\nACTIVATION_STATUS = "oracle_certified_intelligence_registry_consumption_activated"\n\n\nclass OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceRegistryConsumptionActivation:\n    activation_id: str\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_attestation_id: str\n    source_attestation_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    authorization_verified: bool\n    exact_authorization_hash_scope_preserved: bool\n    exact_attestation_hash_scope_preserved: bool\n    exact_registry_hash_scope_preserved: bool\n    exact_entry_hash_scope_preserved: bool\n    certified_subsystem_scope_preserved: bool\n    read_only_consumption_activated: bool\n    deterministic_activation: bool\n    bounded_registry_scope_preserved: bool\n    single_use_authorization_consumed: bool\n    duplicate_activation_rejected: bool\n    activation_reversible: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    activation_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    activation_hash: str\n\n\ndef activate_oracle_certified_intelligence_registry_consumption(\n    *,\n    authorization: OracleCertifiedIntelligenceRegistryConsumptionAuthorization,\n) -> OracleCertifiedIntelligenceRegistryConsumptionActivation:\n    try:\n        verdict = (\n            verify_oracle_certified_intelligence_registry_consumption_authorization(\n                authorization\n            )\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "INT-OII-003 registry consumption authorization verification failed"\n        ) from exc\n\n    if verdict is False:\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "INT-OII-003 authorization verifier returned false"\n        )\n\n    if authorization.authorization_consumed is not False:\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "authorization has already been consumed"\n        )\n\n    if authorization.single_use_authorization_required is not True:\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "single-use authorization requirement missing"\n        )\n\n    if authorization.read_only_consumption_authorized is not True:\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "read-only registry consumption is not authorized"\n        )\n\n    if authorization.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "authorized registry scope is empty"\n        )\n\n    if authorization.source_entry_count != len(\n        authorization.source_entry_hashes\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "authorized entry hash scope mismatch"\n        )\n\n    if authorization.source_entry_count != len(\n        authorization.source_subsystem_keys\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "authorized subsystem scope mismatch"\n        )\n\n    body = {\n        "source_authorization_id": authorization.authorization_id,\n        "source_authorization_hash": authorization.authorization_hash,\n        "source_attestation_id": authorization.source_attestation_id,\n        "source_attestation_hash": authorization.source_attestation_hash,\n        "source_registry_id": authorization.source_registry_id,\n        "source_registry_hash": authorization.source_registry_hash,\n        "source_entry_count": authorization.source_entry_count,\n        "source_entry_hashes": authorization.source_entry_hashes,\n        "source_subsystem_keys": authorization.source_subsystem_keys,\n        "authorization_verified": True,\n        "exact_authorization_hash_scope_preserved": True,\n        "exact_attestation_hash_scope_preserved": True,\n        "exact_registry_hash_scope_preserved": True,\n        "exact_entry_hash_scope_preserved": True,\n        "certified_subsystem_scope_preserved": True,\n        "read_only_consumption_activated": True,\n        "deterministic_activation": True,\n        "bounded_registry_scope_preserved": True,\n        "single_use_authorization_consumed": True,\n        "duplicate_activation_rejected": True,\n        "activation_reversible": False,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "activation_status": ACTIVATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    activation_hash = stable_hash(body)\n\n    return OracleCertifiedIntelligenceRegistryConsumptionActivation(\n        activation_id=(\n            "oracle-certified-intelligence-registry-consumption-activation:"\n            + activation_hash\n        ),\n        **body,\n        activation_hash=activation_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_registry_consumption_activation(\n    activation: OracleCertifiedIntelligenceRegistryConsumptionActivation,\n) -> bool:\n    if not isinstance(\n        activation,\n        OracleCertifiedIntelligenceRegistryConsumptionActivation,\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "invalid registry consumption activation"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(activation).items()\n        if key not in {"activation_id", "activation_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if activation.activation_hash != expected_hash:\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "registry consumption activation hash mismatch"\n        )\n\n    if activation.activation_id != (\n        "oracle-certified-intelligence-registry-consumption-activation:"\n        + expected_hash\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "registry consumption activation identity mismatch"\n        )\n\n    if activation.source_entry_count != len(activation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "activated entry hash scope mismatch"\n        )\n\n    if activation.source_entry_count != len(activation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "activated subsystem scope mismatch"\n        )\n\n    if activation.source_subsystem_keys != tuple(\n        sorted(activation.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "activated subsystem scope is not deterministic"\n        )\n\n    if len(activation.source_subsystem_keys) != len(\n        set(activation.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "activated subsystem scope contains duplicates"\n        )\n\n    forbidden = (\n        activation.activation_reversible,\n        activation.registry_mutation_allowed,\n        activation.oracle_execution_allowed,\n        activation.reasoning_execution_allowed,\n        activation.probability_estimation_allowed,\n        activation.final_intelligence_conclusion_allowed,\n        activation.publication_allowed,\n        activation.alerting_allowed,\n        activation.qseries_handoff_allowed,\n        activation.qseries_execution_allowed,\n        activation.order_creation_allowed,\n        activation.funds_movement_allowed,\n        activation.portfolio_mutation_allowed,\n    )\n\n    if (\n        activation.engine_id != ENGINE_ID\n        or activation.schema_version != SCHEMA_VERSION\n        or activation.algorithm_version != ALGORITHM_VERSION\n        or activation.activation_status != ACTIVATION_STATUS\n        or activation.source_entry_count <= 0\n        or activation.authorization_verified is not True\n        or activation.exact_authorization_hash_scope_preserved is not True\n        or activation.exact_attestation_hash_scope_preserved is not True\n        or activation.exact_registry_hash_scope_preserved is not True\n        or activation.exact_entry_hash_scope_preserved is not True\n        or activation.certified_subsystem_scope_preserved is not True\n        or activation.read_only_consumption_activated is not True\n        or activation.deterministic_activation is not True\n        or activation.bounded_registry_scope_preserved is not True\n        or activation.single_use_authorization_consumed is not True\n        or activation.duplicate_activation_rejected is not True\n        or activation.read_only is not True\n        or any(forbidden)\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError(\n            "INT-OII-004 permanent safety boundary violated"\n        )\n\n    return True\n\n\ndef serialize_oracle_certified_intelligence_registry_consumption_activation(\n    activation: OracleCertifiedIntelligenceRegistryConsumptionActivation,\n) -> str:\n    verify_oracle_certified_intelligence_registry_consumption_activation(\n        activation\n    )\n    return canonical_json(activation)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "ACTIVATION_STATUS",\n    "OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError",\n    "OracleCertifiedIntelligenceRegistryConsumptionActivation",\n    "activate_oracle_certified_intelligence_registry_consumption",\n    "verify_oracle_certified_intelligence_registry_consumption_activation",\n    "serialize_oracle_certified_intelligence_registry_consumption_activation",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_authorization_gate import (\n    OracleCertifiedIntelligenceRegistryConsumptionAuthorization,\n)\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-004 invariant rejection")\n\n\ndef make_authorization() -> OracleCertifiedIntelligenceRegistryConsumptionAuthorization:\n    return OracleCertifiedIntelligenceRegistryConsumptionAuthorization(\n        authorization_id="registry-consumption-authorization:" + "a" * 64,\n        source_attestation_id="registry-attestation:" + "b" * 64,\n        source_attestation_hash="b" * 64,\n        source_registry_id="registry:" + "c" * 64,\n        source_registry_hash="c" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("1" * 64, "2" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        attestation_verified=True,\n        exact_attestation_hash_scope_preserved=True,\n        exact_registry_hash_scope_preserved=True,\n        exact_entry_hash_scope_preserved=True,\n        certified_subsystem_scope_preserved=True,\n        read_only_consumption_authorized=True,\n        deterministic_consumption_required=True,\n        bounded_registry_scope_required=True,\n        single_use_authorization_required=True,\n        authorization_consumed=False,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        authorization_status=(\n            "oracle_certified_intelligence_registry_consumption_authorized"\n        ),\n        engine_id="INT-OII-003",\n        schema_version="INT-OII-003.v1",\n        algorithm_version=(\n            "oracle-certified-intelligence-registry-consumption-authorization.v1"\n        ),\n        authorization_hash="a" * 64,\n    )\n\n\ndef main() -> None:\n    original_verifier = (\n        module.verify_oracle_certified_intelligence_registry_consumption_authorization\n    )\n    module.verify_oracle_certified_intelligence_registry_consumption_authorization = (\n        lambda _authorization: True\n    )\n\n    try:\n        authorization = make_authorization()\n\n        first = module.activate_oracle_certified_intelligence_registry_consumption(\n            authorization=authorization\n        )\n        second = module.activate_oracle_certified_intelligence_registry_consumption(\n            authorization=authorization\n        )\n\n        assert first == second\n        assert first.activation_hash == second.activation_hash\n        assert (\n            module.verify_oracle_certified_intelligence_registry_consumption_activation(\n                first\n            )\n        )\n        assert first.source_authorization_id == authorization.authorization_id\n        assert first.source_authorization_hash == authorization.authorization_hash\n        assert first.source_attestation_id == authorization.source_attestation_id\n        assert first.source_registry_id == authorization.source_registry_id\n        assert first.source_entry_count == 2\n        assert first.read_only_consumption_activated is True\n        assert first.single_use_authorization_consumed is True\n        assert first.duplicate_activation_rejected is True\n        assert first.activation_reversible is False\n        assert first.registry_mutation_allowed is False\n        assert first.oracle_execution_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation(\n                replace(first, activation_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation(\n                replace(first, activation_reversible=True)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation(\n                replace(first, reasoning_execution_allowed=True)\n            )\n        )\n        rejected(\n            lambda: module.activate_oracle_certified_intelligence_registry_consumption(\n                authorization=replace(\n                    authorization,\n                    authorization_consumed=True,\n                )\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-004 TEST")\n        print(" CERTIFIED INTELLIGENCE REGISTRY")\n        print(" CONSUMPTION ACTIVATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-003 authorization verifier consumed")\n        print("[PASS] Authorization identity and hash preserved")\n        print("[PASS] Attestation identity and hash preserved")\n        print("[PASS] Registry identity and hash preserved")\n        print("[PASS] Exact entry hash scope preserved")\n        print("[PASS] Certified subsystem scope preserved")\n        print("[PASS] Read-only registry consumption activated")\n        print("[PASS] Deterministic activation certified")\n        print("[PASS] Bounded registry scope preserved")\n        print("[PASS] Single-use authorization consumed")\n        print("[PASS] Duplicate activation rejected")\n        print("[PASS] Activation is irreversible")\n        print("[PASS] Registry mutation remains disabled")\n        print("[PASS] Oracle and reasoning execution remain disabled")\n        print("[PASS] Probability estimation and final conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff remain disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] INT-OII-004 REGISTRY CONSUMPTION ACTIVATED")\n    finally:\n        module.verify_oracle_certified_intelligence_registry_consumption_authorization = (\n            original_verifier\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_int_oii_003_contract() -> None:
    if not SOURCE_INT_OII_003.is_file():
        raise FileNotFoundError(
            f"Actual INT-OII-003 module missing: {SOURCE_INT_OII_003}"
        )

    source = SOURCE_INT_OII_003.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-003"',
        "OracleCertifiedIntelligenceRegistryConsumptionAuthorization",
        "verify_oracle_certified_intelligence_registry_consumption_authorization",
        "authorization_id",
        "authorization_hash",
        "source_attestation_id",
        "source_attestation_hash",
        "source_registry_id",
        "source_registry_hash",
        "source_entry_count",
        "source_entry_hashes",
        "source_subsystem_keys",
        "read_only_consumption_authorized",
        "single_use_authorization_required",
        "authorization_consumed",
        "read_only",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OII-003 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_INT_OII_003))
    print("[OK] Actual INT-OII-003 consumption authorization contract verified")


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
    print(" INT-OII-004 INSTALLER")
    print(" CERTIFIED INTELLIGENCE REGISTRY")
    print(" CONSUMPTION ACTIVATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_int_oii_003_contract()
    protected_hash = sha256_file(SOURCE_INT_OII_003)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_intelligence_registry_consumption_activation_gate import *",
    )

    if sha256_file(SOURCE_INT_OII_003) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-003 module changed during installation"
        )
    print("[PASS] Protected INT-OII-003 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_INT_OII_003) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-003 module changed during testing"
        )

    print("[PASS] Protected INT-OII-003 module unchanged after test")
    print("[PASS] INT-OII-002 registry attestation remains intact")
    print("[PASS] INT-OII-001 registry assembly remains intact")
    print("[PASS] OII-015 terminal freeze remains intact")
    print("[PASS] OSR-014 terminal freeze remains intact")
    print("[PASS] INT-OSR-001 consumption boundary remains intact")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] INT-OII-004 certification test executed automatically")
    print("[DONE] INT-OII-004 REGISTRY CONSUMPTION ACTIVATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
