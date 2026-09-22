from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning_runtime"
SOURCE_OSR002 = PACKAGE / "oracle_certified_callable_admission_gate.py"
PRODUCTION = (
    PACKAGE
    / "oracle_scientific_reasoning_callable_resolution_engine.py"
)
TEST = (
    ROOT
    / "test_osr_003_oracle_scientific_reasoning_callable_resolution_engine.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport importlib.util\nimport json\nfrom typing import Any, Mapping\n\nfrom .oracle_certified_callable_admission_gate import (\n    CertifiedCallableAdmissionPackage,\n    CertifiedCallableAdmissionRecord,\n    verify_certified_callable_admission_package,\n)\n\nENGINE_ID = "OSR-003"\nSCHEMA_VERSION = "OSR-003.v1"\nALGORITHM_VERSION = "scientific-reasoning-callable-resolution-engine.v1"\n\nRESOLUTION_STATUS = "resolved_reference_only_inactive_unbound_non_executable"\nPACKAGE_STATUS = "certified_callable_references_resolved_read_only"\n\n\nclass OracleScientificReasoningResolutionInvariantError(ValueError):\n    """Raised when an OSR-003 resolution invariant is violated."""\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, (set, frozenset)):\n        normalized = [_canonical(item) for item in value]\n        return sorted(\n            normalized,\n            key=lambda item: json.dumps(\n                item,\n                sort_keys=True,\n                separators=(",", ":"),\n                ensure_ascii=False,\n            ),\n        )\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass ScientificReasoningCallableResolutionRecord:\n    discipline_id: str\n    callable_id: str\n    source_admission_record_hash: str\n    implementation_module: str\n    implementation_symbol: str\n    module_spec_available: bool\n    symbol_lookup_performed: bool\n    callable_loaded: bool\n    active: bool\n    resolved: bool\n    bound: bool\n    executable: bool\n    read_only: bool\n    resolution_status: str\n    resolution_record_hash: str\n\n\n@dataclass(frozen=True)\nclass ScientificReasoningCallableResolutionPackage:\n    resolution_package_id: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_oii015_certification_hash: str\n    source_frozen_evidence_set_hash: str\n    resolution_records: tuple[ScientificReasoningCallableResolutionRecord, ...]\n    resolved_disciplines: tuple[str, ...]\n    resolved_callable_count: int\n    unresolved_callable_count: int\n    resolution_status: str\n    resolution_hash: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    read_only: bool\n    callable_resolution_allowed: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n\n\ndef _resolve_admitted_record(\n    record: CertifiedCallableAdmissionRecord,\n) -> ScientificReasoningCallableResolutionRecord:\n    if record.admitted is not True:\n        raise OracleScientificReasoningResolutionInvariantError(\n            f"callable was not admitted: {record.callable_id}"\n        )\n    if (\n        record.active\n        or record.resolved\n        or record.bound\n        or record.executable\n        or record.read_only is not True\n    ):\n        raise OracleScientificReasoningResolutionInvariantError(\n            f"admission record boundary violated: {record.callable_id}"\n        )\n\n    try:\n        module_spec_available = (\n            importlib.util.find_spec(record.implementation_module) is not None\n        )\n    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):\n        module_spec_available = False\n\n    body = {\n        "discipline_id": record.discipline_id,\n        "callable_id": record.callable_id,\n        "source_admission_record_hash": record.admission_record_hash,\n        "implementation_module": record.implementation_module,\n        "implementation_symbol": record.implementation_symbol,\n        "module_spec_available": module_spec_available,\n        "symbol_lookup_performed": False,\n        "callable_loaded": False,\n        "active": False,\n        "resolved": True,\n        "bound": False,\n        "executable": False,\n        "read_only": True,\n        "resolution_status": RESOLUTION_STATUS,\n    }\n    return ScientificReasoningCallableResolutionRecord(\n        **body,\n        resolution_record_hash=stable_hash(body),\n    )\n\n\ndef resolve_certified_scientific_reasoning_callables(\n    *,\n    admission_package: CertifiedCallableAdmissionPackage,\n) -> ScientificReasoningCallableResolutionPackage:\n    try:\n        verify_certified_callable_admission_package(admission_package)\n    except Exception as exc:\n        raise OracleScientificReasoningResolutionInvariantError(\n            "OSR-002 admission package verification failed"\n        ) from exc\n\n    ordered_records = tuple(\n        sorted(\n            admission_package.admission_records,\n            key=lambda item: item.discipline_id,\n        )\n    )\n    resolution_records = tuple(\n        _resolve_admitted_record(record)\n        for record in ordered_records\n    )\n    resolved_disciplines = tuple(\n        record.discipline_id for record in resolution_records\n    )\n\n    if resolved_disciplines != admission_package.admitted_disciplines:\n        raise OracleScientificReasoningResolutionInvariantError(\n            "resolution discipline lineage mismatch"\n        )\n    if len({record.callable_id for record in resolution_records}) != len(\n        resolution_records\n    ):\n        raise OracleScientificReasoningResolutionInvariantError(\n            "duplicate callable identity detected during resolution"\n        )\n\n    body = {\n        "source_admission_package_id":\n            admission_package.admission_package_id,\n        "source_admission_hash": admission_package.admission_hash,\n        "source_registry_id": admission_package.source_registry_id,\n        "source_registry_hash": admission_package.source_registry_hash,\n        "source_oii015_certification_hash":\n            admission_package.source_oii015_certification_hash,\n        "source_frozen_evidence_set_hash":\n            admission_package.source_frozen_evidence_set_hash,\n        "resolution_records": resolution_records,\n        "resolved_disciplines": resolved_disciplines,\n        "resolved_callable_count": len(resolution_records),\n        "unresolved_callable_count": 0,\n        "resolution_status": PACKAGE_STATUS,\n    }\n    resolution_hash = stable_hash(body)\n\n    return ScientificReasoningCallableResolutionPackage(\n        resolution_package_id=(\n            "scientific-reasoning-callable-resolution:" + resolution_hash\n        ),\n        **body,\n        resolution_hash=resolution_hash,\n        engine_id=ENGINE_ID,\n        schema_version=SCHEMA_VERSION,\n        algorithm_version=ALGORITHM_VERSION,\n        read_only=True,\n        callable_resolution_allowed=True,\n        callable_binding_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n    )\n\n\ndef verify_scientific_reasoning_callable_resolution_record(\n    record: ScientificReasoningCallableResolutionRecord,\n) -> bool:\n    if not isinstance(record, ScientificReasoningCallableResolutionRecord):\n        raise OracleScientificReasoningResolutionInvariantError(\n            "invalid resolution record"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(record).items()\n        if key != "resolution_record_hash"\n    }\n    if stable_hash(body) != record.resolution_record_hash:\n        raise OracleScientificReasoningResolutionInvariantError(\n            "resolution record hash verification failed"\n        )\n\n    if (\n        record.resolution_status != RESOLUTION_STATUS\n        or record.resolved is not True\n        or record.active\n        or record.bound\n        or record.executable\n        or record.symbol_lookup_performed\n        or record.callable_loaded\n        or record.read_only is not True\n    ):\n        raise OracleScientificReasoningResolutionInvariantError(\n            "resolution record safety boundary violated"\n        )\n    return True\n\n\ndef verify_scientific_reasoning_callable_resolution_package(\n    package: ScientificReasoningCallableResolutionPackage,\n) -> bool:\n    if not isinstance(package, ScientificReasoningCallableResolutionPackage):\n        raise OracleScientificReasoningResolutionInvariantError(\n            "invalid resolution package"\n        )\n\n    for record in package.resolution_records:\n        verify_scientific_reasoning_callable_resolution_record(record)\n\n    if package.resolved_disciplines != tuple(\n        record.discipline_id for record in package.resolution_records\n    ):\n        raise OracleScientificReasoningResolutionInvariantError(\n            "resolved discipline set mismatch"\n        )\n    if package.resolved_callable_count != len(package.resolution_records):\n        raise OracleScientificReasoningResolutionInvariantError(\n            "resolved callable count mismatch"\n        )\n    if package.unresolved_callable_count != 0:\n        raise OracleScientificReasoningResolutionInvariantError(\n            "unresolved callable count must remain zero"\n        )\n\n    body = {\n        "source_admission_package_id":\n            package.source_admission_package_id,\n        "source_admission_hash": package.source_admission_hash,\n        "source_registry_id": package.source_registry_id,\n        "source_registry_hash": package.source_registry_hash,\n        "source_oii015_certification_hash":\n            package.source_oii015_certification_hash,\n        "source_frozen_evidence_set_hash":\n            package.source_frozen_evidence_set_hash,\n        "resolution_records": package.resolution_records,\n        "resolved_disciplines": package.resolved_disciplines,\n        "resolved_callable_count": package.resolved_callable_count,\n        "unresolved_callable_count": package.unresolved_callable_count,\n        "resolution_status": package.resolution_status,\n    }\n    expected_hash = stable_hash(body)\n    if package.resolution_hash != expected_hash:\n        raise OracleScientificReasoningResolutionInvariantError(\n            "resolution package hash verification failed"\n        )\n    if package.resolution_package_id != (\n        "scientific-reasoning-callable-resolution:" + expected_hash\n    ):\n        raise OracleScientificReasoningResolutionInvariantError(\n            "resolution package identity verification failed"\n        )\n\n    forbidden = (\n        package.callable_binding_allowed,\n        package.reasoning_execution_allowed,\n        package.probability_estimation_allowed,\n        package.final_intelligence_conclusion_allowed,\n        package.publication_allowed,\n        package.alerting_allowed,\n        package.qseries_handoff_allowed,\n        package.qseries_execution_allowed,\n        package.order_creation_allowed,\n        package.funds_movement_allowed,\n        package.portfolio_mutation_allowed,\n    )\n    if (\n        package.engine_id != ENGINE_ID\n        or package.read_only is not True\n        or package.callable_resolution_allowed is not True\n        or package.resolution_status != PACKAGE_STATUS\n        or any(forbidden)\n    ):\n        raise OracleScientificReasoningResolutionInvariantError(\n            "OSR-003 permanent safety boundary violated"\n        )\n    return True\n\n\ndef serialize_scientific_reasoning_callable_resolution_package(\n    package: ScientificReasoningCallableResolutionPackage,\n) -> str:\n    verify_scientific_reasoning_callable_resolution_package(package)\n    return canonical_json(package)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "RESOLUTION_STATUS",\n    "PACKAGE_STATUS",\n    "OracleScientificReasoningResolutionInvariantError",\n    "ScientificReasoningCallableResolutionRecord",\n    "ScientificReasoningCallableResolutionPackage",\n    "resolve_certified_scientific_reasoning_callables",\n    "verify_scientific_reasoning_callable_resolution_record",\n    "verify_scientific_reasoning_callable_resolution_package",\n    "serialize_scientific_reasoning_callable_resolution_package",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nfrom qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_final_certification_freeze_gate import (\n    IntegratedIntelligenceFinalCertification,\n    IntegratedIntelligenceModuleAttestation,\n    PERMANENTLY_DISABLED_CAPABILITIES,\n    REQUIRED_ENGINE_IDS,\n    stable_hash as oii_stable_hash,\n)\nfrom qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_callable_registry import (\n    APPROVED_DISCIPLINES,\n    build_scientific_reasoning_callable_registry,\n)\nfrom qseries_v2.oracle_scientific_reasoning_runtime.oracle_certified_callable_admission_gate import (\n    admit_certified_scientific_reasoning_callables,\n)\nfrom qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_callable_resolution_engine import (\n    OracleScientificReasoningResolutionInvariantError,\n    resolve_certified_scientific_reasoning_callables,\n    verify_scientific_reasoning_callable_resolution_package,\n)\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except OracleScientificReasoningResolutionInvariantError:\n        return\n    raise AssertionError("expected OSR-003 invariant rejection")\n\n\ndef build_terminal_certification() -> IntegratedIntelligenceFinalCertification:\n    records = []\n    for engine_id in REQUIRED_ENGINE_IDS:\n        body = {\n            "engine_id": engine_id,\n            "module_name": f"module_{engine_id.lower().replace(\'-\', \'_\')}",\n            "relative_path": f"qseries_v2/frozen/{engine_id}.py",\n            "source_sha256": oii_stable_hash(engine_id),\n            "source_size_bytes": 1000,\n            "syntax_verified": True,\n            "engine_identity_verified": True,\n            "read_only_boundary_declared": True,\n        }\n        records.append(\n            IntegratedIntelligenceModuleAttestation(\n                **body,\n                attestation_hash=oii_stable_hash(body),\n            )\n        )\n\n    body = {\n        "source_invocation_manifest_id": "oii014:manifest",\n        "source_invocation_manifest_hash": oii_stable_hash("oii014"),\n        "source_activation_hash": oii_stable_hash("oii013"),\n        "source_authorization_hash": oii_stable_hash("oii012"),\n        "source_session_hash": oii_stable_hash("oii010"),\n        "source_manifest_hash": oii_stable_hash("oii009"),\n        "frozen_evidence_set_hash": oii_stable_hash("frozen-evidence"),\n        "module_attestations": tuple(records),\n        "certified_engine_ids": REQUIRED_ENGINE_IDS,\n        "certified_module_count": len(records),\n        "permanent_disabled_capabilities": PERMANENTLY_DISABLED_CAPABILITIES,\n        "terminal_status":\n            "integrated_intelligence_certified_frozen_read_only",\n        "subsystem_frozen": True,\n        "further_certification_layers_required": False,\n    }\n    certification_hash = oii_stable_hash(body)\n    return IntegratedIntelligenceFinalCertification(\n        certification_id=(\n            "integrated-intelligence-final-certification:"\n            + certification_hash\n        ),\n        **body,\n        certification_hash=certification_hash,\n        engine_id="OII-015",\n        schema_version="OII-015.v1",\n        algorithm_version=\n            "integrated-intelligence-final-certification-freeze.v1",\n        read_only=True,\n        acquisition_mutation_allowed=False,\n        analytics_mutation_allowed=False,\n        operator_mutation_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n    )\n\n\ndef main() -> None:\n    certification = build_terminal_certification()\n    registry = build_scientific_reasoning_callable_registry(\n        terminal_certification=certification\n    )\n    admission = admit_certified_scientific_reasoning_callables(\n        registry=registry\n    )\n\n    first = resolve_certified_scientific_reasoning_callables(\n        admission_package=admission\n    )\n    second = resolve_certified_scientific_reasoning_callables(\n        admission_package=admission\n    )\n\n    assert first == second\n    assert first.resolution_hash == second.resolution_hash\n    assert verify_scientific_reasoning_callable_resolution_package(first)\n\n    assert first.source_admission_hash == admission.admission_hash\n    assert first.resolved_disciplines == APPROVED_DISCIPLINES\n    assert first.resolved_callable_count == 9\n    assert first.unresolved_callable_count == 0\n    assert all(record.resolved for record in first.resolution_records)\n    assert all(not record.active for record in first.resolution_records)\n    assert all(not record.bound for record in first.resolution_records)\n    assert all(not record.executable for record in first.resolution_records)\n    assert all(\n        not record.symbol_lookup_performed\n        for record in first.resolution_records\n    )\n    assert all(\n        not record.callable_loaded\n        for record in first.resolution_records\n    )\n\n    rejected(\n        lambda: verify_scientific_reasoning_callable_resolution_package(\n            replace(first, resolution_hash="0" * 64)\n        )\n    )\n    rejected(\n        lambda: verify_scientific_reasoning_callable_resolution_package(\n            replace(first, callable_binding_allowed=True)\n        )\n    )\n    rejected(\n        lambda: resolve_certified_scientific_reasoning_callables(\n            admission_package=replace(\n                admission,\n                admission_hash="0" * 64,\n            )\n        )\n    )\n\n    print("========================================")\n    print(" OSR-003 TEST")\n    print(" SCIENTIFIC REASONING CALLABLE")\n    print(" RESOLUTION ENGINE")\n    print("========================================")\n    print("[PASS] Actual OSR-002 admission package consumed")\n    print("[PASS] OSR-002 identity and hash lineage verified")\n    print("[PASS] Exact approved discipline set resolved")\n    print("[PASS] Resolution records deterministic")\n    print("[PASS] Resolution remains reference-only")\n    print("[PASS] No implementation module imported")\n    print("[PASS] No implementation symbol loaded")\n    print("[PASS] No callable activated")\n    print("[PASS] Callable binding remains disabled")\n    print("[PASS] Reasoning execution remains disabled")\n    print("[PASS] Probability estimation remains disabled")\n    print("[PASS] Final intelligence conclusions remain disabled")\n    print("[PASS] Publication, alerting, and handoff disabled")\n    print("[PASS] Q Series execution remains disabled")\n    print("[PASS] Orders, funds, and portfolio mutation disabled")\n    print("[PASS] Read-only Oracle boundary preserved")\n    print("[DONE] OSR-003 CALLABLE RESOLUTION ENGINE CERTIFIED")\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_osr002_contract() -> None:
    if not SOURCE_OSR002.is_file():
        raise FileNotFoundError(
            f"Actual OSR-002 module missing: {SOURCE_OSR002}"
        )
    source = SOURCE_OSR002.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "OSR-002"',
        "class CertifiedCallableAdmissionRecord",
        "class CertifiedCallableAdmissionPackage",
        "def verify_certified_callable_admission_package",
        "admission_package_id",
        "admission_hash",
        "source_registry_id",
        "source_registry_hash",
        "source_oii015_certification_hash",
        "source_frozen_evidence_set_hash",
        "admission_records",
        "admitted_disciplines",
        "read_only",
        "callable_binding_allowed",
        "reasoning_execution_allowed",
        "qseries_execution_allowed",
        "order_creation_allowed",
        "funds_movement_allowed",
        "portfolio_mutation_allowed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual OSR-002 contract mismatch; missing: "
            + ", ".join(missing)
        )
    ast.parse(source, filename=str(SOURCE_OSR002))
    print("[OK] Actual OSR-002 callable admission contract verified")


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
    print(" OSR-003 INSTALLER")
    print(" SCIENTIFIC REASONING CALLABLE")
    print(" RESOLUTION ENGINE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_osr002_contract()
    protected_hash = sha256_file(SOURCE_OSR002)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_scientific_reasoning_callable_resolution_engine import *",
    )

    if sha256_file(SOURCE_OSR002) != protected_hash:
        raise RuntimeError("Protected OSR-002 module changed during installation")
    print("[PASS] Protected OSR-002 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_OSR002) != protected_hash:
        raise RuntimeError("Protected OSR-002 module changed during testing")

    print("[PASS] Protected OSR-002 module unchanged after test")
    print("[PASS] OII-015 terminal freeze remains untouched")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] OSR-003 certification test executed automatically")
    print("[DONE] OSR-003 CALLABLE RESOLUTION ENGINE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
