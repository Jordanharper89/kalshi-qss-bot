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
    OracleScientificReasoningSessionReadinessInvariantError,
    evaluate_scientific_reasoning_session_readiness,
    serialize_scientific_reasoning_session_readiness_package,
    verify_scientific_reasoning_session_readiness_package,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleScientificReasoningSessionReadinessInvariantError:
        return
    raise AssertionError("expected OII-011 invariant rejection")


def build_oii010(reverse: bool = False):
    now = datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc)
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
        subject_id="kalshi:market:readiness-test",
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
    return materialize_scientific_reasoning_session(
        reasoning_input_manifest=oii009
    )


def main() -> None:
    oii010_a = build_oii010(False)
    oii010_b = build_oii010(True)

    first = evaluate_scientific_reasoning_session_readiness(
        reasoning_session=oii010_a
    )
    second = evaluate_scientific_reasoning_session_readiness(
        reasoning_session=oii010_b
    )

    assert first == second
    assert first.readiness_hash == second.readiness_hash
    assert verify_scientific_reasoning_session_readiness_package(first)

    assert first.session_readiness_verified is True
    assert first.session_readiness_status == "ready_for_authorization_review"
    assert first.blocked_discipline_count == 0
    assert first.ready_discipline_count == len(
        first.discipline_readiness_assessments
    )
    assert first.deterministic_execution_order == (
        "information_theory",
        "bayesian_inference",
        "causal_inference",
        "calibration_science",
    )
    assert all(
        item.readiness_status == "ready_for_authorization_review"
        for item in first.discipline_readiness_assessments
    )
    assert all(
        item.execution_disabled_verified
        and item.probability_estimation_disabled_verified
        and item.conclusion_generation_disabled_verified
        for item in first.discipline_readiness_assessments
    )

    payload = json.loads(
        serialize_scientific_reasoning_session_readiness_package(first)
    )
    assert payload["engine_id"] == "OII-011"
    assert payload["reasoning_execution_allowed"] is False
    assert payload["probability_estimation_allowed"] is False
    assert payload["final_intelligence_conclusion_allowed"] is False
    assert payload["qseries_execution_allowed"] is False

    rejected(
        lambda: verify_scientific_reasoning_session_readiness_package(
            replace(first, readiness_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_scientific_reasoning_session_readiness_package(
            replace(first, reasoning_execution_allowed=True)
        )
    )
    rejected(
        lambda: evaluate_scientific_reasoning_session_readiness(
            reasoning_session=replace(
                oii010_a,
                session_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OII-011 TEST")
    print(" SCIENTIFIC REASONING SESSION READINESS")
    print("========================================")
    print("[PASS] Actual OII-010 reasoning session consumed")
    print("[PASS] OII-010 identity and hashes verified")
    print("[PASS] Frozen certified-evidence binding verified")
    print("[PASS] Discipline materialization verified")
    print("[PASS] Deterministic execution order verified")
    print("[PASS] All discipline ordinals verified")
    print("[PASS] Readiness assessed without executing reasoning")
    print("[PASS] Session ready only for authorization review")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Publication, alerting, handoff, and execution disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-011 SCIENTIFIC REASONING READINESS CERTIFIED")


if __name__ == "__main__":
    main()
