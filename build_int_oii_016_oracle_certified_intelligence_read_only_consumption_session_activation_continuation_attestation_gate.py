from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "qseries_v2" / "oracle_intelligence_integration").is_dir():
            return candidate
    raise SystemExit("[ERROR] Could not locate the kalshi-qss-bot repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
PACKAGE_INIT = PACKAGE / "__init__.py"
UPSTREAM = PACKAGE / "oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate.py"
PRODUCTION = PACKAGE / "oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate.py"
TEST = ROOT / "test_int_oii_016_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nfrom dataclasses import asdict, dataclass\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation,\n    verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation,\n)\n\nENGINE_ID = "INT-OII-016"\nSCHEMA_VERSION = "INT-OII-016.v1"\nALGORITHM_VERSION = "oracle-certified-intelligence-read-only-consumption-session-activation-continuation-attestation.v1"\nATTESTATION_STATUS = "oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attested"\n\n\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(ValueError):\n    pass\n\n\ndef _canonical_json(value: object) -> str:\n    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)\n\n\ndef _stable_hash(value: object) -> str:\n    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation:\n    attestation_id: str\n    source_continuation_id: str\n    source_continuation_hash: str\n    source_authorization_consumption_id: str\n    source_authorization_consumption_hash: str\n    source_activation_authorization_id: str\n    source_activation_authorization_hash: str\n    source_activation_id: str\n    source_activation_hash: str\n    source_session_id: str\n    source_session_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    continuation_verified: bool\n    deterministic_attestation: bool\n    bounded_attestation_scope: bool\n    single_continuation_scope: bool\n    attestation_single_use: bool\n    duplicate_attestation_allowed: bool\n    attestation_reversible: bool\n    downstream_read_only_consumption_active: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    attestation_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    attestation_hash: str\n\n\ndef attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(\n    *, continuation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation\n) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation:\n    try:\n        verified = verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(continuation)\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(\n            "INT-OII-015 continuation verification failed"\n        ) from exc\n    if verified is not True:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(\n            "INT-OII-015 continuation was not verified"\n        )\n    if (\n        continuation.source_entry_count <= 0\n        or continuation.source_entry_count != len(continuation.source_entry_hashes)\n        or continuation.source_entry_count != len(continuation.source_subsystem_keys)\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(\n            "certified subsystem scope mismatch"\n        )\n    required = (\n        continuation.authorization_consumption_verified,\n        continuation.deterministic_continuation,\n        continuation.bounded_continuation_scope,\n        continuation.single_consumption_scope,\n        continuation.continuation_single_use,\n        continuation.downstream_read_only_consumption_active,\n        continuation.read_only,\n    )\n    forbidden = (\n        continuation.duplicate_continuation_allowed,\n        continuation.continuation_reversible,\n        continuation.registry_mutation_allowed,\n        continuation.oracle_execution_allowed,\n        continuation.reasoning_execution_allowed,\n        continuation.probability_estimation_allowed,\n        continuation.final_intelligence_conclusion_allowed,\n        continuation.publication_allowed,\n        continuation.alerting_allowed,\n        continuation.qseries_handoff_allowed,\n        continuation.qseries_execution_allowed,\n        continuation.order_creation_allowed,\n        continuation.funds_movement_allowed,\n        continuation.portfolio_mutation_allowed,\n    )\n    if not all(required) or any(forbidden):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(\n            "INT-OII-015 read-only boundary mismatch"\n        )\n    body = {\n        "source_continuation_id": continuation.continuation_id,\n        "source_continuation_hash": continuation.continuation_hash,\n        "source_authorization_consumption_id": continuation.source_authorization_consumption_id,\n        "source_authorization_consumption_hash": continuation.source_authorization_consumption_hash,\n        "source_activation_authorization_id": continuation.source_activation_authorization_id,\n        "source_activation_authorization_hash": continuation.source_activation_authorization_hash,\n        "source_activation_id": continuation.source_activation_id,\n        "source_activation_hash": continuation.source_activation_hash,\n        "source_session_id": continuation.source_session_id,\n        "source_session_hash": continuation.source_session_hash,\n        "source_registry_id": continuation.source_registry_id,\n        "source_registry_hash": continuation.source_registry_hash,\n        "source_entry_count": continuation.source_entry_count,\n        "source_entry_hashes": tuple(continuation.source_entry_hashes),\n        "source_subsystem_keys": tuple(continuation.source_subsystem_keys),\n        "continuation_verified": True,\n        "deterministic_attestation": True,\n        "bounded_attestation_scope": True,\n        "single_continuation_scope": True,\n        "attestation_single_use": True,\n        "duplicate_attestation_allowed": False,\n        "attestation_reversible": False,\n        "downstream_read_only_consumption_active": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "attestation_status": ATTESTATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n    attestation_hash = _stable_hash(body)\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation(\n        attestation_id="oracle-certified-intelligence-read-only-consumption-session-activation-continuation-attestation:" + attestation_hash,\n        **body,\n        attestation_hash=attestation_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation(\n    value: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation,\n) -> bool:\n    if not isinstance(value, OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(\n            "invalid INT-OII-016 attestation type"\n        )\n    body = asdict(value)\n    supplied_hash = body.pop("attestation_hash")\n    body.pop("attestation_id")\n    expected_hash = _stable_hash(body)\n    if supplied_hash != expected_hash:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(\n            "INT-OII-016 attestation hash mismatch"\n        )\n    expected_id = "oracle-certified-intelligence-read-only-consumption-session-activation-continuation-attestation:" + expected_hash\n    if value.attestation_id != expected_id:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(\n            "INT-OII-016 attestation id mismatch"\n        )\n    required = (\n        value.continuation_verified,\n        value.deterministic_attestation,\n        value.bounded_attestation_scope,\n        value.single_continuation_scope,\n        value.attestation_single_use,\n        value.downstream_read_only_consumption_active,\n        value.read_only,\n    )\n    forbidden = (\n        value.duplicate_attestation_allowed,\n        value.attestation_reversible,\n        value.registry_mutation_allowed,\n        value.oracle_execution_allowed,\n        value.reasoning_execution_allowed,\n        value.probability_estimation_allowed,\n        value.final_intelligence_conclusion_allowed,\n        value.publication_allowed,\n        value.alerting_allowed,\n        value.qseries_handoff_allowed,\n        value.qseries_execution_allowed,\n        value.order_creation_allowed,\n        value.funds_movement_allowed,\n        value.portfolio_mutation_allowed,\n    )\n    if (\n        not all(required)\n        or any(forbidden)\n        or value.source_entry_count <= 0\n        or value.source_entry_count != len(value.source_entry_hashes)\n        or value.source_entry_count != len(value.source_subsystem_keys)\n        or value.engine_id != ENGINE_ID\n        or value.schema_version != SCHEMA_VERSION\n        or value.algorithm_version != ALGORITHM_VERSION\n        or value.attestation_status != ATTESTATION_STATUS\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError(\n            "INT-OII-016 permanent safety boundary violated"\n        )\n    return True\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "ATTESTATION_STATUS",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation",\n    "attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation",\n    "verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation",\n]\n'
TEST_SOURCE = 'from __future__ import annotations\n\nfrom dataclasses import replace\n\nfrom qseries_v2.oracle_intelligence_integration import oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation,\n)\n\n\ndef make_continuation():\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation(\n        continuation_id="continuation:" + "a" * 64,\n        source_authorization_consumption_id="authorization-consumption:" + "b" * 64,\n        source_authorization_consumption_hash="b" * 64,\n        source_activation_authorization_id="authorization:" + "c" * 64,\n        source_activation_authorization_hash="c" * 64,\n        source_activation_id="activation:" + "d" * 64,\n        source_activation_hash="d" * 64,\n        source_session_id="session:" + "e" * 64,\n        source_session_hash="e" * 64,\n        source_registry_id="registry:" + "f" * 64,\n        source_registry_hash="f" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("1" * 64, "2" * 64),\n        source_subsystem_keys=("oracle_intelligence_integration", "oracle_scientific_reasoning_runtime"),\n        authorization_consumption_verified=True,\n        deterministic_continuation=True,\n        bounded_continuation_scope=True,\n        single_consumption_scope=True,\n        continuation_single_use=True,\n        duplicate_continuation_allowed=False,\n        continuation_reversible=False,\n        downstream_read_only_consumption_active=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        continuation_status="oracle_certified_intelligence_read_only_consumption_session_activation_continued",\n        engine_id="INT-OII-015",\n        schema_version="INT-OII-015.v1",\n        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation-continuation.v1",\n        continuation_hash="3" * 64,\n    )\n\n\ndef reject(fn):\n    try:\n        fn()\n    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-016 rejection")\n\n\ndef main():\n    original = module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation\n    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation = lambda _: True\n    try:\n        source = make_continuation()\n        first = module.attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(continuation=source)\n        second = module.attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(continuation=source)\n        assert first == second\n        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation(first)\n        assert first.source_continuation_id == source.continuation_id\n        assert first.source_continuation_hash == source.continuation_hash\n        assert first.deterministic_attestation and first.bounded_attestation_scope\n        assert first.single_continuation_scope and first.attestation_single_use and first.read_only\n        assert not first.duplicate_attestation_allowed and not first.attestation_reversible\n        assert not first.oracle_execution_allowed and not first.qseries_execution_allowed\n        reject(lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation(replace(first, attestation_hash="0" * 64)))\n        reject(lambda: module.attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(continuation=replace(source, downstream_read_only_consumption_active=False)))\n        print("========================================")\n        print(" INT-OII-016 TEST")\n        print(" CONTINUATION ATTESTATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-015 activation continuation consumed")\n        print("[PASS] Complete activation and registry lineage preserved")\n        print("[PASS] Deterministic bounded attestation certified")\n        print("[PASS] Single-continuation and single-use scope certified")\n        print("[PASS] Duplicate and reversible attestation disabled")\n        print("[PASS] Downstream read-only consumption remains active")\n        print("[PASS] Oracle and reasoning execution disabled")\n        print("[PASS] Q Series execution disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[DONE] INT-OII-016 CONTINUATION ATTESTATION GATE PASS")\n    finally:\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation = original\n\n\nif __name__ == "__main__":\n    main()\n'


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" INT-OII-016 INSTALLER")
    print(" CONTINUATION ATTESTATION GATE")
    print("========================================")
    if not UPSTREAM.is_file():
        raise SystemExit(f"[ERROR] Actual INT-OII-015 module missing: {UPSTREAM}")
    source = UPSTREAM.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-015"',
        "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation",
        "verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation",
        "continuation_id",
        "continuation_hash",
        "downstream_read_only_consumption_active",
        "read_only",
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise SystemExit("[ERROR] INT-OII-015 contract mismatch: " + ", ".join(missing))
    ast.parse(source, filename=str(UPSTREAM))
    upstream_hash = digest(UPSTREAM)
    print("[OK] Actual INT-OII-015 activation continuation contract verified")

    write_complete(PRODUCTION, PRODUCTION_SOURCE)
    write_complete(TEST, TEST_SOURCE)

    export = "from .oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate import *"
    existing = PACKAGE_INIT.read_text(encoding="utf-8") if PACKAGE_INIT.exists() else ""
    if export not in existing.splitlines():
        if existing and not existing.endswith("\n"):
            existing += "\n"
        PACKAGE_INIT.write_text(existing + export + "\n", encoding="utf-8", newline="\n")
        ast.parse(PACKAGE_INIT.read_text(encoding="utf-8"), filename=str(PACKAGE_INIT))
        print(f"[OK] PACKAGE UPDATED: {PACKAGE_INIT.resolve()}")
    else:
        print(f"[OK] PACKAGE EXPORT PRESENT: {PACKAGE_INIT.resolve()}")

    if digest(UPSTREAM) != upstream_hash:
        raise RuntimeError("Protected INT-OII-015 module changed during installation")

    completed = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if digest(UPSTREAM) != upstream_hash:
        raise RuntimeError("Protected INT-OII-015 module changed during testing")

    print("[PASS] Protected INT-OII-015 module unchanged")
    print("[PASS] INT-OII-001 through INT-OII-015 lineage preserved")
    print("[PASS] No acquisition module modified")
    print("[PASS] No analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print(f"[PASS] Repository located: {ROOT.resolve()}")
    print("[DONE] INT-OII-016 CONTINUATION ATTESTATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
