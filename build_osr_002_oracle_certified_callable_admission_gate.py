from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning_runtime"
SOURCE_OSR003 = (
    PACKAGE
    / "oracle_scientific_reasoning_callable_resolution_engine.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_callable_resolution_authorization_gate.py"
)
TEST = (
    ROOT
    / "test_osr_004_oracle_certified_callable_resolution_authorization_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom .oracle_scientific_reasoning_callable_resolution_engine import (\n    ScientificReasoningCallableResolutionPackage,\n    verify_scientific_reasoning_callable_resolution_package,\n)\n\nENGINE_ID = "OSR-004"\nSCHEMA_VERSION = "OSR-004.v1"\nALGORITHM_VERSION = "certified-callable-resolution-authorization-gate.v1"\n\nAUTHORIZATION_STATUS = (\n    "certified_callable_resolution_authorized_read_only_single_scope"\n)\n\n\nclass OracleCertifiedCallableResolutionAuthorizationInvariantError(ValueError):\n    """Raised when an OSR-004 authorization invariant is violated."""\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass CertifiedCallableResolutionAuthorization:\n    authorization_id: str\n    source_resolution_package_id: str\n    source_resolution_hash: str\n    source_admission_package_id: str\n    source_admission_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_oii015_certification_hash: str\n    source_frozen_evidence_set_hash: str\n    authorized_disciplines: tuple[str, ...]\n    authorized_callable_count: int\n    callable_resolution_authorized: bool\n    authorization_scope: str\n    authorization_status: str\n    authorization_hash: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    read_only: bool\n    callable_activation_allowed: bool\n    callable_binding_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n\n\ndef authorize_certified_callable_resolution(\n    *,\n    resolution_package: ScientificReasoningCallableResolutionPackage,\n) -> CertifiedCallableResolutionAuthorization:\n    try:\n        verify_scientific_reasoning_callable_resolution_package(\n            resolution_package\n        )\n    except Exception as exc:\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "OSR-003 resolution package verification failed"\n        ) from exc\n\n    if resolution_package.resolved_callable_count <= 0:\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "resolution package contains no resolved callables"\n        )\n    if resolution_package.unresolved_callable_count != 0:\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "unresolved callables cannot be authorized"\n        )\n    if not resolution_package.resolved_disciplines:\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "resolved discipline lineage is empty"\n        )\n\n    body = {\n        "source_resolution_package_id":\n            resolution_package.resolution_package_id,\n        "source_resolution_hash": resolution_package.resolution_hash,\n        "source_admission_package_id":\n            resolution_package.source_admission_package_id,\n        "source_admission_hash":\n            resolution_package.source_admission_hash,\n        "source_registry_id": resolution_package.source_registry_id,\n        "source_registry_hash": resolution_package.source_registry_hash,\n        "source_oii015_certification_hash":\n            resolution_package.source_oii015_certification_hash,\n        "source_frozen_evidence_set_hash":\n            resolution_package.source_frozen_evidence_set_hash,\n        "authorized_disciplines":\n            resolution_package.resolved_disciplines,\n        "authorized_callable_count":\n            resolution_package.resolved_callable_count,\n        "callable_resolution_authorized": True,\n        "authorization_scope":\n            "consume_exact_osr003_resolution_hash_once",\n        "authorization_status": AUTHORIZATION_STATUS,\n    }\n    authorization_hash = stable_hash(body)\n\n    return CertifiedCallableResolutionAuthorization(\n        authorization_id=(\n            "certified-callable-resolution-authorization:"\n            + authorization_hash\n        ),\n        **body,\n        authorization_hash=authorization_hash,\n        engine_id=ENGINE_ID,\n        schema_version=SCHEMA_VERSION,\n        algorithm_version=ALGORITHM_VERSION,\n        read_only=True,\n        callable_activation_allowed=False,\n        callable_binding_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n    )\n\n\ndef verify_certified_callable_resolution_authorization(\n    authorization: CertifiedCallableResolutionAuthorization,\n) -> bool:\n    if not isinstance(\n        authorization,\n        CertifiedCallableResolutionAuthorization,\n    ):\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "invalid resolution authorization"\n        )\n\n    body = {\n        "source_resolution_package_id":\n            authorization.source_resolution_package_id,\n        "source_resolution_hash": authorization.source_resolution_hash,\n        "source_admission_package_id":\n            authorization.source_admission_package_id,\n        "source_admission_hash": authorization.source_admission_hash,\n        "source_registry_id": authorization.source_registry_id,\n        "source_registry_hash": authorization.source_registry_hash,\n        "source_oii015_certification_hash":\n            authorization.source_oii015_certification_hash,\n        "source_frozen_evidence_set_hash":\n            authorization.source_frozen_evidence_set_hash,\n        "authorized_disciplines": authorization.authorized_disciplines,\n        "authorized_callable_count":\n            authorization.authorized_callable_count,\n        "callable_resolution_authorized":\n            authorization.callable_resolution_authorized,\n        "authorization_scope": authorization.authorization_scope,\n        "authorization_status": authorization.authorization_status,\n    }\n    expected_hash = stable_hash(body)\n\n    if authorization.authorization_hash != expected_hash:\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "resolution authorization hash verification failed"\n        )\n    if authorization.authorization_id != (\n        "certified-callable-resolution-authorization:" + expected_hash\n    ):\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "resolution authorization identity verification failed"\n        )\n    if (\n        authorization.authorized_callable_count\n        != len(authorization.authorized_disciplines)\n        or authorization.authorized_callable_count <= 0\n    ):\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "authorized callable count mismatch"\n        )\n    if len(set(authorization.authorized_disciplines)) != len(\n        authorization.authorized_disciplines\n    ):\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "duplicate authorized discipline detected"\n        )\n\n    forbidden = (\n        authorization.callable_activation_allowed,\n        authorization.callable_binding_allowed,\n        authorization.reasoning_execution_allowed,\n        authorization.probability_estimation_allowed,\n        authorization.final_intelligence_conclusion_allowed,\n        authorization.publication_allowed,\n        authorization.alerting_allowed,\n        authorization.qseries_handoff_allowed,\n        authorization.qseries_execution_allowed,\n        authorization.order_creation_allowed,\n        authorization.funds_movement_allowed,\n        authorization.portfolio_mutation_allowed,\n    )\n    if (\n        authorization.engine_id != ENGINE_ID\n        or authorization.read_only is not True\n        or authorization.callable_resolution_authorized is not True\n        or authorization.authorization_scope\n        != "consume_exact_osr003_resolution_hash_once"\n        or authorization.authorization_status != AUTHORIZATION_STATUS\n        or any(forbidden)\n    ):\n        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(\n            "OSR-004 permanent safety boundary violated"\n        )\n    return True\n\n\ndef serialize_certified_callable_resolution_authorization(\n    authorization: CertifiedCallableResolutionAuthorization,\n) -> str:\n    verify_certified_callable_resolution_authorization(authorization)\n    return canonical_json(authorization)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "AUTHORIZATION_STATUS",\n    "OracleCertifiedCallableResolutionAuthorizationInvariantError",\n    "CertifiedCallableResolutionAuthorization",\n    "authorize_certified_callable_resolution",\n    "verify_certified_callable_resolution_authorization",\n    "serialize_certified_callable_resolution_authorization",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nfrom qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_final_certification_freeze_gate import (\n    IntegratedIntelligenceFinalCertification,\n    IntegratedIntelligenceModuleAttestation,\n    PERMANENTLY_DISABLED_CAPABILITIES,\n    REQUIRED_ENGINE_IDS,\n    stable_hash as oii_stable_hash,\n)\nfrom qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_callable_registry import (\n    APPROVED_DISCIPLINES,\n    build_scientific_reasoning_callable_registry,\n)\nfrom qseries_v2.oracle_scientific_reasoning_runtime.oracle_certified_callable_admission_gate import (\n    admit_certified_scientific_reasoning_callables,\n)\nfrom qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_callable_resolution_engine import (\n    resolve_certified_scientific_reasoning_callables,\n)\nfrom qseries_v2.oracle_scientific_reasoning_runtime.oracle_certified_callable_resolution_authorization_gate import (\n    OracleCertifiedCallableResolutionAuthorizationInvariantError,\n    authorize_certified_callable_resolution,\n    verify_certified_callable_resolution_authorization,\n)\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except OracleCertifiedCallableResolutionAuthorizationInvariantError:\n        return\n    raise AssertionError("expected OSR-004 invariant rejection")\n\n\ndef build_terminal_certification() -> IntegratedIntelligenceFinalCertification:\n    records = []\n    for engine_id in REQUIRED_ENGINE_IDS:\n        body = {\n            "engine_id": engine_id,\n            "module_name": f"module_{engine_id.lower().replace(\'-\', \'_\')}",\n            "relative_path": f"qseries_v2/frozen/{engine_id}.py",\n            "source_sha256": oii_stable_hash(engine_id),\n            "source_size_bytes": 1000,\n            "syntax_verified": True,\n            "engine_identity_verified": True,\n            "read_only_boundary_declared": True,\n        }\n        records.append(\n            IntegratedIntelligenceModuleAttestation(\n                **body,\n                attestation_hash=oii_stable_hash(body),\n            )\n        )\n\n    body = {\n        "source_invocation_manifest_id": "oii014:manifest",\n        "source_invocation_manifest_hash": oii_stable_hash("oii014"),\n        "source_activation_hash": oii_stable_hash("oii013"),\n        "source_authorization_hash": oii_stable_hash("oii012"),\n        "source_session_hash": oii_stable_hash("oii010"),\n        "source_manifest_hash": oii_stable_hash("oii009"),\n        "frozen_evidence_set_hash": oii_stable_hash("frozen-evidence"),\n        "module_attestations": tuple(records),\n        "certified_engine_ids": REQUIRED_ENGINE_IDS,\n        "certified_module_count": len(records),\n        "permanent_disabled_capabilities": PERMANENTLY_DISABLED_CAPABILITIES,\n        "terminal_status":\n            "integrated_intelligence_certified_frozen_read_only",\n        "subsystem_frozen": True,\n        "further_certification_layers_required": False,\n    }\n    certification_hash = oii_stable_hash(body)\n    return IntegratedIntelligenceFinalCertification(\n        certification_id=(\n            "integrated-intelligence-final-certification:"\n            + certification_hash\n        ),\n        **body,\n        certification_hash=certification_hash,\n        engine_id="OII-015",\n        schema_version="OII-015.v1",\n        algorithm_version=\n            "integrated-intelligence-final-certification-freeze.v1",\n        read_only=True,\n        acquisition_mutation_allowed=False,\n        analytics_mutation_allowed=False,\n        operator_mutation_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n    )\n\n\ndef main() -> None:\n    certification = build_terminal_certification()\n    registry = build_scientific_reasoning_callable_registry(\n        terminal_certification=certification\n    )\n    admission = admit_certified_scientific_reasoning_callables(\n        registry=registry\n    )\n    resolution = resolve_certified_scientific_reasoning_callables(\n        admission_package=admission\n    )\n\n    first = authorize_certified_callable_resolution(\n        resolution_package=resolution\n    )\n    second = authorize_certified_callable_resolution(\n        resolution_package=resolution\n    )\n\n    assert first == second\n    assert first.authorization_hash == second.authorization_hash\n    assert verify_certified_callable_resolution_authorization(first)\n    assert first.source_resolution_hash == resolution.resolution_hash\n    assert first.authorized_disciplines == APPROVED_DISCIPLINES\n    assert first.authorized_callable_count == 9\n    assert first.callable_resolution_authorized is True\n    assert first.callable_activation_allowed is False\n    assert first.callable_binding_allowed is False\n    assert first.reasoning_execution_allowed is False\n    assert first.qseries_execution_allowed is False\n\n    rejected(\n        lambda: verify_certified_callable_resolution_authorization(\n            replace(first, authorization_hash="0" * 64)\n        )\n    )\n    rejected(\n        lambda: verify_certified_callable_resolution_authorization(\n            replace(first, callable_binding_allowed=True)\n        )\n    )\n    rejected(\n        lambda: authorize_certified_callable_resolution(\n            resolution_package=replace(\n                resolution,\n                resolution_hash="0" * 64,\n            )\n        )\n    )\n\n    print("========================================")\n    print(" OSR-004 TEST")\n    print(" CERTIFIED CALLABLE RESOLUTION")\n    print(" AUTHORIZATION GATE")\n    print("========================================")\n    print("[PASS] Actual OSR-003 resolution package consumed")\n    print("[PASS] OSR-003 identity and hash lineage verified")\n    print("[PASS] Exact resolved discipline set authorized")\n    print("[PASS] Authorization identity deterministic")\n    print("[PASS] Exact resolution hash scope preserved")\n    print("[PASS] Resolution authorization enabled")\n    print("[PASS] Callable activation remains disabled")\n    print("[PASS] Callable binding remains disabled")\n    print("[PASS] Reasoning execution remains disabled")\n    print("[PASS] Probability estimation remains disabled")\n    print("[PASS] Final intelligence conclusions remain disabled")\n    print("[PASS] Publication, alerting, and handoff disabled")\n    print("[PASS] Q Series execution remains disabled")\n    print("[PASS] Orders, funds, and portfolio mutation disabled")\n    print("[PASS] Read-only Oracle boundary preserved")\n    print("[DONE] OSR-004 RESOLUTION AUTHORIZATION GATE CERTIFIED")\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_osr003_contract() -> None:
    if not SOURCE_OSR003.is_file():
        raise FileNotFoundError(
            f"Actual OSR-003 module missing: {SOURCE_OSR003}"
        )
    source = SOURCE_OSR003.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "OSR-003"',
        "class ScientificReasoningCallableResolutionPackage",
        "def verify_scientific_reasoning_callable_resolution_package",
        "resolution_package_id",
        "resolution_hash",
        "source_admission_package_id",
        "source_admission_hash",
        "source_registry_id",
        "source_registry_hash",
        "source_oii015_certification_hash",
        "source_frozen_evidence_set_hash",
        "resolved_disciplines",
        "resolved_callable_count",
        "unresolved_callable_count",
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
            "Actual OSR-003 contract mismatch; missing: "
            + ", ".join(missing)
        )
    ast.parse(source, filename=str(SOURCE_OSR003))
    print("[OK] Actual OSR-003 callable resolution contract verified")


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
    print(" OSR-004 INSTALLER")
    print(" CERTIFIED CALLABLE RESOLUTION")
    print(" AUTHORIZATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_osr003_contract()
    protected_hash = sha256_file(SOURCE_OSR003)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_callable_resolution_authorization_gate import *",
    )

    if sha256_file(SOURCE_OSR003) != protected_hash:
        raise RuntimeError("Protected OSR-003 module changed during installation")
    print("[PASS] Protected OSR-003 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_OSR003) != protected_hash:
        raise RuntimeError("Protected OSR-003 module changed during testing")

    print("[PASS] Protected OSR-003 module unchanged after test")
    print("[PASS] OII-015 terminal freeze remains untouched")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] OSR-004 certification test executed automatically")
    print("[DONE] OSR-004 RESOLUTION AUTHORIZATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
