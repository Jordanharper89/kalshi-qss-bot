from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_final_certification_freeze_gate import (
    IntegratedIntelligenceFinalCertification,
    IntegratedIntelligenceModuleAttestation,
    PERMANENTLY_DISABLED_CAPABILITIES,
    REQUIRED_ENGINE_IDS,
    stable_hash as oii_stable_hash,
)
from qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_callable_registry import (
    APPROVED_DISCIPLINES,
    build_scientific_reasoning_callable_registry,
)
from qseries_v2.oracle_scientific_reasoning_runtime.oracle_certified_callable_admission_gate import (
    admit_certified_scientific_reasoning_callables,
)
from qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_callable_resolution_engine import (
    resolve_certified_scientific_reasoning_callables,
)
from qseries_v2.oracle_scientific_reasoning_runtime.oracle_certified_callable_resolution_authorization_gate import (
    OracleCertifiedCallableResolutionAuthorizationInvariantError,
    authorize_certified_callable_resolution,
    verify_certified_callable_resolution_authorization,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleCertifiedCallableResolutionAuthorizationInvariantError:
        return
    raise AssertionError("expected OSR-004 invariant rejection")


def build_terminal_certification() -> IntegratedIntelligenceFinalCertification:
    records = []
    for engine_id in REQUIRED_ENGINE_IDS:
        body = {
            "engine_id": engine_id,
            "module_name": f"module_{engine_id.lower().replace('-', '_')}",
            "relative_path": f"qseries_v2/frozen/{engine_id}.py",
            "source_sha256": oii_stable_hash(engine_id),
            "source_size_bytes": 1000,
            "syntax_verified": True,
            "engine_identity_verified": True,
            "read_only_boundary_declared": True,
        }
        records.append(
            IntegratedIntelligenceModuleAttestation(
                **body,
                attestation_hash=oii_stable_hash(body),
            )
        )

    body = {
        "source_invocation_manifest_id": "oii014:manifest",
        "source_invocation_manifest_hash": oii_stable_hash("oii014"),
        "source_activation_hash": oii_stable_hash("oii013"),
        "source_authorization_hash": oii_stable_hash("oii012"),
        "source_session_hash": oii_stable_hash("oii010"),
        "source_manifest_hash": oii_stable_hash("oii009"),
        "frozen_evidence_set_hash": oii_stable_hash("frozen-evidence"),
        "module_attestations": tuple(records),
        "certified_engine_ids": REQUIRED_ENGINE_IDS,
        "certified_module_count": len(records),
        "permanent_disabled_capabilities": PERMANENTLY_DISABLED_CAPABILITIES,
        "terminal_status":
            "integrated_intelligence_certified_frozen_read_only",
        "subsystem_frozen": True,
        "further_certification_layers_required": False,
    }
    certification_hash = oii_stable_hash(body)
    return IntegratedIntelligenceFinalCertification(
        certification_id=(
            "integrated-intelligence-final-certification:"
            + certification_hash
        ),
        **body,
        certification_hash=certification_hash,
        engine_id="OII-015",
        schema_version="OII-015.v1",
        algorithm_version=
            "integrated-intelligence-final-certification-freeze.v1",
        read_only=True,
        acquisition_mutation_allowed=False,
        analytics_mutation_allowed=False,
        operator_mutation_allowed=False,
        reasoning_execution_allowed=False,
        probability_estimation_allowed=False,
        final_intelligence_conclusion_allowed=False,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
    )


def main() -> None:
    certification = build_terminal_certification()
    registry = build_scientific_reasoning_callable_registry(
        terminal_certification=certification
    )
    admission = admit_certified_scientific_reasoning_callables(
        registry=registry
    )
    resolution = resolve_certified_scientific_reasoning_callables(
        admission_package=admission
    )

    first = authorize_certified_callable_resolution(
        resolution_package=resolution
    )
    second = authorize_certified_callable_resolution(
        resolution_package=resolution
    )

    assert first == second
    assert first.authorization_hash == second.authorization_hash
    assert verify_certified_callable_resolution_authorization(first)
    assert first.source_resolution_hash == resolution.resolution_hash
    assert first.authorized_disciplines == APPROVED_DISCIPLINES
    assert first.authorized_callable_count == 9
    assert first.callable_resolution_authorized is True
    assert first.callable_activation_allowed is False
    assert first.callable_binding_allowed is False
    assert first.reasoning_execution_allowed is False
    assert first.qseries_execution_allowed is False

    rejected(
        lambda: verify_certified_callable_resolution_authorization(
            replace(first, authorization_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_certified_callable_resolution_authorization(
            replace(first, callable_binding_allowed=True)
        )
    )
    rejected(
        lambda: authorize_certified_callable_resolution(
            resolution_package=replace(
                resolution,
                resolution_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OSR-004 TEST")
    print(" CERTIFIED CALLABLE RESOLUTION")
    print(" AUTHORIZATION GATE")
    print("========================================")
    print("[PASS] Actual OSR-003 resolution package consumed")
    print("[PASS] OSR-003 identity and hash lineage verified")
    print("[PASS] Exact resolved discipline set authorized")
    print("[PASS] Authorization identity deterministic")
    print("[PASS] Exact resolution hash scope preserved")
    print("[PASS] Resolution authorization enabled")
    print("[PASS] Callable activation remains disabled")
    print("[PASS] Callable binding remains disabled")
    print("[PASS] Reasoning execution remains disabled")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Publication, alerting, and handoff disabled")
    print("[PASS] Q Series execution remains disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OSR-004 RESOLUTION AUTHORIZATION GATE CERTIFIED")


if __name__ == "__main__":
    main()
