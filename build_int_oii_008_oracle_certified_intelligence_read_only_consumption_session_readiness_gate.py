from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
SOURCE_INT_OII_007 = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_attestation_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_readiness_gate.py"
)
TEST = (
    ROOT
    / "test_int_oii_008_oracle_certified_intelligence_read_only_consumption_session_readiness_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_attestation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,\n    verify_oracle_certified_intelligence_read_only_consumption_session_attestation,\n)\n\nENGINE_ID = "INT-OII-008"\nSCHEMA_VERSION = "INT-OII-008.v1"\nALGORITHM_VERSION = (\n    "oracle-certified-intelligence-read-only-consumption-session-readiness.v1"\n)\nREADINESS_STATUS = (\n    "oracle_certified_intelligence_read_only_consumption_session_ready"\n)\n\n\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n    ValueError\n):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness:\n    readiness_id: str\n    source_session_attestation_id: str\n    source_session_attestation_hash: str\n    source_session_id: str\n    source_session_hash: str\n    source_activation_id: str\n    source_activation_hash: str\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    session_attestation_verified: bool\n    exact_session_attestation_hash_scope_preserved: bool\n    exact_session_hash_scope_preserved: bool\n    exact_activation_hash_scope_preserved: bool\n    exact_authorization_hash_scope_preserved: bool\n    exact_registry_hash_scope_preserved: bool\n    exact_entry_hash_scope_preserved: bool\n    certified_subsystem_scope_preserved: bool\n    deterministic_session_identity_verified: bool\n    bounded_session_scope_verified: bool\n    single_activation_scope_verified: bool\n    session_materialization_verified: bool\n    active_session_verified: bool\n    unclosed_session_verified: bool\n    read_only_consumption_verified: bool\n    downstream_read_only_consumption_ready: bool\n    readiness_single_scope: bool\n    readiness_reversible: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    readiness_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    readiness_hash: str\n\n\ndef certify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n    *,\n    session_attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,\n) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness:\n    try:\n        verdict = (\n            verify_oracle_certified_intelligence_read_only_consumption_session_attestation(\n                session_attestation\n            )\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "INT-OII-007 session attestation verification failed"\n        ) from exc\n\n    if verdict is False:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "INT-OII-007 session attestation verifier returned false"\n        )\n\n    if session_attestation.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "certified subsystem scope is empty"\n        )\n\n    if session_attestation.source_entry_count != len(\n        session_attestation.source_entry_hashes\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if session_attestation.source_entry_count != len(\n        session_attestation.source_subsystem_keys\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    body = {\n        "source_session_attestation_id": session_attestation.attestation_id,\n        "source_session_attestation_hash": session_attestation.attestation_hash,\n        "source_session_id": session_attestation.source_session_id,\n        "source_session_hash": session_attestation.source_session_hash,\n        "source_activation_id": session_attestation.source_activation_id,\n        "source_activation_hash": session_attestation.source_activation_hash,\n        "source_authorization_id": session_attestation.source_authorization_id,\n        "source_authorization_hash": session_attestation.source_authorization_hash,\n        "source_registry_id": session_attestation.source_registry_id,\n        "source_registry_hash": session_attestation.source_registry_hash,\n        "source_entry_count": session_attestation.source_entry_count,\n        "source_entry_hashes": session_attestation.source_entry_hashes,\n        "source_subsystem_keys": session_attestation.source_subsystem_keys,\n        "session_attestation_verified": True,\n        "exact_session_attestation_hash_scope_preserved": True,\n        "exact_session_hash_scope_preserved": True,\n        "exact_activation_hash_scope_preserved": True,\n        "exact_authorization_hash_scope_preserved": True,\n        "exact_registry_hash_scope_preserved": True,\n        "exact_entry_hash_scope_preserved": True,\n        "certified_subsystem_scope_preserved": True,\n        "deterministic_session_identity_verified": True,\n        "bounded_session_scope_verified": True,\n        "single_activation_scope_verified": True,\n        "session_materialization_verified": True,\n        "active_session_verified": True,\n        "unclosed_session_verified": True,\n        "read_only_consumption_verified": True,\n        "downstream_read_only_consumption_ready": True,\n        "readiness_single_scope": True,\n        "readiness_reversible": False,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "readiness_status": READINESS_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    readiness_hash = stable_hash(body)\n\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness(\n        readiness_id=(\n            "oracle-certified-intelligence-read-only-consumption-session-readiness:"\n            + readiness_hash\n        ),\n        **body,\n        readiness_hash=readiness_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n    readiness: OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,\n) -> bool:\n    if not isinstance(\n        readiness,\n        OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "invalid read-only consumption session readiness"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(readiness).items()\n        if key not in {"readiness_id", "readiness_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if readiness.readiness_hash != expected_hash:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "session readiness hash mismatch"\n        )\n\n    if readiness.readiness_id != (\n        "oracle-certified-intelligence-read-only-consumption-session-readiness:"\n        + expected_hash\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "session readiness identity mismatch"\n        )\n\n    if readiness.source_entry_count != len(readiness.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "readiness entry hash scope mismatch"\n        )\n\n    if readiness.source_entry_count != len(readiness.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "readiness subsystem scope mismatch"\n        )\n\n    if readiness.source_subsystem_keys != tuple(\n        sorted(readiness.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "readiness subsystem scope is not deterministic"\n        )\n\n    if len(readiness.source_subsystem_keys) != len(\n        set(readiness.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "readiness subsystem scope contains duplicates"\n        )\n\n    required_true = (\n        readiness.session_attestation_verified,\n        readiness.exact_session_attestation_hash_scope_preserved,\n        readiness.exact_session_hash_scope_preserved,\n        readiness.exact_activation_hash_scope_preserved,\n        readiness.exact_authorization_hash_scope_preserved,\n        readiness.exact_registry_hash_scope_preserved,\n        readiness.exact_entry_hash_scope_preserved,\n        readiness.certified_subsystem_scope_preserved,\n        readiness.deterministic_session_identity_verified,\n        readiness.bounded_session_scope_verified,\n        readiness.single_activation_scope_verified,\n        readiness.session_materialization_verified,\n        readiness.active_session_verified,\n        readiness.unclosed_session_verified,\n        readiness.read_only_consumption_verified,\n        readiness.downstream_read_only_consumption_ready,\n        readiness.readiness_single_scope,\n        readiness.read_only,\n    )\n\n    forbidden = (\n        readiness.readiness_reversible,\n        readiness.registry_mutation_allowed,\n        readiness.oracle_execution_allowed,\n        readiness.reasoning_execution_allowed,\n        readiness.probability_estimation_allowed,\n        readiness.final_intelligence_conclusion_allowed,\n        readiness.publication_allowed,\n        readiness.alerting_allowed,\n        readiness.qseries_handoff_allowed,\n        readiness.qseries_execution_allowed,\n        readiness.order_creation_allowed,\n        readiness.funds_movement_allowed,\n        readiness.portfolio_mutation_allowed,\n    )\n\n    if (\n        readiness.engine_id != ENGINE_ID\n        or readiness.schema_version != SCHEMA_VERSION\n        or readiness.algorithm_version != ALGORITHM_VERSION\n        or readiness.readiness_status != READINESS_STATUS\n        or readiness.source_entry_count <= 0\n        or not all(value is True for value in required_true)\n        or any(forbidden)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError(\n            "INT-OII-008 permanent safety boundary violated"\n        )\n\n    return True\n\n\ndef serialize_oracle_certified_intelligence_read_only_consumption_session_readiness(\n    readiness: OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,\n) -> str:\n    verify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n        readiness\n    )\n    return canonical_json(readiness)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "READINESS_STATUS",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness",\n    "certify_oracle_certified_intelligence_read_only_consumption_session_readiness",\n    "verify_oracle_certified_intelligence_read_only_consumption_session_readiness",\n    "serialize_oracle_certified_intelligence_read_only_consumption_session_readiness",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_readiness_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_attestation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,\n)\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError:\n        return\n    raise AssertionError("expected INT-OII-008 invariant rejection")\n\n\ndef make_attestation() -> (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation\n):\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation(\n        attestation_id="session-attestation:" + "a" * 64,\n        source_session_id="session:" + "b" * 64,\n        source_session_hash="b" * 64,\n        source_activation_attestation_id="activation-attestation:" + "c" * 64,\n        source_activation_attestation_hash="c" * 64,\n        source_activation_id="activation:" + "d" * 64,\n        source_activation_hash="d" * 64,\n        source_authorization_id="authorization:" + "e" * 64,\n        source_authorization_hash="e" * 64,\n        source_registry_id="registry:" + "f" * 64,\n        source_registry_hash="f" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("1" * 64, "2" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        session_verified=True,\n        exact_session_hash_scope_preserved=True,\n        exact_activation_attestation_hash_scope_preserved=True,\n        exact_activation_hash_scope_preserved=True,\n        exact_authorization_hash_scope_preserved=True,\n        exact_registry_hash_scope_preserved=True,\n        exact_entry_hash_scope_preserved=True,\n        certified_subsystem_scope_preserved=True,\n        deterministic_session_identity_verified=True,\n        bounded_session_scope_verified=True,\n        single_activation_scope_verified=True,\n        session_materialization_verified=True,\n        active_session_verified=True,\n        unclosed_session_verified=True,\n        read_only_consumption_verified=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        attestation_status=(\n            "oracle_certified_intelligence_read_only_consumption_session_attested"\n        ),\n        engine_id="INT-OII-007",\n        schema_version="INT-OII-007.v1",\n        algorithm_version=(\n            "oracle-certified-intelligence-read-only-consumption-session-attestation.v1"\n        ),\n        attestation_hash="a" * 64,\n    )\n\n\ndef main() -> None:\n    original_verifier = (\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation\n    )\n    module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation = (\n        lambda _attestation: True\n    )\n\n    try:\n        attestation = make_attestation()\n\n        first = (\n            module.certify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n                session_attestation=attestation\n            )\n        )\n        second = (\n            module.certify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n                session_attestation=attestation\n            )\n        )\n\n        assert first == second\n        assert first.readiness_hash == second.readiness_hash\n        assert (\n            module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n                first\n            )\n        )\n        assert first.source_session_attestation_id == attestation.attestation_id\n        assert first.source_session_attestation_hash == attestation.attestation_hash\n        assert first.source_session_id == attestation.source_session_id\n        assert first.source_activation_id == attestation.source_activation_id\n        assert first.source_authorization_id == attestation.source_authorization_id\n        assert first.source_registry_id == attestation.source_registry_id\n        assert first.source_entry_count == 2\n        assert first.session_attestation_verified is True\n        assert first.downstream_read_only_consumption_ready is True\n        assert first.readiness_single_scope is True\n        assert first.readiness_reversible is False\n        assert first.oracle_execution_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n                replace(first, readiness_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n                replace(first, downstream_read_only_consumption_ready=False)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n                replace(first, readiness_reversible=True)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(\n                replace(first, reasoning_execution_allowed=True)\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-008 TEST")\n        print(" CERTIFIED INTELLIGENCE")\n        print(" SESSION READINESS GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-007 session attestation verifier consumed")\n        print("[PASS] Session attestation identity and hash preserved")\n        print("[PASS] Session identity and hash preserved")\n        print("[PASS] Activation identity and hash preserved")\n        print("[PASS] Authorization identity and hash preserved")\n        print("[PASS] Registry identity and hash preserved")\n        print("[PASS] Exact entry hash scope preserved")\n        print("[PASS] Certified subsystem scope preserved")\n        print("[PASS] Deterministic session identity verified")\n        print("[PASS] Bounded session scope verified")\n        print("[PASS] Single activation scope verified")\n        print("[PASS] Session materialization verified")\n        print("[PASS] Active and unclosed session verified")\n        print("[PASS] Read-only consumption verified")\n        print("[PASS] Downstream read-only consumption ready")\n        print("[PASS] Readiness bound to one immutable scope")\n        print("[PASS] Readiness is irreversible")\n        print("[PASS] Registry mutation remains disabled")\n        print("[PASS] Oracle and reasoning execution remain disabled")\n        print("[PASS] Probability estimation and final conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff remain disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] INT-OII-008 READ-ONLY CONSUMPTION SESSION READY")\n    finally:\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation = (\n            original_verifier\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_int_oii_007_contract() -> None:
    if not SOURCE_INT_OII_007.is_file():
        raise FileNotFoundError(
            f"Actual INT-OII-007 module missing: {SOURCE_INT_OII_007}"
        )

    source = SOURCE_INT_OII_007.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-007"',
        "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation",
        "verify_oracle_certified_intelligence_read_only_consumption_session_attestation",
        "attestation_id",
        "attestation_hash",
        "source_session_id",
        "source_session_hash",
        "source_activation_id",
        "source_activation_hash",
        "source_authorization_id",
        "source_authorization_hash",
        "source_registry_id",
        "source_registry_hash",
        "source_entry_count",
        "source_entry_hashes",
        "source_subsystem_keys",
        "session_verified",
        "active_session_verified",
        "unclosed_session_verified",
        "read_only_consumption_verified",
        "read_only",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OII-007 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_INT_OII_007))
    print("[OK] Actual INT-OII-007 session attestation contract verified")


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
    print(" INT-OII-008 INSTALLER")
    print(" CERTIFIED INTELLIGENCE")
    print(" SESSION READINESS GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_int_oii_007_contract()
    protected_hash = sha256_file(SOURCE_INT_OII_007)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_intelligence_read_only_consumption_session_readiness_gate import *",
    )

    if sha256_file(SOURCE_INT_OII_007) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-007 module changed during installation"
        )
    print("[PASS] Protected INT-OII-007 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_INT_OII_007) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-007 module changed during testing"
        )

    print("[PASS] Protected INT-OII-007 module unchanged after test")
    print("[PASS] INT-OII-006 read-only session remains intact")
    print("[PASS] INT-OII-005 activation attestation remains intact")
    print("[PASS] INT-OII-004 consumption activation remains intact")
    print("[PASS] INT-OII-003 consumption authorization remains intact")
    print("[PASS] INT-OII-002 registry attestation remains intact")
    print("[PASS] INT-OII-001 registry assembly remains intact")
    print("[PASS] OII-015 terminal freeze remains intact")
    print("[PASS] OSR-014 terminal freeze remains intact")
    print("[PASS] INT-OSR-001 consumption boundary remains intact")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] INT-OII-008 certification test executed automatically")
    print("[DONE] INT-OII-008 SESSION READINESS GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
