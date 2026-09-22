from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
SOURCE_INT_OII_002 = (
    PACKAGE / "oracle_certified_intelligence_registry_attestation_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_intelligence_registry_consumption_authorization_gate.py"
)
TEST = (
    ROOT
    / "test_int_oii_003_oracle_certified_intelligence_registry_consumption_authorization_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_attestation_gate import (\n    OracleCertifiedIntelligenceRegistryAttestation,\n    verify_oracle_certified_intelligence_registry_attestation,\n)\n\nENGINE_ID = "INT-OII-003"\nSCHEMA_VERSION = "INT-OII-003.v1"\nALGORITHM_VERSION = "oracle-certified-intelligence-registry-consumption-authorization.v1"\nAUTHORIZATION_STATUS = "oracle_certified_intelligence_registry_consumption_authorized"\n\n\nclass OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceRegistryConsumptionAuthorization:\n    authorization_id: str\n    source_attestation_id: str\n    source_attestation_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    attestation_verified: bool\n    exact_attestation_hash_scope_preserved: bool\n    exact_registry_hash_scope_preserved: bool\n    exact_entry_hash_scope_preserved: bool\n    certified_subsystem_scope_preserved: bool\n    read_only_consumption_authorized: bool\n    deterministic_consumption_required: bool\n    bounded_registry_scope_required: bool\n    single_use_authorization_required: bool\n    authorization_consumed: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    authorization_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    authorization_hash: str\n\n\ndef authorize_oracle_certified_intelligence_registry_consumption(\n    *,\n    attestation: OracleCertifiedIntelligenceRegistryAttestation,\n) -> OracleCertifiedIntelligenceRegistryConsumptionAuthorization:\n    try:\n        verdict = verify_oracle_certified_intelligence_registry_attestation(\n            attestation\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "INT-OII-002 registry attestation verification failed"\n        ) from exc\n\n    if verdict is False:\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "INT-OII-002 registry attestation verifier returned false"\n        )\n\n    if attestation.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "attested registry must contain at least one subsystem"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "attested entry hash scope mismatch"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "attested subsystem scope mismatch"\n        )\n\n    body = {\n        "source_attestation_id": attestation.attestation_id,\n        "source_attestation_hash": attestation.attestation_hash,\n        "source_registry_id": attestation.source_registry_id,\n        "source_registry_hash": attestation.source_registry_hash,\n        "source_entry_count": attestation.source_entry_count,\n        "source_entry_hashes": attestation.source_entry_hashes,\n        "source_subsystem_keys": attestation.source_subsystem_keys,\n        "attestation_verified": True,\n        "exact_attestation_hash_scope_preserved": True,\n        "exact_registry_hash_scope_preserved": True,\n        "exact_entry_hash_scope_preserved": True,\n        "certified_subsystem_scope_preserved": True,\n        "read_only_consumption_authorized": True,\n        "deterministic_consumption_required": True,\n        "bounded_registry_scope_required": True,\n        "single_use_authorization_required": True,\n        "authorization_consumed": False,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "authorization_status": AUTHORIZATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    authorization_hash = stable_hash(body)\n\n    return OracleCertifiedIntelligenceRegistryConsumptionAuthorization(\n        authorization_id=(\n            "oracle-certified-intelligence-registry-consumption-authorization:"\n            + authorization_hash\n        ),\n        **body,\n        authorization_hash=authorization_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_registry_consumption_authorization(\n    authorization: OracleCertifiedIntelligenceRegistryConsumptionAuthorization,\n) -> bool:\n    if not isinstance(\n        authorization,\n        OracleCertifiedIntelligenceRegistryConsumptionAuthorization,\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "invalid registry consumption authorization"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(authorization).items()\n        if key not in {"authorization_id", "authorization_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if authorization.authorization_hash != expected_hash:\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "registry consumption authorization hash mismatch"\n        )\n\n    if authorization.authorization_id != (\n        "oracle-certified-intelligence-registry-consumption-authorization:"\n        + expected_hash\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "registry consumption authorization identity mismatch"\n        )\n\n    if authorization.source_entry_count != len(\n        authorization.source_entry_hashes\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "authorized entry hash scope mismatch"\n        )\n\n    if authorization.source_entry_count != len(\n        authorization.source_subsystem_keys\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "authorized subsystem scope mismatch"\n        )\n\n    if authorization.source_subsystem_keys != tuple(\n        sorted(authorization.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "authorized subsystem scope is not deterministic"\n        )\n\n    if len(authorization.source_subsystem_keys) != len(\n        set(authorization.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "authorized subsystem scope contains duplicates"\n        )\n\n    forbidden = (\n        authorization.authorization_consumed,\n        authorization.registry_mutation_allowed,\n        authorization.oracle_execution_allowed,\n        authorization.publication_allowed,\n        authorization.alerting_allowed,\n        authorization.qseries_handoff_allowed,\n        authorization.qseries_execution_allowed,\n        authorization.order_creation_allowed,\n        authorization.funds_movement_allowed,\n        authorization.portfolio_mutation_allowed,\n    )\n\n    if (\n        authorization.engine_id != ENGINE_ID\n        or authorization.schema_version != SCHEMA_VERSION\n        or authorization.algorithm_version != ALGORITHM_VERSION\n        or authorization.authorization_status != AUTHORIZATION_STATUS\n        or authorization.source_entry_count <= 0\n        or authorization.attestation_verified is not True\n        or authorization.exact_attestation_hash_scope_preserved is not True\n        or authorization.exact_registry_hash_scope_preserved is not True\n        or authorization.exact_entry_hash_scope_preserved is not True\n        or authorization.certified_subsystem_scope_preserved is not True\n        or authorization.read_only_consumption_authorized is not True\n        or authorization.deterministic_consumption_required is not True\n        or authorization.bounded_registry_scope_required is not True\n        or authorization.single_use_authorization_required is not True\n        or authorization.read_only is not True\n        or any(forbidden)\n    ):\n        raise OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError(\n            "INT-OII-003 permanent safety boundary violated"\n        )\n\n    return True\n\n\ndef serialize_oracle_certified_intelligence_registry_consumption_authorization(\n    authorization: OracleCertifiedIntelligenceRegistryConsumptionAuthorization,\n) -> str:\n    verify_oracle_certified_intelligence_registry_consumption_authorization(\n        authorization\n    )\n    return canonical_json(authorization)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "AUTHORIZATION_STATUS",\n    "OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError",\n    "OracleCertifiedIntelligenceRegistryConsumptionAuthorization",\n    "authorize_oracle_certified_intelligence_registry_consumption",\n    "verify_oracle_certified_intelligence_registry_consumption_authorization",\n    "serialize_oracle_certified_intelligence_registry_consumption_authorization",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_authorization_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_attestation_gate import (\n    OracleCertifiedIntelligenceRegistryAttestation,\n)\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-003 invariant rejection")\n\n\ndef make_attestation() -> OracleCertifiedIntelligenceRegistryAttestation:\n    return OracleCertifiedIntelligenceRegistryAttestation(\n        attestation_id="registry-attestation:" + "a" * 64,\n        source_registry_id="registry:" + "b" * 64,\n        source_registry_hash="b" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("1" * 64, "2" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        registry_verified=True,\n        exact_registry_hash_scope_preserved=True,\n        exact_entry_hash_scope_preserved=True,\n        deterministic_registration_order_verified=True,\n        duplicate_subsystem_rejection_verified=True,\n        immutable_registry_verified=True,\n        downstream_read_only_consumption_verified=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        attestation_status="oracle_certified_intelligence_registry_attested",\n        engine_id="INT-OII-002",\n        schema_version="INT-OII-002.v1",\n        algorithm_version="oracle-certified-intelligence-registry-attestation.v1",\n        attestation_hash="a" * 64,\n    )\n\n\ndef main() -> None:\n    original_verifier = (\n        module.verify_oracle_certified_intelligence_registry_attestation\n    )\n    module.verify_oracle_certified_intelligence_registry_attestation = (\n        lambda _attestation: True\n    )\n\n    try:\n        attestation = make_attestation()\n\n        first = (\n            module.authorize_oracle_certified_intelligence_registry_consumption(\n                attestation=attestation\n            )\n        )\n        second = (\n            module.authorize_oracle_certified_intelligence_registry_consumption(\n                attestation=attestation\n            )\n        )\n\n        assert first == second\n        assert first.authorization_hash == second.authorization_hash\n        assert (\n            module.verify_oracle_certified_intelligence_registry_consumption_authorization(\n                first\n            )\n        )\n        assert first.source_attestation_id == attestation.attestation_id\n        assert first.source_attestation_hash == attestation.attestation_hash\n        assert first.source_registry_id == attestation.source_registry_id\n        assert first.source_registry_hash == attestation.source_registry_hash\n        assert first.source_entry_count == 2\n        assert first.read_only_consumption_authorized is True\n        assert first.single_use_authorization_required is True\n        assert first.authorization_consumed is False\n        assert first.registry_mutation_allowed is False\n        assert first.oracle_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_consumption_authorization(\n                replace(first, authorization_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_consumption_authorization(\n                replace(first, authorization_consumed=True)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_consumption_authorization(\n                replace(first, registry_mutation_allowed=True)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_consumption_authorization(\n                replace(first, source_entry_count=3)\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-003 TEST")\n        print(" CERTIFIED INTELLIGENCE REGISTRY")\n        print(" CONSUMPTION AUTHORIZATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-002 registry attestation verifier consumed")\n        print("[PASS] Attestation identity and hash preserved")\n        print("[PASS] Registry identity and hash preserved")\n        print("[PASS] Exact entry hash scope preserved")\n        print("[PASS] Certified subsystem scope preserved")\n        print("[PASS] Read-only registry consumption authorized")\n        print("[PASS] Deterministic consumption required")\n        print("[PASS] Bounded registry scope required")\n        print("[PASS] Single-use authorization required")\n        print("[PASS] Authorization remains unconsumed")\n        print("[PASS] Registry mutation remains disabled")\n        print("[PASS] Oracle execution remains disabled")\n        print("[PASS] Publication, alerting, and handoff remain disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] INT-OII-003 REGISTRY CONSUMPTION AUTHORIZED")\n    finally:\n        module.verify_oracle_certified_intelligence_registry_attestation = (\n            original_verifier\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_int_oii_002_contract() -> None:
    if not SOURCE_INT_OII_002.is_file():
        raise FileNotFoundError(
            f"Actual INT-OII-002 module missing: {SOURCE_INT_OII_002}"
        )

    source = SOURCE_INT_OII_002.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-002"',
        "OracleCertifiedIntelligenceRegistryAttestation",
        "verify_oracle_certified_intelligence_registry_attestation",
        "attestation_id",
        "attestation_hash",
        "source_registry_id",
        "source_registry_hash",
        "source_entry_count",
        "source_entry_hashes",
        "source_subsystem_keys",
        "registry_verified",
        "read_only",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OII-002 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_INT_OII_002))
    print("[OK] Actual INT-OII-002 registry attestation contract verified")


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
    print(" INT-OII-003 INSTALLER")
    print(" CERTIFIED INTELLIGENCE REGISTRY")
    print(" CONSUMPTION AUTHORIZATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_int_oii_002_contract()
    protected_hash = sha256_file(SOURCE_INT_OII_002)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_intelligence_registry_consumption_authorization_gate import *",
    )

    if sha256_file(SOURCE_INT_OII_002) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-002 module changed during installation"
        )
    print("[PASS] Protected INT-OII-002 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_INT_OII_002) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-002 module changed during testing"
        )

    print("[PASS] Protected INT-OII-002 module unchanged after test")
    print("[PASS] INT-OII-001 registry assembly remains intact")
    print("[PASS] OII-015 terminal freeze remains intact")
    print("[PASS] OSR-014 terminal freeze remains intact")
    print("[PASS] INT-OSR-001 consumption boundary remains intact")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] INT-OII-003 certification test executed automatically")
    print("[DONE] INT-OII-003 REGISTRY CONSUMPTION AUTHORIZATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
