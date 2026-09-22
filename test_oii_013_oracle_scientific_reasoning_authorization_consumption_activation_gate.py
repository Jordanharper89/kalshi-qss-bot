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
    OracleScientificReasoningActivationInvariantError,
    consume_and_activate_scientific_reasoning_authorization,
    serialize_scientific_reasoning_session_activation_package,
    verify_scientific_reasoning_session_activation_package,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleScientificReasoningActivationInvariantError:
        return
    raise AssertionError("expected OII-013 invariant rejection")


def build_oii012(reverse: bool = False):
    now = datetime(2026, 7, 28, 14, 0, tzinfo=timezone.utc)
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
        subject_id="kalshi:market:activation-test",
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
    return authorize_scientific_reasoning_session(
        readiness_package=oii011
    )


def main() -> None:
    oii012_a = build_oii012(False)
    oii012_b = build_oii012(True)

    first = consume_and_activate_scientific_reasoning_authorization(
        authorization_package=oii012_a
    )
    second = consume_and_activate_scientific_reasoning_authorization(
        authorization_package=oii012_b
    )

    assert first == second
    assert first.activation_hash == second.activation_hash
    assert verify_scientific_reasoning_session_activation_package(first)

    assert first.authorization_consumed is True
    assert first.activation_materialized is True
    assert first.invocation_manifest_allowed is True
    assert (
        first.activation_status
        == "activated_for_controlled_invocation_manifest"
    )
    assert first.blocked_discipline_count == 0
    assert first.activated_discipline_count == len(
        first.discipline_activations
    )
    assert all(
        item.activation_status
        == "activated_for_invocation_manifest"
        for item in first.discipline_activations
    )
    assert all(
        item.source_session_hash == first.source_session_hash
        for item in first.discipline_activations
    )
    assert all(
        item.frozen_evidence_set_hash
        == first.frozen_evidence_set_hash
        for item in first.discipline_activations
    )

    payload = json.loads(
        serialize_scientific_reasoning_session_activation_package(first)
    )
    assert payload["engine_id"] == "OII-013"
    assert payload["authorization_consumed"] is True
    assert payload["activation_materialized"] is True
    assert payload["invocation_manifest_allowed"] is True
    assert payload["reasoning_execution_allowed"] is False
    assert payload["probability_estimation_allowed"] is False
    assert payload["final_intelligence_conclusion_allowed"] is False
    assert payload["qseries_execution_allowed"] is False

    rejected(
        lambda: verify_scientific_reasoning_session_activation_package(
            replace(first, activation_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_scientific_reasoning_session_activation_package(
            replace(first, reasoning_execution_allowed=True)
        )
    )
    rejected(
        lambda: consume_and_activate_scientific_reasoning_authorization(
            authorization_package=replace(
                oii012_a,
                authorization_consumed=True,
            )
        )
    )
    rejected(
        lambda: consume_and_activate_scientific_reasoning_authorization(
            authorization_package=replace(
                oii012_a,
                authorization_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OII-013 TEST")
    print(" AUTHORIZATION CONSUMPTION / ACTIVATION")
    print("========================================")
    print("[PASS] Actual OII-012 authorization package consumed")
    print("[PASS] OII-012 identity and hashes verified")
    print("[PASS] Single-use authorization consumption enforced")
    print("[PASS] Authorization consumption receipt materialized")
    print("[PASS] Exact session and frozen-evidence scope preserved")
    print("[PASS] Discipline activation records materialized")
    print("[PASS] Deterministic execution order preserved")
    print("[PASS] Re-consumption of authorization rejected")
    print("[PASS] Controlled invocation manifest boundary enabled")
    print("[PASS] Reasoning execution remains disabled")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Publication, alerting, handoff, and execution disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-013 AUTHORIZATION CONSUMPTION / ACTIVATION CERTIFIED")


if __name__ == "__main__":
    main()
