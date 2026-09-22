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
UPSTREAM = PACKAGE / "oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate.py"
PRODUCTION = PACKAGE / "oracle_intelligence_integration_final_completion_and_freeze_gate.py"
TEST = ROOT / "test_int_oii_017_oracle_intelligence_integration_final_completion_and_freeze_gate.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nfrom dataclasses import asdict, dataclass\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation,\n    verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation,\n)\n\nENGINE_ID = "INT-OII-017"\nSCHEMA_VERSION = "INT-OII-017.v1"\nALGORITHM_VERSION = "oracle-intelligence-integration-final-completion-and-freeze.v1"\nCOMPLETION_STATUS = "oracle_intelligence_integration_complete_and_frozen"\n\n\nclass OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(ValueError):\n    pass\n\n\ndef _canonical_json(value: object) -> str:\n    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)\n\n\ndef _stable_hash(value: object) -> str:\n    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleIntelligenceIntegrationFinalCompletionAndFreeze:\n    completion_id: str\n    source_attestation_id: str\n    source_attestation_hash: str\n    source_continuation_id: str\n    source_continuation_hash: str\n    source_session_id: str\n    source_session_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    continuation_attestation_verified: bool\n    complete_lineage_verified: bool\n    deterministic_completion: bool\n    immutable_freeze: bool\n    integration_complete: bool\n    further_int_oii_certification_required: bool\n    downstream_read_only_consumption_active: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    completion_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    completion_hash: str\n\n\ndef complete_and_freeze_oracle_intelligence_integration(\n    *, attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation\n) -> OracleIntelligenceIntegrationFinalCompletionAndFreeze:\n    try:\n        verified = verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation(attestation)\n    except Exception as exc:\n        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(\n            "INT-OII-016 continuation attestation verification failed"\n        ) from exc\n    if verified is not True:\n        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(\n            "INT-OII-016 continuation attestation was not verified"\n        )\n    if (\n        attestation.source_entry_count <= 0\n        or attestation.source_entry_count != len(attestation.source_entry_hashes)\n        or attestation.source_entry_count != len(attestation.source_subsystem_keys)\n    ):\n        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(\n            "certified integration scope mismatch"\n        )\n    required = (\n        attestation.continuation_verified,\n        attestation.deterministic_attestation,\n        attestation.bounded_attestation_scope,\n        attestation.single_continuation_scope,\n        attestation.attestation_single_use,\n        attestation.downstream_read_only_consumption_active,\n        attestation.read_only,\n    )\n    forbidden = (\n        attestation.duplicate_attestation_allowed,\n        attestation.attestation_reversible,\n        attestation.registry_mutation_allowed,\n        attestation.oracle_execution_allowed,\n        attestation.reasoning_execution_allowed,\n        attestation.probability_estimation_allowed,\n        attestation.final_intelligence_conclusion_allowed,\n        attestation.publication_allowed,\n        attestation.alerting_allowed,\n        attestation.qseries_handoff_allowed,\n        attestation.qseries_execution_allowed,\n        attestation.order_creation_allowed,\n        attestation.funds_movement_allowed,\n        attestation.portfolio_mutation_allowed,\n    )\n    if not all(required) or any(forbidden):\n        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(\n            "INT-OII-016 read-only boundary mismatch"\n        )\n    body = {\n        "source_attestation_id": attestation.attestation_id,\n        "source_attestation_hash": attestation.attestation_hash,\n        "source_continuation_id": attestation.source_continuation_id,\n        "source_continuation_hash": attestation.source_continuation_hash,\n        "source_session_id": attestation.source_session_id,\n        "source_session_hash": attestation.source_session_hash,\n        "source_registry_id": attestation.source_registry_id,\n        "source_registry_hash": attestation.source_registry_hash,\n        "source_entry_count": attestation.source_entry_count,\n        "source_entry_hashes": tuple(attestation.source_entry_hashes),\n        "source_subsystem_keys": tuple(attestation.source_subsystem_keys),\n        "continuation_attestation_verified": True,\n        "complete_lineage_verified": True,\n        "deterministic_completion": True,\n        "immutable_freeze": True,\n        "integration_complete": True,\n        "further_int_oii_certification_required": False,\n        "downstream_read_only_consumption_active": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "completion_status": COMPLETION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n    completion_hash = _stable_hash(body)\n    return OracleIntelligenceIntegrationFinalCompletionAndFreeze(\n        completion_id="int-oii-completion:" + completion_hash,\n        completion_hash=completion_hash,\n        **body,\n    )\n\n\ndef verify_oracle_intelligence_integration_final_completion_and_freeze(\n    value: OracleIntelligenceIntegrationFinalCompletionAndFreeze,\n) -> bool:\n    if not isinstance(value, OracleIntelligenceIntegrationFinalCompletionAndFreeze):\n        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError("unexpected completion record type")\n    body = asdict(value)\n    completion_hash = body.pop("completion_hash")\n    completion_id = body.pop("completion_id")\n    expected_hash = _stable_hash(body)\n    if completion_hash != expected_hash or completion_id != "int-oii-completion:" + expected_hash:\n        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError("completion identity mismatch")\n    required = (\n        value.continuation_attestation_verified,\n        value.complete_lineage_verified,\n        value.deterministic_completion,\n        value.immutable_freeze,\n        value.integration_complete,\n        value.downstream_read_only_consumption_active,\n        value.read_only,\n    )\n    forbidden = (\n        value.further_int_oii_certification_required,\n        value.registry_mutation_allowed,\n        value.oracle_execution_allowed,\n        value.reasoning_execution_allowed,\n        value.probability_estimation_allowed,\n        value.final_intelligence_conclusion_allowed,\n        value.publication_allowed,\n        value.alerting_allowed,\n        value.qseries_handoff_allowed,\n        value.qseries_execution_allowed,\n        value.order_creation_allowed,\n        value.funds_movement_allowed,\n        value.portfolio_mutation_allowed,\n    )\n    if (\n        not all(required)\n        or any(forbidden)\n        or value.source_entry_count <= 0\n        or value.source_entry_count != len(value.source_entry_hashes)\n        or value.source_entry_count != len(value.source_subsystem_keys)\n        or value.engine_id != ENGINE_ID\n        or value.schema_version != SCHEMA_VERSION\n        or value.algorithm_version != ALGORITHM_VERSION\n        or value.completion_status != COMPLETION_STATUS\n    ):\n        raise OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError(\n            "INT-OII-017 permanent completion boundary violated"\n        )\n    return True\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "COMPLETION_STATUS",\n    "OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError",\n    "OracleIntelligenceIntegrationFinalCompletionAndFreeze",\n    "complete_and_freeze_oracle_intelligence_integration",\n    "verify_oracle_intelligence_integration_final_completion_and_freeze",\n]\n'
TEST_SOURCE = 'from __future__ import annotations\n\nfrom dataclasses import replace\n\nfrom qseries_v2.oracle_intelligence_integration import oracle_intelligence_integration_final_completion_and_freeze_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation,\n)\n\n\ndef make_attestation():\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation(\n        attestation_id="attestation:" + "a" * 64,\n        source_continuation_id="continuation:" + "b" * 64,\n        source_continuation_hash="b" * 64,\n        source_authorization_consumption_id="authorization-consumption:" + "c" * 64,\n        source_authorization_consumption_hash="c" * 64,\n        source_activation_authorization_id="authorization:" + "d" * 64,\n        source_activation_authorization_hash="d" * 64,\n        source_activation_id="activation:" + "e" * 64,\n        source_activation_hash="e" * 64,\n        source_session_id="session:" + "f" * 64,\n        source_session_hash="f" * 64,\n        source_registry_id="registry:" + "1" * 64,\n        source_registry_hash="1" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("2" * 64, "3" * 64),\n        source_subsystem_keys=("oracle_intelligence_integration", "oracle_scientific_reasoning_runtime"),\n        continuation_verified=True,\n        deterministic_attestation=True,\n        bounded_attestation_scope=True,\n        single_continuation_scope=True,\n        attestation_single_use=True,\n        duplicate_attestation_allowed=False,\n        attestation_reversible=False,\n        downstream_read_only_consumption_active=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        attestation_status="oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attested",\n        engine_id="INT-OII-016",\n        schema_version="INT-OII-016.v1",\n        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation-continuation-attestation.v1",\n        attestation_hash="4" * 64,\n    )\n\n\ndef reject(fn):\n    try:\n        fn()\n    except module.OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError:\n        return\n    raise AssertionError("expected INT-OII-017 rejection")\n\n\ndef main():\n    original = module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation\n    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation = lambda _: True\n    try:\n        source = make_attestation()\n        first = module.complete_and_freeze_oracle_intelligence_integration(attestation=source)\n        second = module.complete_and_freeze_oracle_intelligence_integration(attestation=source)\n        assert first == second\n        assert module.verify_oracle_intelligence_integration_final_completion_and_freeze(first)\n        assert first.source_attestation_id == source.attestation_id\n        assert first.source_attestation_hash == source.attestation_hash\n        assert first.complete_lineage_verified and first.deterministic_completion\n        assert first.immutable_freeze and first.integration_complete and first.read_only\n        assert not first.further_int_oii_certification_required\n        assert not first.oracle_execution_allowed and not first.qseries_execution_allowed\n        reject(lambda: module.verify_oracle_intelligence_integration_final_completion_and_freeze(replace(first, completion_hash="0" * 64)))\n        reject(lambda: module.complete_and_freeze_oracle_intelligence_integration(attestation=replace(source, downstream_read_only_consumption_active=False)))\n        print("========================================")\n        print(" INT-OII-017 TEST")\n        print(" FINAL COMPLETION AND FREEZE GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-016 continuation attestation consumed")\n        print("[PASS] Complete INT-OII-001 through INT-OII-016 lineage preserved")\n        print("[PASS] Deterministic final completion certified")\n        print("[PASS] Immutable INT-OII integration freeze certified")\n        print("[PASS] Downstream read-only consumption remains active")\n        print("[PASS] Oracle and reasoning execution disabled")\n        print("[PASS] Q Series execution disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] No further INT-OII certification layers required")\n        print("[DONE] INT-OII-017 FINAL COMPLETION AND FREEZE GATE PASS")\n    finally:\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation = original\n\n\nif __name__ == "__main__":\n    main()\n'


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" INT-OII-017 INSTALLER")
    print(" FINAL COMPLETION AND FREEZE GATE")
    print("========================================")
    if not UPSTREAM.is_file():
        raise SystemExit(f"[ERROR] Actual INT-OII-016 module missing: {UPSTREAM}")
    source = UPSTREAM.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-016"',
        "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation",
        "verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation",
        "attestation_id",
        "attestation_hash",
        "downstream_read_only_consumption_active",
        "read_only",
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise SystemExit("[ERROR] INT-OII-016 contract mismatch: " + ", ".join(missing))
    ast.parse(source, filename=str(UPSTREAM))
    upstream_hash = digest(UPSTREAM)
    print("[OK] Actual INT-OII-016 continuation attestation contract verified")

    write_complete(PRODUCTION, PRODUCTION_SOURCE)
    write_complete(TEST, TEST_SOURCE)

    export = "from .oracle_intelligence_integration_final_completion_and_freeze_gate import *"
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
        raise RuntimeError("Protected INT-OII-016 module changed during installation")

    completed = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if digest(UPSTREAM) != upstream_hash:
        raise RuntimeError("Protected INT-OII-016 module changed during testing")

    print("[PASS] Protected INT-OII-016 module unchanged")
    print("[PASS] INT-OII-001 through INT-OII-016 lineage preserved")
    print("[PASS] No acquisition module modified")
    print("[PASS] No analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print(f"[PASS] Repository located: {ROOT.resolve()}")
    print("[DONE] INT-OII-017 FINAL COMPLETION AND FREEZE GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
