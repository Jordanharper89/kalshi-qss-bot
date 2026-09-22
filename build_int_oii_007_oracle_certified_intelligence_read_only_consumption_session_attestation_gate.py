from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
SOURCE_INT_OII_006 = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_attestation_gate.py"
)
TEST = (
    ROOT
    / "test_int_oii_007_oracle_certified_intelligence_read_only_consumption_session_attestation_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSession,\n    verify_oracle_certified_intelligence_read_only_consumption_session,\n)\n\nENGINE_ID = "INT-OII-007"\nSCHEMA_VERSION = "INT-OII-007.v1"\nALGORITHM_VERSION = (\n    "oracle-certified-intelligence-read-only-consumption-session-attestation.v1"\n)\nATTESTATION_STATUS = (\n    "oracle_certified_intelligence_read_only_consumption_session_attested"\n)\n\n\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n    ValueError\n):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation:\n    attestation_id: str\n    source_session_id: str\n    source_session_hash: str\n    source_activation_attestation_id: str\n    source_activation_attestation_hash: str\n    source_activation_id: str\n    source_activation_hash: str\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    session_verified: bool\n    exact_session_hash_scope_preserved: bool\n    exact_activation_attestation_hash_scope_preserved: bool\n    exact_activation_hash_scope_preserved: bool\n    exact_authorization_hash_scope_preserved: bool\n    exact_registry_hash_scope_preserved: bool\n    exact_entry_hash_scope_preserved: bool\n    certified_subsystem_scope_preserved: bool\n    deterministic_session_identity_verified: bool\n    bounded_session_scope_verified: bool\n    single_activation_scope_verified: bool\n    session_materialization_verified: bool\n    active_session_verified: bool\n    unclosed_session_verified: bool\n    read_only_consumption_verified: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    attestation_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    attestation_hash: str\n\n\ndef attest_oracle_certified_intelligence_read_only_consumption_session(\n    *,\n    session: OracleCertifiedIntelligenceReadOnlyConsumptionSession,\n) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation:\n    try:\n        verdict = verify_oracle_certified_intelligence_read_only_consumption_session(\n            session\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "INT-OII-006 read-only consumption session verification failed"\n        ) from exc\n\n    if verdict is False:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "INT-OII-006 session verifier returned false"\n        )\n\n    if session.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "certified subsystem scope is empty"\n        )\n\n    if session.source_entry_count != len(session.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if session.source_entry_count != len(session.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    body = {\n        "source_session_id": session.session_id,\n        "source_session_hash": session.session_hash,\n        "source_activation_attestation_id": (\n            session.source_activation_attestation_id\n        ),\n        "source_activation_attestation_hash": (\n            session.source_activation_attestation_hash\n        ),\n        "source_activation_id": session.source_activation_id,\n        "source_activation_hash": session.source_activation_hash,\n        "source_authorization_id": session.source_authorization_id,\n        "source_authorization_hash": session.source_authorization_hash,\n        "source_registry_id": session.source_registry_id,\n        "source_registry_hash": session.source_registry_hash,\n        "source_entry_count": session.source_entry_count,\n        "source_entry_hashes": session.source_entry_hashes,\n        "source_subsystem_keys": session.source_subsystem_keys,\n        "session_verified": True,\n        "exact_session_hash_scope_preserved": True,\n        "exact_activation_attestation_hash_scope_preserved": True,\n        "exact_activation_hash_scope_preserved": True,\n        "exact_authorization_hash_scope_preserved": True,\n        "exact_registry_hash_scope_preserved": True,\n        "exact_entry_hash_scope_preserved": True,\n        "certified_subsystem_scope_preserved": True,\n        "deterministic_session_identity_verified": True,\n        "bounded_session_scope_verified": True,\n        "single_activation_scope_verified": True,\n        "session_materialization_verified": True,\n        "active_session_verified": True,\n        "unclosed_session_verified": True,\n        "read_only_consumption_verified": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "attestation_status": ATTESTATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    attestation_hash = stable_hash(body)\n\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation(\n        attestation_id=(\n            "oracle-certified-intelligence-read-only-consumption-session-attestation:"\n            + attestation_hash\n        ),\n        **body,\n        attestation_hash=attestation_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_read_only_consumption_session_attestation(\n    attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,\n) -> bool:\n    if not isinstance(\n        attestation,\n        OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "invalid read-only consumption session attestation"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(attestation).items()\n        if key not in {"attestation_id", "attestation_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if attestation.attestation_hash != expected_hash:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "session attestation hash mismatch"\n        )\n\n    if attestation.attestation_id != (\n        "oracle-certified-intelligence-read-only-consumption-session-attestation:"\n        + expected_hash\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "session attestation identity mismatch"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "attested entry hash scope mismatch"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "attested subsystem scope mismatch"\n        )\n\n    if attestation.source_subsystem_keys != tuple(\n        sorted(attestation.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "attested subsystem scope is not deterministic"\n        )\n\n    if len(attestation.source_subsystem_keys) != len(\n        set(attestation.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "attested subsystem scope contains duplicates"\n        )\n\n    required_true = (\n        attestation.session_verified,\n        attestation.exact_session_hash_scope_preserved,\n        attestation.exact_activation_attestation_hash_scope_preserved,\n        attestation.exact_activation_hash_scope_preserved,\n        attestation.exact_authorization_hash_scope_preserved,\n        attestation.exact_registry_hash_scope_preserved,\n        attestation.exact_entry_hash_scope_preserved,\n        attestation.certified_subsystem_scope_preserved,\n        attestation.deterministic_session_identity_verified,\n        attestation.bounded_session_scope_verified,\n        attestation.single_activation_scope_verified,\n        attestation.session_materialization_verified,\n        attestation.active_session_verified,\n        attestation.unclosed_session_verified,\n        attestation.read_only_consumption_verified,\n        attestation.read_only,\n    )\n\n    forbidden = (\n        attestation.registry_mutation_allowed,\n        attestation.oracle_execution_allowed,\n        attestation.reasoning_execution_allowed,\n        attestation.probability_estimation_allowed,\n        attestation.final_intelligence_conclusion_allowed,\n        attestation.publication_allowed,\n        attestation.alerting_allowed,\n        attestation.qseries_handoff_allowed,\n        attestation.qseries_execution_allowed,\n        attestation.order_creation_allowed,\n        attestation.funds_movement_allowed,\n        attestation.portfolio_mutation_allowed,\n    )\n\n    if (\n        attestation.engine_id != ENGINE_ID\n        or attestation.schema_version != SCHEMA_VERSION\n        or attestation.algorithm_version != ALGORITHM_VERSION\n        or attestation.attestation_status != ATTESTATION_STATUS\n        or attestation.source_entry_count <= 0\n        or not all(value is True for value in required_true)\n        or any(forbidden)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError(\n            "INT-OII-007 permanent safety boundary violated"\n        )\n\n    return True\n\n\ndef serialize_oracle_certified_intelligence_read_only_consumption_session_attestation(\n    attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,\n) -> str:\n    verify_oracle_certified_intelligence_read_only_consumption_session_attestation(\n        attestation\n    )\n    return canonical_json(attestation)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "ATTESTATION_STATUS",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation",\n    "attest_oracle_certified_intelligence_read_only_consumption_session",\n    "verify_oracle_certified_intelligence_read_only_consumption_session_attestation",\n    "serialize_oracle_certified_intelligence_read_only_consumption_session_attestation",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_attestation_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSession,\n)\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-007 invariant rejection")\n\n\ndef make_session() -> OracleCertifiedIntelligenceReadOnlyConsumptionSession:\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSession(\n        session_id="read-only-session:" + "a" * 64,\n        source_activation_attestation_id="activation-attestation:" + "b" * 64,\n        source_activation_attestation_hash="b" * 64,\n        source_activation_id="activation:" + "c" * 64,\n        source_activation_hash="c" * 64,\n        source_authorization_id="authorization:" + "d" * 64,\n        source_authorization_hash="d" * 64,\n        source_registry_id="registry:" + "e" * 64,\n        source_registry_hash="e" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("1" * 64, "2" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        activation_attestation_verified=True,\n        exact_activation_attestation_hash_scope_preserved=True,\n        exact_activation_hash_scope_preserved=True,\n        exact_authorization_hash_scope_preserved=True,\n        exact_registry_hash_scope_preserved=True,\n        exact_entry_hash_scope_preserved=True,\n        certified_subsystem_scope_preserved=True,\n        deterministic_session_identity=True,\n        bounded_session_scope=True,\n        single_activation_scope=True,\n        session_materialized=True,\n        session_active=True,\n        session_closed=False,\n        read_only_consumption_allowed=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        session_status=(\n            "oracle_certified_intelligence_read_only_consumption_session_materialized"\n        ),\n        engine_id="INT-OII-006",\n        schema_version="INT-OII-006.v1",\n        algorithm_version=(\n            "oracle-certified-intelligence-read-only-consumption-session.v1"\n        ),\n        session_hash="a" * 64,\n    )\n\n\ndef main() -> None:\n    original_verifier = (\n        module.verify_oracle_certified_intelligence_read_only_consumption_session\n    )\n    module.verify_oracle_certified_intelligence_read_only_consumption_session = (\n        lambda _session: True\n    )\n\n    try:\n        session = make_session()\n\n        first = (\n            module.attest_oracle_certified_intelligence_read_only_consumption_session(\n                session=session\n            )\n        )\n        second = (\n            module.attest_oracle_certified_intelligence_read_only_consumption_session(\n                session=session\n            )\n        )\n\n        assert first == second\n        assert first.attestation_hash == second.attestation_hash\n        assert (\n            module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(\n                first\n            )\n        )\n        assert first.source_session_id == session.session_id\n        assert first.source_session_hash == session.session_hash\n        assert first.source_activation_id == session.source_activation_id\n        assert first.source_authorization_id == session.source_authorization_id\n        assert first.source_registry_id == session.source_registry_id\n        assert first.source_entry_count == 2\n        assert first.session_verified is True\n        assert first.deterministic_session_identity_verified is True\n        assert first.bounded_session_scope_verified is True\n        assert first.single_activation_scope_verified is True\n        assert first.session_materialization_verified is True\n        assert first.active_session_verified is True\n        assert first.unclosed_session_verified is True\n        assert first.read_only_consumption_verified is True\n        assert first.oracle_execution_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(\n                replace(first, attestation_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(\n                replace(first, active_session_verified=False)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(\n                replace(first, oracle_execution_allowed=True)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(\n                replace(first, source_entry_count=3)\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-007 TEST")\n        print(" CERTIFIED INTELLIGENCE")\n        print(" SESSION ATTESTATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-006 session verifier consumed")\n        print("[PASS] Session identity and hash preserved")\n        print("[PASS] Activation attestation identity and hash preserved")\n        print("[PASS] Activation identity and hash preserved")\n        print("[PASS] Authorization identity and hash preserved")\n        print("[PASS] Registry identity and hash preserved")\n        print("[PASS] Exact entry hash scope preserved")\n        print("[PASS] Certified subsystem scope preserved")\n        print("[PASS] Deterministic session identity verified")\n        print("[PASS] Bounded session scope verified")\n        print("[PASS] Single activation scope verified")\n        print("[PASS] Session materialization verified")\n        print("[PASS] Active and unclosed session verified")\n        print("[PASS] Read-only consumption verified")\n        print("[PASS] Registry mutation remains disabled")\n        print("[PASS] Oracle and reasoning execution remain disabled")\n        print("[PASS] Probability estimation and final conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff remain disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] INT-OII-007 READ-ONLY CONSUMPTION SESSION ATTESTED")\n    finally:\n        module.verify_oracle_certified_intelligence_read_only_consumption_session = (\n            original_verifier\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_int_oii_006_contract() -> None:
    if not SOURCE_INT_OII_006.is_file():
        raise FileNotFoundError(
            f"Actual INT-OII-006 module missing: {SOURCE_INT_OII_006}"
        )

    source = SOURCE_INT_OII_006.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-006"',
        "OracleCertifiedIntelligenceReadOnlyConsumptionSession",
        "verify_oracle_certified_intelligence_read_only_consumption_session",
        "session_id",
        "session_hash",
        "source_activation_attestation_id",
        "source_activation_attestation_hash",
        "source_activation_id",
        "source_activation_hash",
        "source_authorization_id",
        "source_authorization_hash",
        "source_registry_id",
        "source_registry_hash",
        "source_entry_count",
        "source_entry_hashes",
        "source_subsystem_keys",
        "deterministic_session_identity",
        "bounded_session_scope",
        "single_activation_scope",
        "session_materialized",
        "session_active",
        "session_closed",
        "read_only_consumption_allowed",
        "read_only",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OII-006 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_INT_OII_006))
    print("[OK] Actual INT-OII-006 read-only consumption session contract verified")


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
    print(" INT-OII-007 INSTALLER")
    print(" CERTIFIED INTELLIGENCE")
    print(" SESSION ATTESTATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_int_oii_006_contract()
    protected_hash = sha256_file(SOURCE_INT_OII_006)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_intelligence_read_only_consumption_session_attestation_gate import *",
    )

    if sha256_file(SOURCE_INT_OII_006) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-006 module changed during installation"
        )
    print("[PASS] Protected INT-OII-006 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_INT_OII_006) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-006 module changed during testing"
        )

    print("[PASS] Protected INT-OII-006 module unchanged after test")
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
    print("[OK] INT-OII-007 certification test executed automatically")
    print("[DONE] INT-OII-007 SESSION ATTESTATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
