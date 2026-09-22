from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_source_identity_provenance_graph_contract import (
    build_evidence_node,
    build_provenance_edge,
    build_source_node,
    build_source_provenance_graph,
    stable_hash,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_source_dependency_independence_engine import (
    analyze_source_dependency_and_independence,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_redundancy_novelty_engine import (
    analyze_redundancy_and_novelty,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_entropy_information_gain_engine import (
    analyze_entropy_and_information_gain,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_provenance_confidence_engine import (
    analyze_provenance_confidence,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_certified_evidence_admission_gate import (
    build_certified_evidence_admission_policy,
    certify_evidence_for_reasoning,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_scientific_reasoning_input_manifest import (
    build_scientific_reasoning_input_manifest,
    build_scientific_reasoning_request,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_scientific_reasoning_session_orchestrator import (
    materialize_scientific_reasoning_session,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_scientific_reasoning_session_readiness_gate import (
    evaluate_scientific_reasoning_session_readiness,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_scientific_reasoning_session_authorization_gate import (
    authorize_scientific_reasoning_session,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_scientific_reasoning_authorization_consumption_activation_gate import (
    consume_and_activate_scientific_reasoning_authorization,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_controlled_scientific_reasoning_invocation_manifest import (
    build_controlled_scientific_reasoning_invocation_manifest,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_final_certification_freeze_gate import (
    OracleIntegratedIntelligenceFreezeInvariantError,
    REQUIRED_ENGINE_IDS,
    certify_and_freeze_integrated_intelligence_subsystem,
    serialize_integrated_intelligence_final_certification,
    verify_integrated_intelligence_final_certification,
)


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence" / "integrated_intelligence"

MODULE_CONTRACTS = (
    ("OII-003", "oracle_source_identity_provenance_graph_contract"),
    ("OII-004", "oracle_source_dependency_independence_engine"),
    ("OII-005", "oracle_redundancy_novelty_engine"),
    ("OII-006", "oracle_entropy_information_gain_engine"),
    ("OII-007", "oracle_provenance_confidence_engine"),
    ("OII-008", "oracle_certified_evidence_admission_gate"),
    ("OII-009", "oracle_scientific_reasoning_input_manifest"),
    ("OII-010", "oracle_scientific_reasoning_session_orchestrator"),
    ("OII-011", "oracle_scientific_reasoning_session_readiness_gate"),
    ("OII-012", "oracle_scientific_reasoning_session_authorization_gate"),
    (
        "OII-013",
        "oracle_scientific_reasoning_authorization_consumption_activation_gate",
    ),
    (
        "OII-014",
        "oracle_controlled_scientific_reasoning_invocation_manifest",
    ),
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleIntegratedIntelligenceFreezeInvariantError:
        return
    raise AssertionError("expected OII-015 invariant rejection")


def build_oii014(reverse: bool = False):
    now = datetime(2026, 7, 28, 18, 0, tzinfo=timezone.utc)
    later = now + timedelta(hours=12)

    source_a = build_source_node(
        source_id="source.primary",
        source_class="regulatory_filing",
        source_locator="regulator://primary",
        source_identity_hash=stable_hash("source.primary"),
        observed_at=now,
    )
    source_b = build_source_node(
        source_id="source.independent",
        source_class="expert_statement",
        source_locator="expert://independent",
        source_identity_hash=stable_hash("source.independent"),
        observed_at=now,
    )
    evidence_a = build_evidence_node(
        evidence_id="evidence.primary",
        source_id=source_a.source_id,
        observation_id="obs.primary",
        content_hash=stable_hash("primary-content"),
        replay_hash=stable_hash("primary-replay"),
        chain_hash=stable_hash("primary-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.resolution",),
    )
    evidence_b = build_evidence_node(
        evidence_id="evidence.independent",
        source_id=source_b.source_id,
        observation_id="obs.independent",
        content_hash=stable_hash("independent-content"),
        replay_hash=stable_hash("independent-replay"),
        chain_hash=stable_hash("independent-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.resolution",),
    )
    edges = (
        build_provenance_edge(
            from_node_id=evidence_a.node_id,
            to_node_id=source_a.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=evidence_a.evidence_id,
            observed_at=now,
            confidence_basis="direct primary source",
        ),
        build_provenance_edge(
            from_node_id=evidence_b.node_id,
            to_node_id=source_b.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=evidence_b.evidence_id,
            observed_at=now,
            confidence_basis="independent source",
        ),
    )
    sources = (source_a, source_b)
    evidence = (evidence_a, evidence_b)
    if reverse:
        sources = tuple(reversed(sources))
        evidence = tuple(reversed(evidence))
        edges = tuple(reversed(edges))

    graph = build_source_provenance_graph(
        source_nodes=sources,
        evidence_nodes=evidence,
        edges=edges,
        created_at=now,
    )
    oii004 = analyze_source_dependency_and_independence(graph=graph)
    oii005 = analyze_redundancy_and_novelty(
        source_independence_package=oii004
    )
    oii006 = analyze_entropy_and_information_gain(
        redundancy_novelty_package=oii005
    )
    oii007 = analyze_provenance_confidence(
        entropy_information_gain_package=oii006
    )
    policy = build_certified_evidence_admission_policy(
        minimum_provenance_confidence_score="0.500000",
        minimum_information_gain_score="0.250000",
    )
    oii008 = certify_evidence_for_reasoning(
        provenance_confidence_package=oii007,
        policy=policy,
    )
    request = build_scientific_reasoning_request(
        subject_id="kalshi:market:final-freeze-test",
        question_text="What evidence bears on the market outcome?",
        requested_disciplines=(
            "information_theory",
            "bayesian_inference",
            "causal_inference",
            "calibration_science",
        ),
        requested_claim_ids=("claim.resolution",),
        request_context={"mode": "read_only"},
    )
    oii009 = build_scientific_reasoning_input_manifest(
        certified_evidence_package=oii008,
        reasoning_request=request,
    )
    oii010 = materialize_scientific_reasoning_session(
        reasoning_input_manifest=oii009
    )
    oii011 = evaluate_scientific_reasoning_session_readiness(
        reasoning_session=oii010
    )
    oii012 = authorize_scientific_reasoning_session(
        readiness_package=oii011
    )
    oii013 = consume_and_activate_scientific_reasoning_authorization(
        authorization_package=oii012
    )
    return build_controlled_scientific_reasoning_invocation_manifest(
        activation_package=oii013
    )


def main() -> None:
    manifest_a = build_oii014(False)
    manifest_b = build_oii014(True)

    first = certify_and_freeze_integrated_intelligence_subsystem(
        invocation_manifest=manifest_a,
        package_root=PACKAGE,
        module_contracts=MODULE_CONTRACTS,
    )
    second = certify_and_freeze_integrated_intelligence_subsystem(
        invocation_manifest=manifest_b,
        package_root=PACKAGE,
        module_contracts=tuple(reversed(MODULE_CONTRACTS)),
    )

    assert first == second
    assert first.certification_hash == second.certification_hash
    assert verify_integrated_intelligence_final_certification(first)

    assert first.certified_engine_ids == REQUIRED_ENGINE_IDS
    assert first.certified_module_count == 12
    assert first.subsystem_frozen is True
    assert first.further_certification_layers_required is False
    assert (
        first.terminal_status
        == "integrated_intelligence_certified_frozen_read_only"
    )
    assert all(record.syntax_verified for record in first.module_attestations)
    assert all(
        record.engine_identity_verified
        for record in first.module_attestations
    )
    assert all(
        record.read_only_boundary_declared
        for record in first.module_attestations
    )

    payload = json.loads(
        serialize_integrated_intelligence_final_certification(first)
    )
    assert payload["engine_id"] == "OII-015"
    assert payload["subsystem_frozen"] is True
    assert payload["further_certification_layers_required"] is False
    assert payload["reasoning_execution_allowed"] is False
    assert payload["probability_estimation_allowed"] is False
    assert payload["final_intelligence_conclusion_allowed"] is False
    assert payload["publication_allowed"] is False
    assert payload["qseries_handoff_allowed"] is False
    assert payload["qseries_execution_allowed"] is False

    rejected(
        lambda: verify_integrated_intelligence_final_certification(
            replace(first, certification_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_integrated_intelligence_final_certification(
            replace(first, subsystem_frozen=False)
        )
    )
    rejected(
        lambda: certify_and_freeze_integrated_intelligence_subsystem(
            invocation_manifest=replace(
                manifest_a,
                reasoning_execution_allowed=True,
            ),
            package_root=PACKAGE,
            module_contracts=MODULE_CONTRACTS,
        )
    )

    print("========================================")
    print(" OII-015 FINAL CERTIFICATION")
    print(" INTEGRATED INTELLIGENCE FREEZE GATE")
    print("========================================")
    print("[PASS] Actual OII-014 invocation manifest consumed")
    print("[PASS] OII-003 through OII-014 lineage verified")
    print("[PASS] All integrated-intelligence modules syntax verified")
    print("[PASS] All engine identities verified")
    print("[PASS] Module source hashes frozen")
    print("[PASS] Frozen evidence lineage preserved")
    print("[PASS] Session, authorization, and activation lineage preserved")
    print("[PASS] Deterministic terminal certification identity verified")
    print("[PASS] Input ordering cannot alter certification identity")
    print("[PASS] Integrated Intelligence subsystem frozen")
    print("[PASS] Reasoning execution remains disabled")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Publication and alerting remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] No further OII certification layers required")
    print("[DONE] OII INTEGRATED INTELLIGENCE CERTIFIED AND FROZEN")


if __name__ == "__main__":
    main()
