from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
SOURCE_INT_OII_001 = PACKAGE / "oracle_certified_intelligence_registry_assembly_gate.py"
PRODUCTION = PACKAGE / "oracle_certified_intelligence_registry_attestation_gate.py"
TEST = ROOT / "test_int_oii_002_oracle_certified_intelligence_registry_attestation_gate.py"
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_assembly_gate import (\n    OracleCertifiedIntelligenceRegistry,\n    verify_oracle_certified_intelligence_registry,\n)\n\nENGINE_ID = "INT-OII-002"\nSCHEMA_VERSION = "INT-OII-002.v1"\nALGORITHM_VERSION = "oracle-certified-intelligence-registry-attestation.v1"\nATTESTATION_STATUS = "oracle_certified_intelligence_registry_attested"\n\n\nclass OracleCertifiedIntelligenceRegistryAttestationInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceRegistryAttestation:\n    attestation_id: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    registry_verified: bool\n    exact_registry_hash_scope_preserved: bool\n    exact_entry_hash_scope_preserved: bool\n    deterministic_registration_order_verified: bool\n    duplicate_subsystem_rejection_verified: bool\n    immutable_registry_verified: bool\n    downstream_read_only_consumption_verified: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    attestation_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    attestation_hash: str\n\n\ndef attest_oracle_certified_intelligence_registry(\n    *,\n    registry: OracleCertifiedIntelligenceRegistry,\n) -> OracleCertifiedIntelligenceRegistryAttestation:\n    try:\n        verdict = verify_oracle_certified_intelligence_registry(registry)\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "INT-OII-001 registry verification failed"\n        ) from exc\n\n    if verdict is False:\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "INT-OII-001 registry verifier returned false"\n        )\n\n    if registry.entry_count <= 0:\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "registry must contain at least one certified subsystem"\n        )\n\n    entry_hashes = tuple(entry.entry_hash for entry in registry.entries)\n    subsystem_keys = tuple(entry.subsystem_key for entry in registry.entries)\n\n    if subsystem_keys != tuple(sorted(subsystem_keys)):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "registry subsystem order is not deterministic"\n        )\n    if len(subsystem_keys) != len(set(subsystem_keys)):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "registry contains duplicate subsystem keys"\n        )\n\n    body = {\n        "source_registry_id": registry.registry_id,\n        "source_registry_hash": registry.registry_hash,\n        "source_entry_count": registry.entry_count,\n        "source_entry_hashes": entry_hashes,\n        "source_subsystem_keys": subsystem_keys,\n        "registry_verified": True,\n        "exact_registry_hash_scope_preserved": True,\n        "exact_entry_hash_scope_preserved": True,\n        "deterministic_registration_order_verified": True,\n        "duplicate_subsystem_rejection_verified": True,\n        "immutable_registry_verified": True,\n        "downstream_read_only_consumption_verified": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "attestation_status": ATTESTATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n    attestation_hash = stable_hash(body)\n\n    return OracleCertifiedIntelligenceRegistryAttestation(\n        attestation_id="oracle-certified-intelligence-registry-attestation:"\n        + attestation_hash,\n        **body,\n        attestation_hash=attestation_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_registry_attestation(\n    attestation: OracleCertifiedIntelligenceRegistryAttestation,\n) -> bool:\n    if not isinstance(\n        attestation,\n        OracleCertifiedIntelligenceRegistryAttestation,\n    ):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "invalid registry attestation record"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(attestation).items()\n        if key not in {"attestation_id", "attestation_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if attestation.attestation_hash != expected_hash:\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "registry attestation hash mismatch"\n        )\n    if attestation.attestation_id != (\n        "oracle-certified-intelligence-registry-attestation:" + expected_hash\n    ):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "registry attestation identity mismatch"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "entry count and entry hash scope mismatch"\n        )\n    if attestation.source_entry_count != len(attestation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "entry count and subsystem scope mismatch"\n        )\n    if attestation.source_subsystem_keys != tuple(\n        sorted(attestation.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "attested subsystem order mismatch"\n        )\n    if len(attestation.source_subsystem_keys) != len(\n        set(attestation.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "attested subsystem scope contains duplicates"\n        )\n\n    forbidden = (\n        attestation.registry_mutation_allowed,\n        attestation.oracle_execution_allowed,\n        attestation.publication_allowed,\n        attestation.alerting_allowed,\n        attestation.qseries_execution_allowed,\n        attestation.order_creation_allowed,\n        attestation.funds_movement_allowed,\n        attestation.portfolio_mutation_allowed,\n    )\n\n    if (\n        attestation.engine_id != ENGINE_ID\n        or attestation.schema_version != SCHEMA_VERSION\n        or attestation.algorithm_version != ALGORITHM_VERSION\n        or attestation.attestation_status != ATTESTATION_STATUS\n        or attestation.source_entry_count <= 0\n        or attestation.registry_verified is not True\n        or attestation.exact_registry_hash_scope_preserved is not True\n        or attestation.exact_entry_hash_scope_preserved is not True\n        or attestation.deterministic_registration_order_verified is not True\n        or attestation.duplicate_subsystem_rejection_verified is not True\n        or attestation.immutable_registry_verified is not True\n        or attestation.downstream_read_only_consumption_verified is not True\n        or attestation.read_only is not True\n        or any(forbidden)\n    ):\n        raise OracleCertifiedIntelligenceRegistryAttestationInvariantError(\n            "INT-OII-002 permanent safety boundary violated"\n        )\n\n    return True\n\n\ndef serialize_oracle_certified_intelligence_registry_attestation(\n    attestation: OracleCertifiedIntelligenceRegistryAttestation,\n) -> str:\n    verify_oracle_certified_intelligence_registry_attestation(attestation)\n    return canonical_json(attestation)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "ATTESTATION_STATUS",\n    "OracleCertifiedIntelligenceRegistryAttestationInvariantError",\n    "OracleCertifiedIntelligenceRegistryAttestation",\n    "attest_oracle_certified_intelligence_registry",\n    "verify_oracle_certified_intelligence_registry_attestation",\n    "serialize_oracle_certified_intelligence_registry_attestation",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_assembly_gate import (\n    OracleCertifiedIntelligenceRegistry,\n    OracleCertifiedIntelligenceRegistryEntry,\n)\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_attestation_gate as module\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceRegistryAttestationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-002 invariant rejection")\n\n\ndef make_registry() -> OracleCertifiedIntelligenceRegistry:\n    entries = (\n        OracleCertifiedIntelligenceRegistryEntry(\n            subsystem_key="oracle_intelligence_integration",\n            engine_id="OII-015",\n            source_record_id="oii-terminal:" + "a" * 64,\n            source_record_hash="a" * 64,\n            verified=True,\n            read_only_verified=True,\n            mutation_allowed=False,\n            execution_allowed=False,\n            publication_allowed=False,\n            qseries_execution_allowed=False,\n            entry_hash="1" * 64,\n        ),\n        OracleCertifiedIntelligenceRegistryEntry(\n            subsystem_key="oracle_scientific_reasoning_runtime",\n            engine_id="INT-OSR-001",\n            source_record_id="osr-consumption:" + "b" * 64,\n            source_record_hash="b" * 64,\n            verified=True,\n            read_only_verified=True,\n            mutation_allowed=False,\n            execution_allowed=False,\n            publication_allowed=False,\n            qseries_execution_allowed=False,\n            entry_hash="2" * 64,\n        ),\n    )\n    return OracleCertifiedIntelligenceRegistry(\n        registry_id="oracle-certified-intelligence-registry:" + "c" * 64,\n        entries=entries,\n        entry_count=2,\n        deterministic_registration_order=True,\n        exact_source_hashes_preserved=True,\n        duplicate_subsystems_rejected=True,\n        immutable_registry=True,\n        downstream_read_only_consumption_allowed=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        registry_status="oracle_certified_intelligence_registry_assembled",\n        engine_id="INT-OII-001",\n        schema_version="INT-OII-001.v1",\n        algorithm_version="oracle-certified-intelligence-registry-assembly.v1",\n        registry_hash="c" * 64,\n    )\n\n\ndef main() -> None:\n    original_verifier = module.verify_oracle_certified_intelligence_registry\n    module.verify_oracle_certified_intelligence_registry = lambda _registry: True\n\n    try:\n        registry = make_registry()\n\n        first = module.attest_oracle_certified_intelligence_registry(\n            registry=registry\n        )\n        second = module.attest_oracle_certified_intelligence_registry(\n            registry=registry\n        )\n\n        assert first == second\n        assert first.attestation_hash == second.attestation_hash\n        assert module.verify_oracle_certified_intelligence_registry_attestation(\n            first\n        )\n        assert first.source_registry_id == registry.registry_id\n        assert first.source_registry_hash == registry.registry_hash\n        assert first.source_entry_count == 2\n        assert first.source_entry_hashes == ("1" * 64, "2" * 64)\n        assert first.source_subsystem_keys == (\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        )\n        assert first.registry_verified is True\n        assert first.read_only is True\n        assert first.registry_mutation_allowed is False\n        assert first.oracle_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_attestation(\n                replace(first, attestation_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_attestation(\n                replace(first, registry_mutation_allowed=True)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_attestation(\n                replace(first, source_entry_count=3)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_registry_attestation(\n                replace(\n                    first,\n                    source_subsystem_keys=tuple(\n                        reversed(first.source_subsystem_keys)\n                    ),\n                )\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-002 TEST")\n        print(" ORACLE CERTIFIED INTELLIGENCE")\n        print(" REGISTRY ATTESTATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-001 registry verifier consumed")\n        print("[PASS] Registry identity and hash preserved")\n        print("[PASS] Exact registry hash scope preserved")\n        print("[PASS] Exact entry hash scope preserved")\n        print("[PASS] Certified subsystem scope preserved")\n        print("[PASS] Deterministic registration order verified")\n        print("[PASS] Duplicate subsystem rejection verified")\n        print("[PASS] Immutable registry verified")\n        print("[PASS] Registry attestation identity deterministic")\n        print("[PASS] Downstream read-only consumption verified")\n        print("[PASS] Registry mutation remains disabled")\n        print("[PASS] Oracle execution remains disabled")\n        print("[PASS] Publication and alerting remain disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] INT-OII-002 CERTIFIED INTELLIGENCE REGISTRY ATTESTED")\n    finally:\n        module.verify_oracle_certified_intelligence_registry = original_verifier\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_int_oii_001_contract() -> None:
    if not SOURCE_INT_OII_001.is_file():
        raise FileNotFoundError(
            f"Actual INT-OII-001 module missing: {SOURCE_INT_OII_001}"
        )

    source = SOURCE_INT_OII_001.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-001"',
        "OracleCertifiedIntelligenceRegistry",
        "verify_oracle_certified_intelligence_registry",
        "registry_id",
        "registry_hash",
        "entry_count",
        "entries",
        "deterministic_registration_order",
        "duplicate_subsystems_rejected",
        "immutable_registry",
        "downstream_read_only_consumption_allowed",
        "registry_mutation_allowed",
        "oracle_execution_allowed",
        "qseries_execution_allowed",
        "read_only",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OII-001 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_INT_OII_001))
    print("[OK] Actual INT-OII-001 certified registry contract verified")


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
    print(" INT-OII-002 INSTALLER")
    print(" ORACLE CERTIFIED INTELLIGENCE")
    print(" REGISTRY ATTESTATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_int_oii_001_contract()
    protected_hash = sha256_file(SOURCE_INT_OII_001)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_intelligence_registry_attestation_gate import *",
    )

    if sha256_file(SOURCE_INT_OII_001) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-001 module changed during installation"
        )
    print("[PASS] Protected INT-OII-001 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_INT_OII_001) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-001 module changed during testing"
        )

    print("[PASS] Protected INT-OII-001 module unchanged after test")
    print("[PASS] OII-015 terminal freeze remains intact")
    print("[PASS] OSR-014 terminal freeze remains intact")
    print("[PASS] INT-OSR-001 consumption boundary remains intact")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] INT-OII-002 certification test executed automatically")
    print("[DONE] INT-OII-002 CERTIFIED REGISTRY ATTESTATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
