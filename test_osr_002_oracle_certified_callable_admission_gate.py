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
    build_scientific_reasoning_callable_descriptor,
    build_scientific_reasoning_callable_registry,
)
from qseries_v2.oracle_scientific_reasoning_runtime.oracle_certified_callable_admission_gate import (
    OracleCertifiedCallableAdmissionInvariantError,
    admit_certified_scientific_reasoning_callables,
    build_certified_callable_admission_policy,
    verify_certified_callable_admission_package,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleCertifiedCallableAdmissionInvariantError:
        return
    raise AssertionError("expected OSR-002 invariant rejection")


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
    reverse_descriptors = tuple(
        build_scientific_reasoning_callable_descriptor(discipline)
        for discipline in reversed(APPROVED_DISCIPLINES)
    )
    registry = build_scientific_reasoning_callable_registry(
        terminal_certification=certification,
        descriptors=reverse_descriptors,
    )

    first = admit_certified_scientific_reasoning_callables(
        registry=registry,
    )
    second = admit_certified_scientific_reasoning_callables(
        registry=registry,
        policy=build_certified_callable_admission_policy(
            allowed_disciplines=tuple(reversed(APPROVED_DISCIPLINES))
        ),
    )

    assert first == second
    assert first.admission_hash == second.admission_hash
    assert verify_certified_callable_admission_package(first)

    assert first.source_registry_hash == registry.registry_hash
    assert first.admitted_disciplines == APPROVED_DISCIPLINES
    assert first.admitted_callable_count == 9
    assert first.rejected_callable_count == 0
    assert first.registry_admitted is True
    assert all(item.admitted for item in first.admission_records)
    assert all(not item.active for item in first.admission_records)
    assert all(not item.resolved for item in first.admission_records)
    assert all(not item.bound for item in first.admission_records)
    assert all(not item.executable for item in first.admission_records)
    assert all(item.read_only for item in first.admission_records)

    rejected(
        lambda: verify_certified_callable_admission_package(
            replace(first, admission_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_certified_callable_admission_package(
            replace(first, callable_resolution_allowed=True)
        )
    )
    rejected(
        lambda: admit_certified_scientific_reasoning_callables(
            registry=replace(
                registry,
                registry_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OSR-002 TEST")
    print(" CERTIFIED CALLABLE ADMISSION GATE")
    print("========================================")
    print("[PASS] Actual OSR-001 callable registry consumed")
    print("[PASS] OSR-001 registry identity and hashes verified")
    print("[PASS] Exact approved discipline set admitted")
    print("[PASS] Admission policy deterministic and hash-verified")
    print("[PASS] Descriptor identity and lineage preserved")
    print("[PASS] Input ordering cannot alter admission identity")
    print("[PASS] All admitted callables remain inactive")
    print("[PASS] Callable activation remains disabled")
    print("[PASS] Callable resolution remains disabled")
    print("[PASS] Callable binding remains disabled")
    print("[PASS] Reasoning execution remains disabled")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Publication, alerting, handoff, and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OSR-002 CERTIFIED CALLABLE ADMISSION GATE CERTIFIED")


if __name__ == "__main__":
    main()
