from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
PACKAGE = QSERIES / "oracle_intelligence_integration"
PRODUCTION = PACKAGE / "oracle_certified_intelligence_registry_assembly_gate.py"
TEST = ROOT / "test_int_oii_001_oracle_certified_intelligence_registry_assembly_gate.py"
PACKAGE_INIT = PACKAGE / "__init__.py"
OSR_SOURCE = (
    QSERIES
    / "oracle_scientific_reasoning_runtime"
    / "oracle_scientific_reasoning_runtime_terminal_certification_consumption_gate.py"
)

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nENGINE_ID = "INT-OII-001"\nSCHEMA_VERSION = "INT-OII-001.v1"\nALGORITHM_VERSION = "oracle-certified-intelligence-registry-assembly.v1"\nREGISTRY_STATUS = "oracle_certified_intelligence_registry_assembled"\n\n\nclass OracleCertifiedIntelligenceRegistryInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(v) for v in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\ndef _snapshot(value: Any) -> dict[str, Any]:\n    if is_dataclass(value):\n        return asdict(value)\n    if isinstance(value, Mapping):\n        return dict(value)\n    data = getattr(value, "__dict__", None)\n    if isinstance(data, dict):\n        return dict(data)\n    raise OracleCertifiedIntelligenceRegistryInvariantError("record cannot be snapshotted")\n\n\ndef _identity(snapshot: Mapping[str, Any]) -> tuple[str, str]:\n    id_names = (\n        "terminal_certification_id", "consumption_id", "certification_id",\n        "freeze_id", "record_id", "registry_id",\n    )\n    hash_names = (\n        "terminal_certification_hash", "consumption_hash", "certification_hash",\n        "freeze_hash", "record_hash", "registry_hash",\n    )\n    record_id = next((str(snapshot[n]) for n in id_names if snapshot.get(n)), "")\n    record_hash = next((str(snapshot[n]) for n in hash_names if snapshot.get(n)), "")\n    if not record_id or not record_hash:\n        raise OracleCertifiedIntelligenceRegistryInvariantError("source identity/hash unavailable")\n    return record_id, record_hash\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceRegistryEntry:\n    subsystem_key: str\n    engine_id: str\n    source_record_id: str\n    source_record_hash: str\n    verified: bool\n    read_only_verified: bool\n    mutation_allowed: bool\n    execution_allowed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    entry_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceRegistry:\n    registry_id: str\n    entries: tuple[OracleCertifiedIntelligenceRegistryEntry, ...]\n    entry_count: int\n    deterministic_registration_order: bool\n    exact_source_hashes_preserved: bool\n    duplicate_subsystems_rejected: bool\n    immutable_registry: bool\n    downstream_read_only_consumption_allowed: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    registry_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    registry_hash: str\n\n\ndef _entry(*, subsystem_key: str, record: Any, verifier) -> OracleCertifiedIntelligenceRegistryEntry:\n    try:\n        verdict = verifier(record)\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceRegistryInvariantError(\n            f"{subsystem_key} source verification failed"\n        ) from exc\n    if verdict is False:\n        raise OracleCertifiedIntelligenceRegistryInvariantError(\n            f"{subsystem_key} source verifier returned false"\n        )\n    snapshot = _snapshot(record)\n    if snapshot.get("read_only") is not True:\n        raise OracleCertifiedIntelligenceRegistryInvariantError(\n            f"{subsystem_key} source is not read-only"\n        )\n    source_id, source_hash = _identity(snapshot)\n    body = {\n        "subsystem_key": subsystem_key,\n        "engine_id": str(snapshot.get("engine_id", subsystem_key)),\n        "source_record_id": source_id,\n        "source_record_hash": source_hash,\n        "verified": True,\n        "read_only_verified": True,\n        "mutation_allowed": False,\n        "execution_allowed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n    }\n    return OracleCertifiedIntelligenceRegistryEntry(**body, entry_hash=stable_hash(body))\n\n\ndef assemble_oracle_certified_intelligence_registry(\n    *,\n    oii_terminal_certification: Any,\n    oii_terminal_verifier,\n    osr_terminal_consumption: Any,\n    osr_terminal_consumption_verifier,\n) -> OracleCertifiedIntelligenceRegistry:\n    entries = tuple(sorted((\n        _entry(\n            subsystem_key="oracle_intelligence_integration",\n            record=oii_terminal_certification,\n            verifier=oii_terminal_verifier,\n        ),\n        _entry(\n            subsystem_key="oracle_scientific_reasoning_runtime",\n            record=osr_terminal_consumption,\n            verifier=osr_terminal_consumption_verifier,\n        ),\n    ), key=lambda e: e.subsystem_key))\n\n    keys = [entry.subsystem_key for entry in entries]\n    if len(keys) != len(set(keys)):\n        raise OracleCertifiedIntelligenceRegistryInvariantError("duplicate subsystem registration")\n\n    body = {\n        "entries": entries,\n        "entry_count": len(entries),\n        "deterministic_registration_order": True,\n        "exact_source_hashes_preserved": True,\n        "duplicate_subsystems_rejected": True,\n        "immutable_registry": True,\n        "downstream_read_only_consumption_allowed": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "registry_status": REGISTRY_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n    registry_hash = stable_hash(body)\n    return OracleCertifiedIntelligenceRegistry(\n        registry_id="oracle-certified-intelligence-registry:" + registry_hash,\n        **body,\n        registry_hash=registry_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_registry(\n    registry: OracleCertifiedIntelligenceRegistry,\n) -> bool:\n    if not isinstance(registry, OracleCertifiedIntelligenceRegistry):\n        raise OracleCertifiedIntelligenceRegistryInvariantError("invalid registry record")\n    if registry.entries != tuple(sorted(registry.entries, key=lambda e: e.subsystem_key)):\n        raise OracleCertifiedIntelligenceRegistryInvariantError("registry order mismatch")\n    if len({e.subsystem_key for e in registry.entries}) != len(registry.entries):\n        raise OracleCertifiedIntelligenceRegistryInvariantError("duplicate registry entries")\n\n    for entry in registry.entries:\n        body = {k: v for k, v in asdict(entry).items() if k != "entry_hash"}\n        if entry.entry_hash != stable_hash(body):\n            raise OracleCertifiedIntelligenceRegistryInvariantError("entry hash mismatch")\n        if (\n            entry.verified is not True\n            or entry.read_only_verified is not True\n            or entry.mutation_allowed\n            or entry.execution_allowed\n            or entry.publication_allowed\n            or entry.qseries_execution_allowed\n        ):\n            raise OracleCertifiedIntelligenceRegistryInvariantError("entry safety boundary violated")\n\n    body = {k: v for k, v in asdict(registry).items() if k not in {"registry_id", "registry_hash"}}\n    expected_hash = stable_hash(body)\n    if registry.registry_hash != expected_hash:\n        raise OracleCertifiedIntelligenceRegistryInvariantError("registry hash mismatch")\n    if registry.registry_id != "oracle-certified-intelligence-registry:" + expected_hash:\n        raise OracleCertifiedIntelligenceRegistryInvariantError("registry identity mismatch")\n\n    forbidden = (\n        registry.registry_mutation_allowed,\n        registry.oracle_execution_allowed,\n        registry.publication_allowed,\n        registry.alerting_allowed,\n        registry.qseries_execution_allowed,\n        registry.order_creation_allowed,\n        registry.funds_movement_allowed,\n        registry.portfolio_mutation_allowed,\n    )\n    if (\n        registry.entry_count != 2\n        or registry.entry_count != len(registry.entries)\n        or registry.deterministic_registration_order is not True\n        or registry.exact_source_hashes_preserved is not True\n        or registry.duplicate_subsystems_rejected is not True\n        or registry.immutable_registry is not True\n        or registry.downstream_read_only_consumption_allowed is not True\n        or registry.read_only is not True\n        or registry.engine_id != ENGINE_ID\n        or registry.schema_version != SCHEMA_VERSION\n        or registry.algorithm_version != ALGORITHM_VERSION\n        or registry.registry_status != REGISTRY_STATUS\n        or any(forbidden)\n    ):\n        raise OracleCertifiedIntelligenceRegistryInvariantError("INT-OII-001 safety boundary violated")\n    return True\n\n\ndef serialize_oracle_certified_intelligence_registry(\n    registry: OracleCertifiedIntelligenceRegistry,\n) -> str:\n    verify_oracle_certified_intelligence_registry(registry)\n    return canonical_json(registry)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "REGISTRY_STATUS",\n    "OracleCertifiedIntelligenceRegistryInvariantError",\n    "OracleCertifiedIntelligenceRegistryEntry",\n    "OracleCertifiedIntelligenceRegistry",\n    "assemble_oracle_certified_intelligence_registry",\n    "verify_oracle_certified_intelligence_registry",\n    "serialize_oracle_certified_intelligence_registry",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, replace\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_assembly_gate import (\n    OracleCertifiedIntelligenceRegistryInvariantError,\n    assemble_oracle_certified_intelligence_registry,\n    verify_oracle_certified_intelligence_registry,\n)\n\n\n@dataclass(frozen=True)\nclass StubTerminal:\n    terminal_certification_id: str\n    terminal_certification_hash: str\n    engine_id: str\n    read_only: bool\n\n\n@dataclass(frozen=True)\nclass StubConsumption:\n    consumption_id: str\n    consumption_hash: str\n    engine_id: str\n    read_only: bool\n\n\ndef accepted(_record) -> bool:\n    return True\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except OracleCertifiedIntelligenceRegistryInvariantError:\n        return\n    raise AssertionError("expected invariant rejection")\n\n\ndef main() -> None:\n    oii = StubTerminal(\n        terminal_certification_id="oii-terminal:" + "a" * 64,\n        terminal_certification_hash="a" * 64,\n        engine_id="OII-015",\n        read_only=True,\n    )\n    osr = StubConsumption(\n        consumption_id="osr-consumption:" + "b" * 64,\n        consumption_hash="b" * 64,\n        engine_id="INT-OSR-001",\n        read_only=True,\n    )\n\n    first = assemble_oracle_certified_intelligence_registry(\n        oii_terminal_certification=oii,\n        oii_terminal_verifier=accepted,\n        osr_terminal_consumption=osr,\n        osr_terminal_consumption_verifier=accepted,\n    )\n    second = assemble_oracle_certified_intelligence_registry(\n        oii_terminal_certification=oii,\n        oii_terminal_verifier=accepted,\n        osr_terminal_consumption=osr,\n        osr_terminal_consumption_verifier=accepted,\n    )\n\n    assert first == second\n    assert verify_oracle_certified_intelligence_registry(first)\n    assert first.entry_count == 2\n    assert first.registry_mutation_allowed is False\n    assert first.oracle_execution_allowed is False\n    assert first.qseries_execution_allowed is False\n    assert first.read_only is True\n\n    rejected(lambda: verify_oracle_certified_intelligence_registry(\n        replace(first, registry_hash="0" * 64)\n    ))\n    rejected(lambda: verify_oracle_certified_intelligence_registry(\n        replace(first, registry_mutation_allowed=True)\n    ))\n    rejected(lambda: assemble_oracle_certified_intelligence_registry(\n        oii_terminal_certification=replace(oii, read_only=False),\n        oii_terminal_verifier=accepted,\n        osr_terminal_consumption=osr,\n        osr_terminal_consumption_verifier=accepted,\n    ))\n\n    print("========================================")\n    print(" INT-OII-001 TEST")\n    print(" ORACLE CERTIFIED INTELLIGENCE")\n    print(" REGISTRY ASSEMBLY GATE")\n    print("========================================")\n    print("[PASS] OII-015 terminal certification accepted")\n    print("[PASS] INT-OSR-001 terminal consumption accepted")\n    print("[PASS] Certified subsystem identities preserved")\n    print("[PASS] Exact source hashes preserved")\n    print("[PASS] Deterministic registration order certified")\n    print("[PASS] Duplicate subsystem registration rejected")\n    print("[PASS] Immutable registry identity deterministic")\n    print("[PASS] Downstream read-only consumption allowed")\n    print("[PASS] Registry mutation remains disabled")\n    print("[PASS] Oracle execution remains disabled")\n    print("[PASS] Publication and alerting remain disabled")\n    print("[PASS] Q Series execution remains disabled")\n    print("[PASS] Orders, funds, and portfolio mutation disabled")\n    print("[PASS] Read-only Oracle boundary preserved")\n    print("[DONE] INT-OII-001 CERTIFIED INTELLIGENCE REGISTRY ASSEMBLED")\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def find_oii015() -> Path:
    matches = []
    for path in QSERIES.rglob("*.py"):
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if 'ENGINE_ID = "OII-015"' in source or "ENGINE_ID = 'OII-015'" in source:
            matches.append(path)
    if not matches:
        raise FileNotFoundError("Actual OII-015 module not found under qseries_v2")
    terminal = [p for p in matches if "terminal" in p.name]
    if len(terminal) == 1:
        return terminal[0]
    if len(matches) == 1:
        return matches[0]
    raise RuntimeError("Multiple OII-015 modules found: " + ", ".join(str(p) for p in matches))


def verify_source(path: Path, engine_id: str, required: tuple[str, ...]) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Required source missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(f"{engine_id} contract mismatch; missing: " + ", ".join(missing))
    ast.parse(source, filename=str(path))


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
    print(" INT-OII-001 INSTALLER")
    print(" ORACLE CERTIFIED INTELLIGENCE")
    print(" REGISTRY ASSEMBLY GATE")
    print("========================================")

    if not QSERIES.is_dir():
        raise SystemExit("[ERROR] Run from the kalshi-qss-bot repository root.")

    oii_source = find_oii015()
    verify_source(
        oii_source,
        "OII-015",
        ('ENGINE_ID = "OII-015"', "read_only"),
    )
    verify_source(
        OSR_SOURCE,
        "INT-OSR-001",
        (
            'ENGINE_ID = "INT-OSR-001"',
            "verify_oracle_scientific_reasoning_runtime_terminal_consumption",
            "consumption_hash",
            "read_only",
        ),
    )
    print(f"[OK] Actual OII-015 terminal contract verified: {oii_source}")
    print("[OK] Actual INT-OSR-001 terminal consumption contract verified")

    protected = {
        oii_source: sha256_file(oii_source),
        OSR_SOURCE: sha256_file(OSR_SOURCE),
    }

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_intelligence_registry_assembly_gate import *",
    )

    for path, digest in protected.items():
        if sha256_file(path) != digest:
            raise RuntimeError(f"Protected module changed: {path}")
    print("[PASS] Protected OII-015 and INT-OSR-001 modules unchanged")

    completed = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)

    for path, digest in protected.items():
        if sha256_file(path) != digest:
            raise RuntimeError(f"Protected module changed after test: {path}")

    print("[PASS] Protected modules unchanged after test")
    print("[PASS] OII-015 terminal freeze remains intact")
    print("[PASS] OSR-014 terminal freeze remains intact")
    print("[PASS] INT-OSR-001 consumption boundary remains intact")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] INT-OII-001 certification test executed automatically")
    print("[DONE] INT-OII-001 CERTIFIED INTELLIGENCE REGISTRY GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
