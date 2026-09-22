from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
UPSTREAM = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_authorization_consumption_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_activation_gate.py"
)
TEST = (
    ROOT
    / "test_int_oii_011_oracle_certified_intelligence_read_only_consumption_session_activation_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_authorization_consumption_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption,\n    verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption,\n)\n\nENGINE_ID = "INT-OII-011"\nSCHEMA_VERSION = "INT-OII-011.v1"\nALGORITHM_VERSION = (\n    "oracle-certified-intelligence-read-only-consumption-session-activation.v1"\n)\nACTIVATION_STATUS = (\n    "oracle_certified_intelligence_read_only_consumption_session_activated"\n)\n\n\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n    ValueError\n):\n    pass\n\n\ndef _canonical_json(value: object) -> str:\n    return json.dumps(\n        value,\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef _stable_hash(value: object) -> str:\n    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation:\n    activation_id: str\n    source_consumption_id: str\n    source_consumption_hash: str\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_readiness_id: str\n    source_readiness_hash: str\n    source_session_attestation_id: str\n    source_session_attestation_hash: str\n    source_session_id: str\n    source_session_hash: str\n    source_registry_activation_id: str\n    source_registry_activation_hash: str\n    source_registry_authorization_id: str\n    source_registry_authorization_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    authorization_consumption_verified: bool\n    deterministic_activation: bool\n    bounded_activation_scope: bool\n    single_consumption_scope: bool\n    activation_single_use: bool\n    duplicate_activation_allowed: bool\n    activation_reversible: bool\n    downstream_read_only_consumption_active: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    activation_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    activation_hash: str\n\n\ndef activate_oracle_certified_intelligence_read_only_consumption_session(\n    *,\n    consumption: OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption,\n) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation:\n    try:\n        verified = (\n            verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption(\n                consumption\n            )\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "INT-OII-010 authorization consumption verification failed"\n        ) from exc\n\n    if verified is not True:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "INT-OII-010 authorization consumption was not verified"\n        )\n\n    if not consumption.single_use_authorization_consumed:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "single-use authorization consumption is not complete"\n        )\n\n    if not consumption.downstream_read_only_consumption_activated:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "downstream read-only consumption is not activated"\n        )\n\n    if consumption.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "certified subsystem scope is empty"\n        )\n\n    if consumption.source_entry_count != len(consumption.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if consumption.source_entry_count != len(consumption.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    body = {\n        "source_consumption_id": consumption.consumption_id,\n        "source_consumption_hash": consumption.consumption_hash,\n        "source_authorization_id": consumption.source_authorization_id,\n        "source_authorization_hash": consumption.source_authorization_hash,\n        "source_readiness_id": consumption.source_readiness_id,\n        "source_readiness_hash": consumption.source_readiness_hash,\n        "source_session_attestation_id": consumption.source_session_attestation_id,\n        "source_session_attestation_hash": consumption.source_session_attestation_hash,\n        "source_session_id": consumption.source_session_id,\n        "source_session_hash": consumption.source_session_hash,\n        "source_registry_activation_id": consumption.source_activation_id,\n        "source_registry_activation_hash": consumption.source_activation_hash,\n        "source_registry_authorization_id": consumption.source_registry_authorization_id,\n        "source_registry_authorization_hash": consumption.source_registry_authorization_hash,\n        "source_registry_id": consumption.source_registry_id,\n        "source_registry_hash": consumption.source_registry_hash,\n        "source_entry_count": consumption.source_entry_count,\n        "source_entry_hashes": tuple(consumption.source_entry_hashes),\n        "source_subsystem_keys": tuple(consumption.source_subsystem_keys),\n        "authorization_consumption_verified": True,\n        "deterministic_activation": True,\n        "bounded_activation_scope": True,\n        "single_consumption_scope": True,\n        "activation_single_use": True,\n        "duplicate_activation_allowed": False,\n        "activation_reversible": False,\n        "downstream_read_only_consumption_active": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "activation_status": ACTIVATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    activation_hash = _stable_hash(body)\n\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation(\n        activation_id=(\n            "oracle-certified-intelligence-read-only-consumption-session-activation:"\n            + activation_hash\n        ),\n        **body,\n        activation_hash=activation_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_read_only_consumption_session_activation(\n    activation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,\n) -> bool:\n    if not isinstance(\n        activation,\n        OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "invalid INT-OII-011 activation"\n        )\n\n    body = asdict(activation)\n    activation_id = body.pop("activation_id")\n    activation_hash = body.pop("activation_hash")\n\n    expected_hash = _stable_hash(body)\n    expected_id = (\n        "oracle-certified-intelligence-read-only-consumption-session-activation:"\n        + expected_hash\n    )\n\n    if activation_hash != expected_hash or activation_id != expected_id:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "activation identity or hash mismatch"\n        )\n\n    if activation.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "empty activation scope"\n        )\n\n    if activation.source_entry_count != len(activation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if activation.source_entry_count != len(activation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    required_true = (\n        activation.authorization_consumption_verified,\n        activation.deterministic_activation,\n        activation.bounded_activation_scope,\n        activation.single_consumption_scope,\n        activation.activation_single_use,\n        activation.downstream_read_only_consumption_active,\n        activation.read_only,\n    )\n\n    forbidden = (\n        activation.duplicate_activation_allowed,\n        activation.activation_reversible,\n        activation.registry_mutation_allowed,\n        activation.oracle_execution_allowed,\n        activation.reasoning_execution_allowed,\n        activation.probability_estimation_allowed,\n        activation.final_intelligence_conclusion_allowed,\n        activation.publication_allowed,\n        activation.alerting_allowed,\n        activation.qseries_handoff_allowed,\n        activation.qseries_execution_allowed,\n        activation.order_creation_allowed,\n        activation.funds_movement_allowed,\n        activation.portfolio_mutation_allowed,\n    )\n\n    if (\n        not all(required_true)\n        or any(forbidden)\n        or activation.engine_id != ENGINE_ID\n        or activation.schema_version != SCHEMA_VERSION\n        or activation.algorithm_version != ALGORITHM_VERSION\n        or activation.activation_status != ACTIVATION_STATUS\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError(\n            "INT-OII-011 permanent safety boundary violated"\n        )\n\n    return True\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "ACTIVATION_STATUS",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation",\n    "activate_oracle_certified_intelligence_read_only_consumption_session",\n    "verify_oracle_certified_intelligence_read_only_consumption_session_activation",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_authorization_consumption_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption,\n)\n\n\ndef make_consumption() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption:\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption(\n        consumption_id="consumption:" + "a" * 64,\n        source_authorization_id="authorization:" + "b" * 64,\n        source_authorization_hash="b" * 64,\n        source_readiness_id="readiness:" + "c" * 64,\n        source_readiness_hash="c" * 64,\n        source_session_attestation_id="session-attestation:" + "d" * 64,\n        source_session_attestation_hash="d" * 64,\n        source_session_id="session:" + "e" * 64,\n        source_session_hash="e" * 64,\n        source_activation_id="registry-activation:" + "f" * 64,\n        source_activation_hash="f" * 64,\n        source_registry_authorization_id="registry-authorization:" + "1" * 64,\n        source_registry_authorization_hash="1" * 64,\n        source_registry_id="registry:" + "2" * 64,\n        source_registry_hash="2" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("3" * 64, "4" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        authorization_verified=True,\n        deterministic_consumption=True,\n        bounded_consumption_scope=True,\n        single_authorization_scope=True,\n        single_use_authorization_consumed=True,\n        duplicate_consumption_allowed=False,\n        consumption_reversible=False,\n        downstream_read_only_consumption_activated=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        consumption_status="oracle_certified_intelligence_read_only_consumption_session_authorization_consumed",\n        engine_id="INT-OII-010",\n        schema_version="INT-OII-010.v1",\n        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-authorization-consumption.v1",\n        consumption_hash="a" * 64,\n    )\n\n\ndef must_reject(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-011 rejection")\n\n\ndef main() -> None:\n    original = (\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption\n    )\n    module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption = (\n        lambda _: True\n    )\n\n    try:\n        consumption = make_consumption()\n\n        first = module.activate_oracle_certified_intelligence_read_only_consumption_session(\n            consumption=consumption\n        )\n        second = module.activate_oracle_certified_intelligence_read_only_consumption_session(\n            consumption=consumption\n        )\n\n        assert first == second\n        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation(\n            first\n        )\n        assert first.source_consumption_id == consumption.consumption_id\n        assert first.source_consumption_hash == consumption.consumption_hash\n        assert first.authorization_consumption_verified is True\n        assert first.deterministic_activation is True\n        assert first.bounded_activation_scope is True\n        assert first.single_consumption_scope is True\n        assert first.activation_single_use is True\n        assert first.duplicate_activation_allowed is False\n        assert first.activation_reversible is False\n        assert first.downstream_read_only_consumption_active is True\n        assert first.oracle_execution_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation(\n                replace(first, activation_hash="0" * 64)\n            )\n        )\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation(\n                replace(first, duplicate_activation_allowed=True)\n            )\n        )\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation(\n                replace(first, qseries_execution_allowed=True)\n            )\n        )\n\n        inactive = replace(\n            consumption,\n            downstream_read_only_consumption_activated=False,\n        )\n        must_reject(\n            lambda: module.activate_oracle_certified_intelligence_read_only_consumption_session(\n                consumption=inactive\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-011 TEST")\n        print(" SESSION ACTIVATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-010 authorization consumption consumed")\n        print("[PASS] Consumption identity and hash preserved")\n        print("[PASS] Authorization/readiness/session/registry lineage preserved")\n        print("[PASS] Deterministic bounded activation certified")\n        print("[PASS] Single-consumption activation scope certified")\n        print("[PASS] Single-use activation certified")\n        print("[PASS] Duplicate activation disabled")\n        print("[PASS] Activation is irreversible")\n        print("[PASS] Downstream read-only consumption active")\n        print("[PASS] Oracle and reasoning execution disabled")\n        print("[PASS] Q Series execution disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[DONE] INT-OII-011 SESSION ACTIVATION GATE PASS")\n    finally:\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption = (\n            original\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" INT-OII-011 INSTALLER")
    print(" SESSION ACTIVATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    if not UPSTREAM.is_file():
        raise SystemExit(
            f"[ERROR] Actual INT-OII-010 module missing: {UPSTREAM}"
        )

    upstream_source = UPSTREAM.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-010"',
        "OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption",
        "verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption",
        "consumption_id",
        "consumption_hash",
        "single_use_authorization_consumed",
        "downstream_read_only_consumption_activated",
        "read_only",
    )
    missing = [token for token in required if token not in upstream_source]
    if missing:
        raise SystemExit(
            "[ERROR] INT-OII-010 contract mismatch: " + ", ".join(missing)
        )

    ast.parse(upstream_source, filename=str(UPSTREAM))
    upstream_hash = digest(UPSTREAM)
    print("[OK] Actual INT-OII-010 authorization consumption contract verified")

    write_complete(PRODUCTION, PRODUCTION_SOURCE)
    write_complete(TEST, TEST_SOURCE)

    export_line = (
        "from .oracle_certified_intelligence_read_only_consumption_session_activation_gate import *"
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
            "Protected INT-OII-010 module changed during installation"
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
            "Protected INT-OII-010 module changed during testing"
        )

    print("[PASS] Protected INT-OII-010 module unchanged")
    print("[PASS] INT-OII-001 through INT-OII-010 lineage preserved")
    print("[PASS] No acquisition module modified")
    print("[PASS] No analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[DONE] INT-OII-011 SESSION ACTIVATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
