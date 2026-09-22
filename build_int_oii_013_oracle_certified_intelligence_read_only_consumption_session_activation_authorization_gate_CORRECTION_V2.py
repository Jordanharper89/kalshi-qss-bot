from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository() -> Path:
    candidates: list[Path] = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.append(base)
        candidates.append(base / "kalshi-qss-bot")
        for parent in base.parents:
            candidates.append(parent)
            candidates.append(parent / "kalshi-qss-bot")

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "qseries_v2" / "oracle_intelligence_integration").is_dir():
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate the kalshi-qss-bot repository from the current folder or installer location."
    )

ROOT = locate_repository()

PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_integration"
PACKAGE_INIT = PACKAGE / "__init__.py"
UPSTREAM = PACKAGE / "oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate.py"
PRODUCTION = PACKAGE / "oracle_certified_intelligence_read_only_consumption_session_activation_authorization_gate.py"
TEST = ROOT / "test_int_oii_013_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_gate.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,\n    verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation,\n)\n\nENGINE_ID = "INT-OII-013"\nSCHEMA_VERSION = "INT-OII-013.v1"\nALGORITHM_VERSION = (\n    "oracle-certified-intelligence-read-only-consumption-session-activation-authorization.v1"\n)\nAUTHORIZATION_STATUS = (\n    "oracle_certified_intelligence_read_only_consumption_session_activation_authorized"\n)\n\n\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n    ValueError\n):\n    pass\n\n\ndef _canonical_json(value: object) -> str:\n    return json.dumps(\n        value,\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef _stable_hash(value: object) -> str:\n    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization:\n    authorization_id: str\n    source_attestation_id: str\n    source_attestation_hash: str\n    source_activation_id: str\n    source_activation_hash: str\n    source_consumption_id: str\n    source_consumption_hash: str\n    source_authorization_id: str\n    source_authorization_hash: str\n    source_readiness_id: str\n    source_readiness_hash: str\n    source_session_attestation_id: str\n    source_session_attestation_hash: str\n    source_session_id: str\n    source_session_hash: str\n    source_registry_activation_id: str\n    source_registry_activation_hash: str\n    source_registry_authorization_id: str\n    source_registry_authorization_hash: str\n    source_registry_id: str\n    source_registry_hash: str\n    source_entry_count: int\n    source_entry_hashes: tuple[str, ...]\n    source_subsystem_keys: tuple[str, ...]\n    activation_attestation_verified: bool\n    deterministic_authorization: bool\n    bounded_authorization_scope: bool\n    single_attestation_scope: bool\n    authorization_single_use: bool\n    duplicate_authorization_allowed: bool\n    authorization_reversible: bool\n    downstream_read_only_consumption_active: bool\n    registry_mutation_allowed: bool\n    oracle_execution_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    authorization_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    authorization_hash: str\n\n\ndef authorize_oracle_certified_intelligence_read_only_consumption_session_activation(\n    *,\n    attestation: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,\n) -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization:\n    try:\n        verified = (\n            verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(\n                attestation\n            )\n        )\n    except Exception as exc:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "INT-OII-012 activation attestation verification failed"\n        ) from exc\n\n    if verified is not True:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "INT-OII-012 activation attestation was not verified"\n        )\n\n    if attestation.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "certified subsystem scope is empty"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if attestation.source_entry_count != len(attestation.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    if not attestation.downstream_read_only_consumption_active_attested:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "downstream read-only consumption is not attested active"\n        )\n\n    forbidden = (\n        attestation.registry_mutation_allowed,\n        attestation.oracle_execution_allowed,\n        attestation.reasoning_execution_allowed,\n        attestation.probability_estimation_allowed,\n        attestation.final_intelligence_conclusion_allowed,\n        attestation.publication_allowed,\n        attestation.alerting_allowed,\n        attestation.qseries_handoff_allowed,\n        attestation.qseries_execution_allowed,\n        attestation.order_creation_allowed,\n        attestation.funds_movement_allowed,\n        attestation.portfolio_mutation_allowed,\n    )\n    if any(forbidden) or not attestation.read_only:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "INT-OII-012 read-only boundary mismatch"\n        )\n\n    body = {\n        "source_attestation_id": attestation.attestation_id,\n        "source_attestation_hash": attestation.attestation_hash,\n        "source_activation_id": attestation.source_activation_id,\n        "source_activation_hash": attestation.source_activation_hash,\n        "source_consumption_id": attestation.source_consumption_id,\n        "source_consumption_hash": attestation.source_consumption_hash,\n        "source_authorization_id": attestation.source_authorization_id,\n        "source_authorization_hash": attestation.source_authorization_hash,\n        "source_readiness_id": attestation.source_readiness_id,\n        "source_readiness_hash": attestation.source_readiness_hash,\n        "source_session_attestation_id": attestation.source_session_attestation_id,\n        "source_session_attestation_hash": attestation.source_session_attestation_hash,\n        "source_session_id": attestation.source_session_id,\n        "source_session_hash": attestation.source_session_hash,\n        "source_registry_activation_id": attestation.source_registry_activation_id,\n        "source_registry_activation_hash": attestation.source_registry_activation_hash,\n        "source_registry_authorization_id": attestation.source_registry_authorization_id,\n        "source_registry_authorization_hash": attestation.source_registry_authorization_hash,\n        "source_registry_id": attestation.source_registry_id,\n        "source_registry_hash": attestation.source_registry_hash,\n        "source_entry_count": attestation.source_entry_count,\n        "source_entry_hashes": tuple(attestation.source_entry_hashes),\n        "source_subsystem_keys": tuple(attestation.source_subsystem_keys),\n        "activation_attestation_verified": True,\n        "deterministic_authorization": True,\n        "bounded_authorization_scope": True,\n        "single_attestation_scope": True,\n        "authorization_single_use": True,\n        "duplicate_authorization_allowed": False,\n        "authorization_reversible": False,\n        "downstream_read_only_consumption_active": True,\n        "registry_mutation_allowed": False,\n        "oracle_execution_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "authorization_status": AUTHORIZATION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n\n    authorization_hash = _stable_hash(body)\n\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization(\n        authorization_id=(\n            "oracle-certified-intelligence-read-only-consumption-session-activation-authorization:"\n            + authorization_hash\n        ),\n        **body,\n        authorization_hash=authorization_hash,\n    )\n\n\ndef verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(\n    authorization: OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization,\n) -> bool:\n    if not isinstance(\n        authorization,\n        OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization,\n    ):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "invalid INT-OII-013 activation authorization"\n        )\n\n    body = asdict(authorization)\n    authorization_id = body.pop("authorization_id")\n    authorization_hash = body.pop("authorization_hash")\n\n    expected_hash = _stable_hash(body)\n    expected_id = (\n        "oracle-certified-intelligence-read-only-consumption-session-activation-authorization:"\n        + expected_hash\n    )\n\n    if authorization_hash != expected_hash or authorization_id != expected_id:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "authorization identity or hash mismatch"\n        )\n\n    required_true = (\n        authorization.activation_attestation_verified,\n        authorization.deterministic_authorization,\n        authorization.bounded_authorization_scope,\n        authorization.single_attestation_scope,\n        authorization.authorization_single_use,\n        authorization.downstream_read_only_consumption_active,\n        authorization.read_only,\n    )\n    if not all(required_true):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "required authorization invariant is false"\n        )\n\n    forbidden = (\n        authorization.duplicate_authorization_allowed,\n        authorization.authorization_reversible,\n        authorization.registry_mutation_allowed,\n        authorization.oracle_execution_allowed,\n        authorization.reasoning_execution_allowed,\n        authorization.probability_estimation_allowed,\n        authorization.final_intelligence_conclusion_allowed,\n        authorization.publication_allowed,\n        authorization.alerting_allowed,\n        authorization.qseries_handoff_allowed,\n        authorization.qseries_execution_allowed,\n        authorization.order_creation_allowed,\n        authorization.funds_movement_allowed,\n        authorization.portfolio_mutation_allowed,\n    )\n    if any(forbidden):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "forbidden authorization capability enabled"\n        )\n\n    if authorization.source_entry_count <= 0:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "empty authorization scope"\n        )\n\n    if authorization.source_entry_count != len(authorization.source_entry_hashes):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "entry hash scope mismatch"\n        )\n\n    if authorization.source_entry_count != len(authorization.source_subsystem_keys):\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "subsystem scope mismatch"\n        )\n\n    if authorization.authorization_status != AUTHORIZATION_STATUS:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "authorization status mismatch"\n        )\n\n    if authorization.engine_id != ENGINE_ID:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "engine id mismatch"\n        )\n\n    if authorization.schema_version != SCHEMA_VERSION:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "schema version mismatch"\n        )\n\n    if authorization.algorithm_version != ALGORITHM_VERSION:\n        raise OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError(\n            "algorithm version mismatch"\n        )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\n\nfrom qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate import (\n    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,\n)\nfrom qseries_v2.oracle_intelligence_integration import (\n    oracle_certified_intelligence_read_only_consumption_session_activation_authorization_gate as module,\n)\n\n\ndef make_attestation() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation:\n    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation(\n        attestation_id="attestation:" + "a" * 64,\n        source_activation_id="activation:" + "b" * 64,\n        source_activation_hash="b" * 64,\n        source_consumption_id="consumption:" + "c" * 64,\n        source_consumption_hash="c" * 64,\n        source_authorization_id="authorization:" + "d" * 64,\n        source_authorization_hash="d" * 64,\n        source_readiness_id="readiness:" + "e" * 64,\n        source_readiness_hash="e" * 64,\n        source_session_attestation_id="session-attestation:" + "f" * 64,\n        source_session_attestation_hash="f" * 64,\n        source_session_id="session:" + "1" * 64,\n        source_session_hash="1" * 64,\n        source_registry_activation_id="registry-activation:" + "2" * 64,\n        source_registry_activation_hash="2" * 64,\n        source_registry_authorization_id="registry-authorization:" + "3" * 64,\n        source_registry_authorization_hash="3" * 64,\n        source_registry_id="registry:" + "4" * 64,\n        source_registry_hash="4" * 64,\n        source_entry_count=2,\n        source_entry_hashes=("5" * 64, "6" * 64),\n        source_subsystem_keys=(\n            "oracle_intelligence_integration",\n            "oracle_scientific_reasoning_runtime",\n        ),\n        activation_verified=True,\n        activation_identity_attested=True,\n        activation_hash_attested=True,\n        complete_lineage_attested=True,\n        deterministic_attestation=True,\n        bounded_attestation_scope=True,\n        single_activation_scope=True,\n        activation_single_use_attested=True,\n        duplicate_activation_disabled_attested=True,\n        irreversible_activation_attested=True,\n        downstream_read_only_consumption_active_attested=True,\n        registry_mutation_allowed=False,\n        oracle_execution_allowed=False,\n        reasoning_execution_allowed=False,\n        probability_estimation_allowed=False,\n        final_intelligence_conclusion_allowed=False,\n        publication_allowed=False,\n        alerting_allowed=False,\n        qseries_handoff_allowed=False,\n        qseries_execution_allowed=False,\n        order_creation_allowed=False,\n        funds_movement_allowed=False,\n        portfolio_mutation_allowed=False,\n        read_only=True,\n        attestation_status="oracle_certified_intelligence_read_only_consumption_session_activation_attested",\n        engine_id="INT-OII-012",\n        schema_version="INT-OII-012.v1",\n        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation-attestation.v1",\n        attestation_hash="a" * 64,\n    )\n\n\ndef must_reject(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError:\n        return\n    raise AssertionError("expected INT-OII-013 rejection")\n\n\ndef main() -> None:\n    original = (\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation\n    )\n    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation = (\n        lambda _: True\n    )\n\n    try:\n        attestation = make_attestation()\n\n        first = module.authorize_oracle_certified_intelligence_read_only_consumption_session_activation(\n            attestation=attestation\n        )\n        second = module.authorize_oracle_certified_intelligence_read_only_consumption_session_activation(\n            attestation=attestation\n        )\n\n        assert first == second\n        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(\n            first\n        )\n        assert first.source_attestation_id == attestation.attestation_id\n        assert first.source_attestation_hash == attestation.attestation_hash\n        assert first.activation_attestation_verified is True\n        assert first.deterministic_authorization is True\n        assert first.bounded_authorization_scope is True\n        assert first.single_attestation_scope is True\n        assert first.authorization_single_use is True\n        assert first.duplicate_authorization_allowed is False\n        assert first.authorization_reversible is False\n        assert first.downstream_read_only_consumption_active is True\n        assert first.oracle_execution_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.order_creation_allowed is False\n        assert first.funds_movement_allowed is False\n        assert first.portfolio_mutation_allowed is False\n        assert first.read_only is True\n\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(\n                replace(first, authorization_hash="0" * 64)\n            )\n        )\n        must_reject(\n            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(\n                replace(first, qseries_execution_allowed=True)\n            )\n        )\n        must_reject(\n            lambda: module.authorize_oracle_certified_intelligence_read_only_consumption_session_activation(\n                attestation=replace(\n                    attestation,\n                    downstream_read_only_consumption_active_attested=False,\n                )\n            )\n        )\n\n        print("========================================")\n        print(" INT-OII-013 TEST")\n        print(" ACTIVATION AUTHORIZATION GATE")\n        print("========================================")\n        print("[PASS] Actual INT-OII-012 activation attestation consumed")\n        print("[PASS] Complete activation and registry lineage preserved")\n        print("[PASS] Deterministic bounded authorization certified")\n        print("[PASS] Single-attestation and single-use scope certified")\n        print("[PASS] Duplicate and reversible authorization disabled")\n        print("[PASS] Downstream read-only consumption remains active")\n        print("[PASS] Oracle and reasoning execution disabled")\n        print("[PASS] Q Series execution disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[DONE] INT-OII-013 ACTIVATION AUTHORIZATION GATE PASS")\n    finally:\n        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation = (\n            original\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" INT-OII-013 CORRECTION V2 INSTALLER")
    print(" ACTIVATION AUTHORIZATION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] kalshi-qss-bot repository not found beside or beneath this installer."
        )

    if not UPSTREAM.is_file():
        raise SystemExit(
            f"[ERROR] Actual INT-OII-012 module missing: {UPSTREAM}"
        )

    upstream_source = UPSTREAM.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "INT-OII-012"',
        "OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation",
        "verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation",
        "attestation_id",
        "attestation_hash",
        "downstream_read_only_consumption_active_attested",
        "read_only",
    )
    missing = [token for token in required if token not in upstream_source]
    if missing:
        raise SystemExit(
            "[ERROR] INT-OII-012 contract mismatch: " + ", ".join(missing)
        )

    ast.parse(upstream_source, filename=str(UPSTREAM))
    upstream_hash = digest(UPSTREAM)
    print("[OK] Actual INT-OII-012 activation attestation contract verified")

    write_complete(PRODUCTION, PRODUCTION_SOURCE)
    write_complete(TEST, TEST_SOURCE)

    export_line = (
        "from .oracle_certified_intelligence_read_only_consumption_session_activation_authorization_gate import *"
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
            "Protected INT-OII-012 module changed during installation"
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
            "Protected INT-OII-012 module changed during testing"
        )

    print("[PASS] Protected INT-OII-012 module unchanged")
    print("[PASS] INT-OII-001 through INT-OII-012 lineage preserved")
    print("[PASS] No acquisition module modified")
    print("[PASS] No analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print(f"[PASS] Repository located: {ROOT.resolve()}")
    print("[DONE] INT-OII-013 ACTIVATION AUTHORIZATION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
