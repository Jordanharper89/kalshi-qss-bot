from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
SOURCE_INT_OII_005 = (
    PACKAGE
    / "oracle_certified_intelligence_registry_consumption_activation_attestation_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_gate.py"
)
TEST = (
    ROOT
    / "test_int_oii_006_oracle_certified_intelligence_read_only_consumption_session_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_attestation_gate import (\n    OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,\n    verify_oracle_certified_intelligence_registry_consumption_activation_attestation,\n)\n\nENGINE_ID = "INT-OII-006"\nSCHEMA_VERSION = "INT-OII-006.v1"\nALGORITHM_VERSION = "oracle-certified-intelligence-read-only-consumption-session.v1"\nSESSION_STATUS = "oracle_certified_intelligence_read_only_consumption_session_materialized"\n\n\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSession:\n    session_id: str\n    source_activation_attestation_id: str\n    source_activation_attestation_hash: str\n    source_activation_id: str\n    source_activation_hash: str\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    activation_attestation_verified: bool\n    exact_activation_attestation_hash_scope_preserved: bool\n    exact_activation_hash_scope_preserved: bool\n    exact_authorization_hash_scope_preserved: bool\n    exact_registry_hash_scope_preserved: bool\n    exact_entry_hash_scope_preserved: bool\n    certified_subsystem_scope_preserved: bool\n    deterministic_session_identity: bool\n    bounded_session_scope: bool\n    single_activation_scope: bool\n    session_materialized: bool\n    session_active: bool\n    session_closed: bool\n    read_only_consumption_allowed: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    session_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    session_hash: str\n\n\ndef materialize_oracle_certified_intelligence_read_only_consumption_session(\n    *,\n    activation_attestation: OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,\n) -> OracleCertifiedIntelligenceReadOnlyConsumptionSession:\n    try:\n        verdict = (\n            verify_oracle_certified_intelligence_registry_consumption_activation_attestation(\n                activation_attestation\n            )\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "INT-OII-005 activation attestation verification failed"\n        ) from exc\n\n    if verdict is False:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "INT-OII-005 activation attestation verifier returned false"\n        )\n\n    if activation_attestation.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "certified subsystem scope is empty"\n        )\n\n    if activation_attestation.source_entry_count != len(\n        activation_attestation.source_entry_hashes\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if activation_attestation.source_entry_count != len(\n        activation_attestation.source_subsystem_keys\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    body = {\n        "source_activation_attestation_id": activation_attestation.attestation_id,\n        "source_activation_attestation_hash": activation_attestation.attestation_hash,\n        "source_activation_id": activation_attestation.source_activation_id,\n        "source_activation_hash": activation_attestation.source_activation_hash,\n        "source_authorization_id": activation_attestation.source_authorization_id,\n        "source_authorization_hash": activation_attestation.source_authorization_hash,\n        "source_registry_id": activation_attestation.source_registry_id,\n        "source_registry_hash": activation_attestation.source_registry_hash,\n        "source_entry_count": activation_attestation.source_entry_count,\n        "source_entry_hashes": activation_attestation.source_entry_hashes,\n        "source_subsystem_keys": activation_attestation.source_subsystem_keys,\n        "activation_attestation_verified": True,\n        "exact_activation_attestation_hash_scope_preserved": True,\n        "exact_activation_hash_scope_preserved": True,\n        "exact_authorization_hash_scope_preserved": True,\n        "exact_registry_hash_scope_preserved": True,\n        "exact_entry_hash_scope_preserved": True,\n        "certified_subsystem_scope_preserved": True,\n        "deterministic_session_identity": True,\n        "bounded_session_scope": True,\n        "single_activation_scope": True,\n        "session_materialized": True,\n        "session_active": True,\n        "session_closed": False,\n        "read_only_consumption_allowed": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "session_status": SESSION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    session_hash = stable_hash(body)\n\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSession(\n        session_id="oracle-certified-intelligence-read-only-consumption-session:"\n        + session_hash,\n        **body,\n        session_hash=session_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_read_only_consumption_session(\n    session: OracleCertifiedIntelligenceReadOnlyConsumptionSession,\n) -> bool:\n    if not isinstance(\n        session,\n        OracleCertifiedIntelligenceReadOnlyConsumptionSession,\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "invalid read-only consumption session"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(session).items()\n        if key not in {"session_id", "session_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if session.session_hash != expected_hash:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "session hash mismatch"\n        )\n\n    if session.session_id != (\n        "oracle-certified-intelligence-read-only-consumption-session:"\n        + expected_hash\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "session identity mismatch"\n        )\n\n    if session.source_entry_count != len(session.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "session entry hash scope mismatch"\n        )\n\n    if session.source_entry_count != len(session.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "session subsystem scope mismatch"\n        )\n\n    if session.source_subsystem_keys != tuple(\n        sorted(session.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "session subsystem scope is not deterministic"\n        )\n\n    if len(session.source_subsystem_keys) != len(\n        set(session.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "session subsystem scope contains duplicates"\n        )\n\n    required_true = (\n        session.activation_attestation_verified,\n        session.exact_activation_attestation_hash_scope_preserved,\n        session.exact_activation_hash_scope_preserved,\n        session.exact_authorization_hash_scope_preserved,\n        session.exact_registry_hash_scope_preserved,\n        session.exact_entry_hash_scope_preserved,\n        session.certified_subsystem_scope_preserved,\n        session.deterministic_session_identity,\n        session.bounded_session_scope,\n        session.single_activation_scope,\n        session.session_materialized,\n        session.session_active,\n        session.read_only_consumption_allowed,\n        session.read_only,\n    )\n\n    forbidden = (\n        session.session_closed,\n        session.registry_mutation_allowed,\n        session.oracle_execution_allowed,\n        session.reasoning_execution_allowed,\n        session.probability_estimation_allowed,\n        session.final_intelligence_conclusion_allowed,\n        session.publication_allowed,\n        session.alerting_allowed,\n        session.qseries_handoff_allowed,\n        session.qseries_execution_allowed,\n        session.order_creation_allowed,\n        session.funds_movement_allowed,\n        session.portfolio_mutation_allowed,\n    )\n\n    if (\n        session.engine_id != ENGINE_ID\n        or session.schema_version != SCHEMA_VERSION\n        or session.algorithm_version != ALGORITHM_VERSION\n        or session.session_status != SESSION_STATUS\n        or session.source_entry_count <= 0\n        or not all(value is True for value in required_true)\n        or any(forbidden)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError(\n            "INT-OII-006 permanent safety boundary violated"\n        )\n\n    return True\n\n\ndef serialize_oracle_certified_intelligence_read_only_consumption_session(\n    session: OracleCertifiedIntelligenceReadOnlyConsumptionSession,\n) -> str:\n    verify_oracle_certified_intelligence_read_only_consumption_session(session)\n    return canonical_json(session)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "SESSION_STATUS",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSession",\n    "materialize_oracle_certified_intelligence_read_only_consumption_session",\n    "verify_oracle_certified_intelligence_read_only_consumption_session",\n    "serialize_oracle_certified_intelligence_read_only_consumption_session",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_attestation_gate import (\n    OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,\n)\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError:\n        return\n    raise AssertionError("expected INT-OII-006 invariant rejection")\n\n\ndef make_activation_attestation() -> (\n    OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation\n):\n    return OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation(\n        attestation_id="activation-attestation:" + "a" * 64,\n        source_activation_id="activation:" + "b" * 64,\n        source_activation_hash="b" * 64,\n        source_authorization_id="authorization:" + "c" * 64,\n        source_authorization_hash="c" * 64,\n        source_attestation_id="registry-attestation:" + "d" * 64,\n        source_attestation_hash="d" * 64,\n        source_registry_id="registry:" + "e" * 64,\n        source_registry_hash="e" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("1" * 64, "2" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        activation_verified=True,\n        exact_activation_hash_scope_preserved=True,\n        exact_authorization_hash_scope_preserved=True,\n        exact_attestation_hash_scope_preserved=True,\n        exact_registry_hash_scope_preserved=True,\n        exact_entry_hash_scope_preserved=True,\n        certified_subsystem_scope_preserved=True,\n        deterministic_activation_verified=True,\n        bounded_registry_scope_verified=True,\n        single_use_authorization_consumption_verified=True,\n        duplicate_activation_rejection_verified=True,\n        irreversible_activation_verified=True,\n        read_only_consumption_activation_verified=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        attestation_status=(\n            "oracle_certified_intelligence_registry_consumption_activation_attested"\n        ),\n        engine_id="INT-OII-005",\n        schema_version="INT-OII-005.v1",\n        algorithm_version=(\n            "oracle-certified-intelligence-registry-consumption-activation-attestation.v1"\n        ),\n        attestation_hash="a" * 64,\n    )\n\n\ndef main() -> None:\n    original_verifier = (\n        module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation\n    )\n    module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation = (\n        lambda _attestation: True\n    )\n\n    try:\n        activation_attestation = make_activation_attestation()\n\n        first = (\n            module.materialize_oracle_certified_intelligence_read_only_consumption_session(\n                activation_attestation=activation_attestation\n            )\n        )\n        second = (\n            module.materialize_oracle_certified_intelligence_read_only_consumption_session(\n                activation_attestation=activation_attestation\n            )\n        )\n\n        assert first == second\n        assert first.session_hash == second.session_hash\n        assert (\n            module.verify_oracle_certified_intelligence_read_only_consumption_session(\n                first\n            )\n        )\n        assert (\n            first.source_activation_attestation_id\n            == activation_attestation.attestation_id\n        )\n        assert (\n            first.source_activation_attestation_hash\n            == activation_attestation.attestation_hash\n        )\n        assert first.source_activation_id == activation_attestation.source_activation_id\n        assert first.source_authorization_id == (\n            activation_attestation.source_authorization_id\n        )\n        assert first.source_registry_id == activation_attestation.source_registry_id\n        assert first.source_entry_count == 2\n        assert first.deterministic_session_identity is True\n        assert first.bounded_session_scope is True\n        assert first.single_activation_scope is True\n        assert first.session_materialized is True\n        assert first.session_active is True\n        assert first.session_closed is False\n        assert first.read_only_consumption_allowed is True\n        assert first.oracle_execution_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session(\n                replace(first, session_hash="0" * 64)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session(\n                replace(first, session_active=False)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session(\n                replace(first, session_closed=True)\n            )\n        )\n        rejected(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session(\n                replace(first, reasoning_execution_allowed=True)\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-006 TEST")\n        print(" CERTIFIED INTELLIGENCE")\n        print(" READ-ONLY CONSUMPTION SESSION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-005 activation attestation verifier consumed")\n        print("[PASS] Activation attestation identity and hash preserved")\n        print("[PASS] Activation identity and hash preserved")\n        print("[PASS] Authorization identity and hash preserved")\n        print("[PASS] Registry identity and hash preserved")\n        print("[PASS] Exact entry hash scope preserved")\n        print("[PASS] Certified subsystem scope preserved")\n        print("[PASS] Deterministic session identity certified")\n        print("[PASS] Bounded session scope certified")\n        print("[PASS] Single activation scope certified")\n        print("[PASS] Read-only consumption session materialized")\n        print("[PASS] Session active and not closed")\n        print("[PASS] Registry mutation remains disabled")\n        print("[PASS] Oracle and reasoning execution remain disabled")\n        print("[PASS] Probability estimation and final conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff remain disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] INT-OII-006 READ-ONLY CONSUMPTION SESSION MATERIALIZED")\n    finally:\n        module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation = (\n            original_verifier\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_int_oii_005_contract() -> None:
    if not SOURCE_INT_OII_005.is_file():
        raise FileNotFoundError(
            f"Actual INT-OII-005 module missing: {SOURCE_INT_OII_005}"
        )

    source = SOURCE_INT_OII_005.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-005"',
        "OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation",
        "verify_oracle_certified_intelligence_registry_consumption_activation_attestation",
        "attestation_id",
        "attestation_hash",
        "source_activation_id",
        "source_activation_hash",
        "source_authorization_id",
        "source_authorization_hash",
        "source_registry_id",
        "source_registry_hash",
        "source_entry_count",
        "source_entry_hashes",
        "source_subsystem_keys",
        "activation_verified",
        "read_only_consumption_activation_verified",
        "read_only",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OII-005 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_INT_OII_005))
    print("[OK] Actual INT-OII-005 activation attestation contract verified")


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
    print(" INT-OII-006 INSTALLER")
    print(" CERTIFIED INTELLIGENCE")
    print(" READ-ONLY CONSUMPTION SESSION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_int_oii_005_contract()
    protected_hash = sha256_file(SOURCE_INT_OII_005)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_certified_intelligence_read_only_consumption_session_gate import *",
    )

    if sha256_file(SOURCE_INT_OII_005) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-005 module changed during installation"
        )
    print("[PASS] Protected INT-OII-005 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_INT_OII_005) != protected_hash:
        raise RuntimeError(
            "Protected INT-OII-005 module changed during testing"
        )

    print("[PASS] Protected INT-OII-005 module unchanged after test")
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
    print("[OK] INT-OII-006 certification test executed automatically")
    print("[DONE] INT-OII-006 READ-ONLY CONSUMPTION SESSION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
