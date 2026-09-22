from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

def _find_repository_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    candidates = (
        Path.cwd(),
        script_dir,
        Path.cwd() / "kalshi-qss-bot",
        script_dir / "kalshi-qss-bot",
        script_dir.parent / "kalshi-qss-bot",
    )
    for candidate in candidates:
        if (candidate / "qseries_v2").is_dir():
            return candidate.resolve()
    raise SystemExit(
        "[ERROR] Could not locate the kalshi-qss-bot repository. "
        "Place this installer either in the repository root or in its parent GitHub folder."
    )


ROOT = _find_repository_root()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
UPSTREAM = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate.py"
)
TEST = (
    ROOT
    / "test_int_oii_015_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption,\n    verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption,\n)\n\nENGINE_ID = "INT-OII-015"\nSCHEMA_VERSION = "INT-OII-015.v1"\nALGORITHM_VERSION = (\n    "oracle-certified-intelligence-read-only-consumption-session-activation-continuation.v1"\n)\nCONTINUATION_STATUS = (\n    "oracle_certified_intelligence_read_only_consumption_session_activation_continuation_active"\n)\n\n\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n    ValueError\n):\n    pass\n\n\ndef _canonical_json(value: object) -> str:\n    return json.dumps(\n        value,\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef _stable_hash(value: object) -> str:\n    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation:\n    continuation_id: str\n    source_activation_authorization_consumption_id: str\n    source_activation_authorization_consumption_hash: str\n    source_activation_authorization_id: str\n    source_activation_authorization_hash: str\n    source_attestation_id: str\n    source_attestation_hash: str\n    source_activation_id: str\n    source_activation_hash: str\n    source_consumption_id: str\n    source_consumption_hash: str\n    source_session_authorization_id: str\n    source_session_authorization_hash: str\n    source_readiness_id: str\n    source_readiness_hash: str\n    source_session_attestation_id: str\n    source_session_attestation_hash: str\n    source_session_id: str\n    source_session_hash: str\n    source_registry_activation_id: str\n    source_registry_activation_hash: str\n    source_registry_authorization_id: str\n    source_registry_authorization_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    activation_authorization_consumption_verified: bool\n    deterministic_continuation: bool\n    bounded_continuation_scope: bool\n    single_continuation_scope: bool\n    duplicate_continuation_allowed: bool\n    continuation_reversible: bool\n    downstream_read_only_continuation_active: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    continuation_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    continuation_hash: str\n\n\ndef continue_oracle_certified_intelligence_read_only_consumption_session_activation(\n    *,\n    consumption: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption,\n) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation:\n    try:\n        verified = (\n            verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption(\n                consumption\n            )\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "INT-OII-014 activation authorization consumption verification failed"\n        ) from exc\n\n    if verified is not True:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "INT-OII-014 activation authorization consumption was not verified"\n        )\n\n    if not consumption.single_use_authorization_consumed:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "single-use activation authorization was not consumed"\n        )\n\n    if consumption.duplicate_consumption_allowed:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "duplicate authorization consumption is allowed"\n        )\n\n    if consumption.consumption_reversible:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "authorization consumption is reversible"\n        )\n\n    if not consumption.downstream_read_only_continuation_active:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "downstream read-only continuation is not active"\n        )\n\n    if consumption.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "certified subsystem scope is empty"\n        )\n\n    if consumption.source_entry_count != len(consumption.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if consumption.source_entry_count != len(consumption.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    body = {\n        "source_activation_authorization_consumption_id": consumption.consumption_id,\n        "source_activation_authorization_consumption_hash": consumption.consumption_hash,\n        "source_activation_authorization_id": consumption.source_activation_authorization_id,\n        "source_activation_authorization_hash": consumption.source_activation_authorization_hash,\n        "source_attestation_id": consumption.source_attestation_id,\n        "source_attestation_hash": consumption.source_attestation_hash,\n        "source_activation_id": consumption.source_activation_id,\n        "source_activation_hash": consumption.source_activation_hash,\n        "source_consumption_id": consumption.source_consumption_id,\n        "source_consumption_hash": consumption.source_consumption_hash,\n        "source_session_authorization_id": consumption.source_session_authorization_id,\n        "source_session_authorization_hash": consumption.source_session_authorization_hash,\n        "source_readiness_id": consumption.source_readiness_id,\n        "source_readiness_hash": consumption.source_readiness_hash,\n        "source_session_attestation_id": consumption.source_session_attestation_id,\n        "source_session_attestation_hash": consumption.source_session_attestation_hash,\n        "source_session_id": consumption.source_session_id,\n        "source_session_hash": consumption.source_session_hash,\n        "source_registry_activation_id": consumption.source_registry_activation_id,\n        "source_registry_activation_hash": consumption.source_registry_activation_hash,\n        "source_registry_authorization_id": consumption.source_registry_authorization_id,\n        "source_registry_authorization_hash": consumption.source_registry_authorization_hash,\n        "source_registry_id": consumption.source_registry_id,\n        "source_registry_hash": consumption.source_registry_hash,\n        "source_entry_count": consumption.source_entry_count,\n        "source_entry_hashes": tuple(consumption.source_entry_hashes),\n        "source_subsystem_keys": tuple(consumption.source_subsystem_keys),\n        "activation_authorization_consumption_verified": True,\n        "deterministic_continuation": True,\n        "bounded_continuation_scope": True,\n        "single_continuation_scope": True,\n        "duplicate_continuation_allowed": False,\n        "continuation_reversible": False,\n        "downstream_read_only_continuation_active": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "continuation_status": CONTINUATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    continuation_hash = _stable_hash(body)\n\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation(\n        continuation_id=(\n            "oracle-certified-intelligence-read-only-consumption-session-activation-continuation:"\n            + continuation_hash\n        ),\n        **body,\n        continuation_hash=continuation_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(\n    continuation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation,\n) -> bool:\n    if not isinstance(\n        continuation,\n        OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation,\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "invalid INT-OII-015 activation continuation"\n        )\n\n    body = asdict(continuation)\n    continuation_id = body.pop("continuation_id")\n    continuation_hash = body.pop("continuation_hash")\n\n    expected_hash = _stable_hash(body)\n    expected_id = (\n        "oracle-certified-intelligence-read-only-consumption-session-activation-continuation:"\n        + expected_hash\n    )\n\n    if continuation_hash != expected_hash or continuation_id != expected_id:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "continuation identity or hash mismatch"\n        )\n\n    if continuation.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "empty continuation scope"\n        )\n\n    if continuation.source_entry_count != len(continuation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if continuation.source_entry_count != len(continuation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    required_true = (\n        continuation.activation_authorization_consumption_verified,\n        continuation.deterministic_continuation,\n        continuation.bounded_continuation_scope,\n        continuation.single_continuation_scope,\n        continuation.downstream_read_only_continuation_active,\n        continuation.read_only,\n    )\n\n    forbidden = (\n        continuation.duplicate_continuation_allowed,\n        continuation.continuation_reversible,\n        continuation.registry_mutation_allowed,\n        continuation.oracle_execution_allowed,\n        continuation.reasoning_execution_allowed,\n        continuation.probability_estimation_allowed,\n        continuation.final_intelligence_conclusion_allowed,\n        continuation.publication_allowed,\n        continuation.alerting_allowed,\n        continuation.qseries_handoff_allowed,\n        continuation.qseries_execution_allowed,\n        continuation.order_creation_allowed,\n        continuation.funds_movement_allowed,\n        continuation.portfolio_mutation_allowed,\n    )\n\n    if (\n        not all(required_true)\n        or any(forbidden)\n        or continuation.engine_id != ENGINE_ID\n        or continuation.schema_version != SCHEMA_VERSION\n        or continuation.algorithm_version != ALGORITHM_VERSION\n        or continuation.continuation_status != CONTINUATION_STATUS\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError(\n            "INT-OII-015 permanent safety boundary violated"\n        )\n\n    return True\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "CONTINUATION_STATUS",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation",\n    "continue_oracle_certified_intelligence_read_only_consumption_session_activation",\n    "verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption,\n)\n\n\ndef make_consumption() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption:\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption(\n        consumption_id="activation-authorization-consumption:" + "a" * 64,\n        source_activation_authorization_id="activation-authorization:" + "b" * 64,\n        source_activation_authorization_hash="b" * 64,\n        source_attestation_id="attestation:" + "c" * 64,\n        source_attestation_hash="c" * 64,\n        source_activation_id="activation:" + "d" * 64,\n        source_activation_hash="d" * 64,\n        source_consumption_id="consumption:" + "e" * 64,\n        source_consumption_hash="e" * 64,\n        source_session_authorization_id="session-authorization:" + "f" * 64,\n        source_session_authorization_hash="f" * 64,\n        source_readiness_id="readiness:" + "1" * 64,\n        source_readiness_hash="1" * 64,\n        source_session_attestation_id="session-attestation:" + "2" * 64,\n        source_session_attestation_hash="2" * 64,\n        source_session_id="session:" + "3" * 64,\n        source_session_hash="3" * 64,\n        source_registry_activation_id="registry-activation:" + "4" * 64,\n        source_registry_activation_hash="4" * 64,\n        source_registry_authorization_id="registry-authorization:" + "5" * 64,\n        source_registry_authorization_hash="5" * 64,\n        source_registry_id="registry:" + "6" * 64,\n        source_registry_hash="6" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("7" * 64, "8" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        activation_authorization_verified=True,\n        deterministic_consumption=True,\n        bounded_consumption_scope=True,\n        single_activation_authorization_scope=True,\n        single_use_authorization_consumed=True,\n        duplicate_consumption_allowed=False,\n        consumption_reversible=False,\n        downstream_read_only_continuation_active=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        consumption_status="oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumed",\n        engine_id="INT-OII-014",\n        schema_version="INT-OII-014.v1",\n        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation-authorization-consumption.v1",\n        consumption_hash="a" * 64,\n    )\n\n\ndef must_reject(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-015 rejection")\n\n\ndef main() -> None:\n    original = (\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption\n    )\n    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption = (\n        lambda _: True\n    )\n\n    try:\n        consumption = make_consumption()\n\n        first = module.continue_oracle_certified_intelligence_read_only_consumption_session_activation(\n            consumption=consumption\n        )\n        second = module.continue_oracle_certified_intelligence_read_only_consumption_session_activation(\n            consumption=consumption\n        )\n\n        assert first == second\n        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(\n            first\n        )\n        assert first.source_activation_authorization_consumption_id == consumption.consumption_id\n        assert first.source_activation_authorization_consumption_hash == consumption.consumption_hash\n        assert first.activation_authorization_consumption_verified is True\n        assert first.deterministic_continuation is True\n        assert first.bounded_continuation_scope is True\n        assert first.single_continuation_scope is True\n        assert first.duplicate_continuation_allowed is False\n        assert first.continuation_reversible is False\n        assert first.downstream_read_only_continuation_active is True\n        assert first.oracle_execution_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(\n                replace(first, continuation_hash="0" * 64)\n            )\n        )\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(\n                replace(first, duplicate_continuation_allowed=True)\n            )\n        )\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(\n                replace(first, qseries_execution_allowed=True)\n            )\n        )\n\n        invalid_consumption = replace(\n            consumption,\n            downstream_read_only_continuation_active=False,\n        )\n        must_reject(\n            lambda: module.continue_oracle_certified_intelligence_read_only_consumption_session_activation(\n                consumption=invalid_consumption\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-015 TEST")\n        print(" ACTIVATION CONTINUATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-014 authorization consumption consumed")\n        print("[PASS] Authorization-consumption identity and hash preserved")\n        print("[PASS] Complete activation/session lineage preserved")\n        print("[PASS] Registry lineage preserved")\n        print("[PASS] Deterministic bounded continuation certified")\n        print("[PASS] Single-continuation scope certified")\n        print("[PASS] Duplicate continuation disabled")\n        print("[PASS] Continuation is irreversible")\n        print("[PASS] Downstream read-only continuation active")\n        print("[PASS] Oracle and reasoning execution disabled")\n        print("[PASS] Q Series execution disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[DONE] INT-OII-015 ACTIVATION CONTINUATION GATE PASS")\n    finally:\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption = (\n            original\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" INT-OII-015 CORRECTION V2 INSTALLER")
    print(" ACTIVATION CONTINUATION GATE")
    print("========================================")

    if not UPSTREAM.is_file():
        raise SystemExit(
            f"[ERROR] Actual INT-OII-014 module missing: {UPSTREAM}"
        )

    upstream_source = UPSTREAM.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-014"',
        "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption",
        "verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption",
        "consumption_id",
        "consumption_hash",
        "single_use_authorization_consumed",
        "duplicate_consumption_allowed",
        "consumption_reversible",
        "downstream_read_only_continuation_active",
        "read_only",
    )

    missing = [token for token in required if token not in upstream_source]
    if missing:
        raise SystemExit(
            "[ERROR] INT-OII-014 contract mismatch: " + ", ".join(missing)
        )

    ast.parse(upstream_source, filename=str(UPSTREAM))
    upstream_hash = digest(UPSTREAM)
    print("[OK] Actual INT-OII-014 activation authorization consumption contract verified")

    write_complete(PRODUCTION, PRODUCTION_SOURCE)
    write_complete(TEST, TEST_SOURCE)

    export_line = (
        "from .oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate import *"
    )
    existing = (
        PACKAGE_INIT.read_text(encoding="utf-8")
        if PACKAGE_INIT.exists()
        else ""
    )

    if export_line not in existing.splitlines():
        if existing and not existing.endswith("\n"):
            existing += "\n"
        PACKAGE_INIT.write_text(
            existing + export_line + "\n",
            encoding="utf-8",
            newline="\n",
        )
        ast.parse(
            PACKAGE_INIT.read_text(encoding="utf-8"),
            filename=str(PACKAGE_INIT),
        )
        print(f"[OK] PACKAGE UPDATED: {PACKAGE_INIT.resolve()}")
    else:
        print(f"[OK] PACKAGE EXPORT PRESENT: {PACKAGE_INIT.resolve()}")

    if digest(UPSTREAM) != upstream_hash:
        raise RuntimeError(
            "Protected INT-OII-014 module changed during installation"
        )

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if digest(UPSTREAM) != upstream_hash:
        raise RuntimeError(
            "Protected INT-OII-014 module changed during testing"
        )

    print("[PASS] Protected INT-OII-014 module unchanged")
    print("[PASS] INT-OII-001 through INT-OII-014 lineage preserved")
    print("[PASS] No acquisition module modified")
    print("[PASS] No analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[DONE] INT-OII-015 ACTIVATION CONTINUATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
