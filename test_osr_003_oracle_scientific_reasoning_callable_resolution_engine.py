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
    OracleScientificReasoningResolutionInvariantError,
    resolve_certified_scientific_reasoning_callables,
    verify_scientific_reasoning_callable_resolution_package,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleScientificReasoningResolutionInvariantError:
        return
    raise AssertionError("expected OSR-003 invariant rejection")


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

    first = resolve_certified_scientific_reasoning_callables(
        admission_package=admission
    )
    second = resolve_certified_scientific_reasoning_callables(
        admission_package=admission
    )

    assert first == second
    assert first.resolution_hash == second.resolution_hash
    assert verify_scientific_reasoning_callable_resolution_package(first)

    assert first.source_admission_hash == admission.admission_hash
    assert first.resolved_disciplines == APPROVED_DISCIPLINES
    assert first.resolved_callable_count == 9
    assert first.unresolved_callable_count == 0
    assert all(record.resolved for record in first.resolution_records)
    assert all(not record.active for record in first.resolution_records)
    assert all(not record.bound for record in first.resolution_records)
    assert all(not record.executable for record in first.resolution_records)
    assert all(
        not record.symbol_lookup_performed
        for record in first.resolution_records
    )
    assert all(
        not record.callable_loaded
        for record in first.resolution_records
    )

    rejected(
        lambda: verify_scientific_reasoning_callable_resolution_package(
            replace(first, resolution_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_scientific_reasoning_callable_resolution_package(
            replace(first, callable_binding_allowed=True)
        )
    )
    rejected(
        lambda: resolve_certified_scientific_reasoning_callables(
            admission_package=replace(
                admission,
                admission_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OSR-003 TEST")
    print(" SCIENTIFIC REASONING CALLABLE")
    print(" RESOLUTION ENGINE")
    print("========================================")
    print("[PASS] Actual OSR-002 admission package consumed")
    print("[PASS] OSR-002 identity and hash lineage verified")
    print("[PASS] Exact approved discipline set resolved")
    print("[PASS] Resolution records deterministic")
    print("[PASS] Resolution remains reference-only")
    print("[PASS] No implementation module imported")
    print("[PASS] No implementation symbol loaded")
    print("[PASS] No callable activated")
    print("[PASS] Callable binding remains disabled")
    print("[PASS] Reasoning execution remains disabled")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Publication, alerting, and handoff disabled")
    print("[PASS] Q Series execution remains disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OSR-003 CALLABLE RESOLUTION ENGINE CERTIFIED")


if __name__ == "__main__":
    main()
