from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
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
    OracleControlledReasoningInvocationInvariantError,
    build_controlled_scientific_reasoning_invocation_manifest,
    serialize_controlled_scientific_reasoning_invocation_manifest,
    verify_controlled_scientific_reasoning_invocation_manifest,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleControlledReasoningInvocationInvariantError:
        return
    raise AssertionError("expected OII-014 invariant rejection")


def build_oii013(reverse: bool = False):
    now = datetime(2026, 7, 28, 16, 0, tzinfo=timezone.utc)
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
        subject_id="kalshi:market:invocation-manifest-test",
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
    return consume_and_activate_scientific_reasoning_authorization(
        authorization_package=oii012
    )


def main() -> None:
    oii013_a = build_oii013(False)
    oii013_b = build_oii013(True)

    first = build_controlled_scientific_reasoning_invocation_manifest(
        activation_package=oii013_a
    )
    second = build_controlled_scientific_reasoning_invocation_manifest(
        activation_package=oii013_b
    )

    assert first == second
    assert first.invocation_manifest_hash == second.invocation_manifest_hash
    assert verify_controlled_scientific_reasoning_invocation_manifest(first)

    assert first.authorization_consumed is True
    assert first.activation_verified is True
    assert first.invocation_manifest_materialized is True
    assert first.invocation_step_count == len(first.invocation_steps)
    assert first.invocation_step_count > 0
    assert first.invocation_scope == "exact_oii013_activation_hash_only"
    assert (
        first.invocation_status
        == "controlled_manifest_materialized_not_resolved_not_bound_not_executed"
    )
    assert tuple(step.discipline_name for step in first.invocation_steps) == (
        first.deterministic_execution_order
    )
    assert all(
        step.invocation_status
        == "manifested_not_resolved_not_bound_not_executed"
        for step in first.invocation_steps
    )
    assert all(
        step.callable_resolution_allowed is False
        and step.callable_binding_allowed is False
        and step.invocation_execution_allowed is False
        and step.probability_estimation_allowed is False
        and step.conclusion_generation_allowed is False
        for step in first.invocation_steps
    )

    payload = json.loads(
        serialize_controlled_scientific_reasoning_invocation_manifest(first)
    )
    assert payload["engine_id"] == "OII-014"
    assert payload["invocation_manifest_materialized"] is True
    assert payload["callable_resolution_allowed"] is False
    assert payload["callable_binding_allowed"] is False
    assert payload["reasoning_execution_allowed"] is False
    assert payload["probability_estimation_allowed"] is False
    assert payload["final_intelligence_conclusion_allowed"] is False
    assert payload["qseries_execution_allowed"] is False

    rejected(
        lambda: verify_controlled_scientific_reasoning_invocation_manifest(
            replace(first, invocation_manifest_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_controlled_scientific_reasoning_invocation_manifest(
            replace(first, callable_resolution_allowed=True)
        )
    )
    rejected(
        lambda: build_controlled_scientific_reasoning_invocation_manifest(
            activation_package=replace(
                oii013_a,
                activation_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OII-014 TEST")
    print(" CONTROLLED REASONING INVOCATION MANIFEST")
    print("========================================")
    print("[PASS] Actual OII-013 activation package consumed")
    print("[PASS] OII-013 identity and hashes verified")
    print("[PASS] Exact activation scope preserved")
    print("[PASS] Frozen evidence and session lineage preserved")
    print("[PASS] Deterministic discipline order preserved")
    print("[PASS] Controlled invocation steps materialized")
    print("[PASS] Invocation manifest identity deterministic")
    print("[PASS] Input ordering cannot alter manifest identity")
    print("[PASS] Callable resolution remains disabled")
    print("[PASS] Callable binding remains disabled")
    print("[PASS] Reasoning execution remains disabled")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Publication, alerting, handoff, and execution disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-014 CONTROLLED INVOCATION MANIFEST CERTIFIED")


if __name__ == "__main__":
    main()
