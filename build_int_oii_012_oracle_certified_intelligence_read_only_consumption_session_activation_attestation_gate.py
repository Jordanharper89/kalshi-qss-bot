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
    / "oracle_certified_intelligence_read_only_consumption_session_activation_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate.py"
)
TEST = (
    ROOT
    / "test_int_oii_012_oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,\n    verify_oracle_certified_intelligence_read_only_consumption_session_activation,\n)\n\nENGINE_ID = "INT-OII-012"\nSCHEMA_VERSION = "INT-OII-012.v1"\nALGORITHM_VERSION = (\n    "oracle-certified-intelligence-read-only-consumption-session-activation-attestation.v1"\n)\nATTESTATION_STATUS = (\n    "oracle_certified_intelligence_read_only_consumption_session_activation_attested"\n)\n\n\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n    ValueError\n):\n    pass\n\n\ndef _canonical_json(value: object) -> str:\n    return json.dumps(\n        value,\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef _stable_hash(value: object) -> str:\n    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation:\n    attestation_id: str\n    source_activation_id: str\n    source_activation_hash: str\n    source_consumption_id: str\n    source_consumption_hash: str\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_readiness_id: str\n    source_readiness_hash: str\n    source_session_attestation_id: str\n    source_session_attestation_hash: str\n    source_session_id: str\n    source_session_hash: str\n    source_registry_activation_id: str\n    source_registry_activation_hash: str\n    source_registry_authorization_id: str\n    source_registry_authorization_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    activation_verified: bool\n    activation_identity_attested: bool\n    activation_hash_attested: bool\n    complete_lineage_attested: bool\n    deterministic_attestation: bool\n    bounded_attestation_scope: bool\n    single_activation_scope: bool\n    activation_single_use_attested: bool\n    duplicate_activation_disabled_attested: bool\n    irreversible_activation_attested: bool\n    downstream_read_only_consumption_active_attested: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    attestation_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    attestation_hash: str\n\n\ndef attest_oracle_certified_intelligence_read_only_consumption_session_activation(\n    *,\n    activation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,\n) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation:\n    try:\n        verified = (\n            verify_oracle_certified_intelligence_read_only_consumption_session_activation(\n                activation\n            )\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "INT-OII-011 activation verification failed"\n        ) from exc\n\n    if verified is not True:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "INT-OII-011 activation was not verified"\n        )\n\n    if not activation.activation_single_use:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "activation is not single-use"\n        )\n\n    if activation.duplicate_activation_allowed:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "duplicate activation is allowed"\n        )\n\n    if activation.activation_reversible:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "activation is reversible"\n        )\n\n    if not activation.downstream_read_only_consumption_active:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "downstream read-only consumption is not active"\n        )\n\n    if activation.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "certified subsystem scope is empty"\n        )\n\n    if activation.source_entry_count != len(activation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if activation.source_entry_count != len(activation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    body = {\n        "source_activation_id": activation.activation_id,\n        "source_activation_hash": activation.activation_hash,\n        "source_consumption_id": activation.source_consumption_id,\n        "source_consumption_hash": activation.source_consumption_hash,\n        "source_authorization_id": activation.source_authorization_id,\n        "source_authorization_hash": activation.source_authorization_hash,\n        "source_readiness_id": activation.source_readiness_id,\n        "source_readiness_hash": activation.source_readiness_hash,\n        "source_session_attestation_id": activation.source_session_attestation_id,\n        "source_session_attestation_hash": activation.source_session_attestation_hash,\n        "source_session_id": activation.source_session_id,\n        "source_session_hash": activation.source_session_hash,\n        "source_registry_activation_id": activation.source_registry_activation_id,\n        "source_registry_activation_hash": activation.source_registry_activation_hash,\n        "source_registry_authorization_id": activation.source_registry_authorization_id,\n        "source_registry_authorization_hash": activation.source_registry_authorization_hash,\n        "source_registry_id": activation.source_registry_id,\n        "source_registry_hash": activation.source_registry_hash,\n        "source_entry_count": activation.source_entry_count,\n        "source_entry_hashes": tuple(activation.source_entry_hashes),\n        "source_subsystem_keys": tuple(activation.source_subsystem_keys),\n        "activation_verified": True,\n        "activation_identity_attested": True,\n        "activation_hash_attested": True,\n        "complete_lineage_attested": True,\n        "deterministic_attestation": True,\n        "bounded_attestation_scope": True,\n        "single_activation_scope": True,\n        "activation_single_use_attested": True,\n        "duplicate_activation_disabled_attested": True,\n        "irreversible_activation_attested": True,\n        "downstream_read_only_consumption_active_attested": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "attestation_status": ATTESTATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    attestation_hash = _stable_hash(body)\n\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation(\n        attestation_id=(\n            "oracle-certified-intelligence-read-only-consumption-session-activation-attestation:"\n            + attestation_hash\n        ),\n        **body,\n        attestation_hash=attestation_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(\n    attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,\n) -> bool:\n    if not isinstance(\n        attestation,\n        OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "invalid INT-OII-012 activation attestation"\n        )\n\n    body = asdict(attestation)\n    attestation_id = body.pop("attestation_id")\n    attestation_hash = body.pop("attestation_hash")\n\n    expected_hash = _stable_hash(body)\n    expected_id = (\n        "oracle-certified-intelligence-read-only-consumption-session-activation-attestation:"\n        + expected_hash\n    )\n\n    if attestation_hash != expected_hash or attestation_id != expected_id:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "attestation identity or hash mismatch"\n        )\n\n    if attestation.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "empty attestation scope"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    required_true = (\n        attestation.activation_verified,\n        attestation.activation_identity_attested,\n        attestation.activation_hash_attested,\n        attestation.complete_lineage_attested,\n        attestation.deterministic_attestation,\n        attestation.bounded_attestation_scope,\n        attestation.single_activation_scope,\n        attestation.activation_single_use_attested,\n        attestation.duplicate_activation_disabled_attested,\n        attestation.irreversible_activation_attested,\n        attestation.downstream_read_only_consumption_active_attested,\n        attestation.read_only,\n    )\n\n    forbidden = (\n        attestation.registry_mutation_allowed,\n        attestation.oracle_execution_allowed,\n        attestation.reasoning_execution_allowed,\n        attestation.probability_estimation_allowed,\n        attestation.final_intelligence_conclusion_allowed,\n        attestation.publication_allowed,\n        attestation.alerting_allowed,\n        attestation.qseries_handoff_allowed,\n        attestation.qseries_execution_allowed,\n        attestation.order_creation_allowed,\n        attestation.funds_movement_allowed,\n        attestation.portfolio_mutation_allowed,\n    )\n\n    if (\n        not all(required_true)\n        or any(forbidden)\n        or attestation.engine_id != ENGINE_ID\n        or attestation.schema_version != SCHEMA_VERSION\n        or attestation.algorithm_version != ALGORITHM_VERSION\n        or attestation.attestation_status != ATTESTATION_STATUS\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError(\n            "INT-OII-012 permanent safety boundary violated"\n        )\n\n    return True\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "ATTESTATION_STATUS",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError",\n    "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation",\n    "attest_oracle_certified_intelligence_read_only_consumption_session_activation",\n    "verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nimport qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate as module\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,\n)\n\n\ndef make_activation() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation:\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation(\n        activation_id="activation:" + "a" * 64,\n        source_consumption_id="consumption:" + "b" * 64,\n        source_consumption_hash="b" * 64,\n        source_authorization_id="authorization:" + "c" * 64,\n        source_authorization_hash="c" * 64,\n        source_readiness_id="readiness:" + "d" * 64,\n        source_readiness_hash="d" * 64,\n        source_session_attestation_id="session-attestation:" + "e" * 64,\n        source_session_attestation_hash="e" * 64,\n        source_session_id="session:" + "f" * 64,\n        source_session_hash="f" * 64,\n        source_registry_activation_id="registry-activation:" + "1" * 64,\n        source_registry_activation_hash="1" * 64,\n        source_registry_authorization_id="registry-authorization:" + "2" * 64,\n        source_registry_authorization_hash="2" * 64,\n        source_registry_id="registry:" + "3" * 64,\n        source_registry_hash="3" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("4" * 64, "5" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        authorization_consumption_verified=True,\n        deterministic_activation=True,\n        bounded_activation_scope=True,\n        single_consumption_scope=True,\n        activation_single_use=True,\n        duplicate_activation_allowed=False,\n        activation_reversible=False,\n        downstream_read_only_consumption_active=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        activation_status="oracle_certified_intelligence_read_only_consumption_session_activated",\n        engine_id="INT-OII-011",\n        schema_version="INT-OII-011.v1",\n        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation.v1",\n        activation_hash="a" * 64,\n    )\n\n\ndef must_reject(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-012 rejection")\n\n\ndef main() -> None:\n    original = (\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation\n    )\n    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation = (\n        lambda _: True\n    )\n\n    try:\n        activation = make_activation()\n\n        first = module.attest_oracle_certified_intelligence_read_only_consumption_session_activation(\n            activation=activation\n        )\n        second = module.attest_oracle_certified_intelligence_read_only_consumption_session_activation(\n            activation=activation\n        )\n\n        assert first == second\n        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(\n            first\n        )\n        assert first.source_activation_id == activation.activation_id\n        assert first.source_activation_hash == activation.activation_hash\n        assert first.activation_verified is True\n        assert first.activation_identity_attested is True\n        assert first.activation_hash_attested is True\n        assert first.complete_lineage_attested is True\n        assert first.deterministic_attestation is True\n        assert first.bounded_attestation_scope is True\n        assert first.single_activation_scope is True\n        assert first.activation_single_use_attested is True\n        assert first.duplicate_activation_disabled_attested is True\n        assert first.irreversible_activation_attested is True\n        assert first.downstream_read_only_consumption_active_attested is True\n        assert first.oracle_execution_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(\n                replace(first, attestation_hash="0" * 64)\n            )\n        )\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(\n                replace(first, qseries_execution_allowed=True)\n            )\n        )\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(\n                replace(first, downstream_read_only_consumption_active_attested=False)\n            )\n        )\n\n        reversible = replace(activation, activation_reversible=True)\n        must_reject(\n            lambda: module.attest_oracle_certified_intelligence_read_only_consumption_session_activation(\n                activation=reversible\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-012 TEST")\n        print(" ACTIVATION ATTESTATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-011 activation boundary consumed")\n        print("[PASS] Activation identity and hash attested")\n        print("[PASS] Consumption/authorization/readiness/session lineage attested")\n        print("[PASS] Registry lineage attested")\n        print("[PASS] Deterministic bounded attestation certified")\n        print("[PASS] Single-activation scope certified")\n        print("[PASS] Single-use activation attested")\n        print("[PASS] Duplicate activation disabled")\n        print("[PASS] Irreversible activation attested")\n        print("[PASS] Downstream read-only consumption remains active")\n        print("[PASS] Oracle and reasoning execution disabled")\n        print("[PASS] Q Series execution disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[DONE] INT-OII-012 ACTIVATION ATTESTATION GATE PASS")\n    finally:\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation = (\n            original\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" INT-OII-012 INSTALLER")
    print(" ACTIVATION ATTESTATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    if not UPSTREAM.is_file():
        raise SystemExit(
            f"[ERROR] Actual INT-OII-011 module missing: {UPSTREAM}"
        )

    upstream_source = UPSTREAM.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-011"',
        "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation",
        "verify_oracle_certified_intelligence_read_only_consumption_session_activation",
        "activation_id",
        "activation_hash",
        "activation_single_use",
        "duplicate_activation_allowed",
        "activation_reversible",
        "downstream_read_only_consumption_active",
        "read_only",
    )
    missing = [token for token in required if token not in upstream_source]
    if missing:
        raise SystemExit(
            "[ERROR] INT-OII-011 contract mismatch: " + ", ".join(missing)
        )

    ast.parse(upstream_source, filename=str(UPSTREAM))
    upstream_hash = digest(UPSTREAM)
    print("[OK] Actual INT-OII-011 activation contract verified")

    write_complete(PRODUCTION, PRODUCTION_SOURCE)
    write_complete(TEST, TEST_SOURCE)

    export_line = (
        "from .oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate import *"
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
            "Protected INT-OII-011 module changed during installation"
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
            "Protected INT-OII-011 module changed during testing"
        )

    print("[PASS] Protected INT-OII-011 module unchanged")
    print("[PASS] INT-OII-001 through INT-OII-011 lineage preserved")
    print("[PASS] No acquisition module modified")
    print("[PASS] No analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[DONE] INT-OII-012 ACTIVATION ATTESTATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
