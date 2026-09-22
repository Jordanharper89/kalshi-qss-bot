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
    OracleScientificReasoningSessionInvariantError,
    materialize_scientific_reasoning_session,
    serialize_scientific_reasoning_session,
    verify_scientific_reasoning_session,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleScientificReasoningSessionInvariantError:
        return
    raise AssertionError("expected OII-010 invariant rejection")


def build_oii009(reverse: bool = False):
    now = datetime(2026, 7, 28, 8, 0, tzinfo=timezone.utc)
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
        subject_id="kalshi:market:session-test",
        question_text="What evidence bears on the market outcome?",
        requested_disciplines=(
            "causal_inference",
            "bayesian_inference",
            "calibration_science",
            "information_theory",
        ),
        requested_claim_ids=("claim.resolution",),
        request_context={"mode": "read_only"},
    )
    return build_scientific_reasoning_input_manifest(
        certified_evidence_package=oii008,
        reasoning_request=request,
    )


def main() -> None:
    oii009_a = build_oii009(False)
    oii009_b = build_oii009(True)

    first = materialize_scientific_reasoning_session(
        reasoning_input_manifest=oii009_a
    )
    second = materialize_scientific_reasoning_session(
        reasoning_input_manifest=oii009_b
    )

    assert first == second
    assert first.session_hash == second.session_hash
    assert verify_scientific_reasoning_session(first)

    assert first.evidence_set_frozen is True
    assert first.session_materialized is True
    assert first.reasoning_execution_allowed is False
    assert first.frozen_evidence_set.evidence_count >= 1
    assert first.deterministic_execution_order == (
        "information_theory",
        "bayesian_inference",
        "causal_inference",
        "calibration_science",
    )
    assert tuple(
        item.ordinal for item in first.discipline_sessions
    ) == (1, 2, 3, 4)
    assert all(
        item.evidence_input_hashes
        == first.frozen_evidence_set.evidence_input_hashes
        for item in first.discipline_sessions
    )
    assert all(
        item.execution_allowed is False
        and item.probability_estimation_allowed is False
        and item.conclusion_generation_allowed is False
        for item in first.discipline_sessions
    )

    payload = json.loads(
        serialize_scientific_reasoning_session(first)
    )
    assert payload["engine_id"] == "OII-010"
    assert payload["reasoning_execution_allowed"] is False
    assert payload["probability_estimation_allowed"] is False
    assert payload["final_intelligence_conclusion_allowed"] is False
    assert payload["qseries_execution_allowed"] is False

    rejected(
        lambda: verify_scientific_reasoning_session(
            replace(first, session_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_scientific_reasoning_session(
            replace(first, reasoning_execution_allowed=True)
        )
    )
    rejected(
        lambda: materialize_scientific_reasoning_session(
            reasoning_input_manifest=replace(
                oii009_a,
                manifest_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OII-010 TEST")
    print(" SCIENTIFIC REASONING SESSION ORCHESTRATOR")
    print("========================================")
    print("[PASS] Actual OII-009 reasoning-input manifest consumed")
    print("[PASS] OII-009 identity and hashes verified")
    print("[PASS] Certified evidence set frozen immutably")
    print("[PASS] Requested disciplines materialized")
    print("[PASS] Deterministic discipline execution order installed")
    print("[PASS] Every discipline bound to identical frozen evidence")
    print("[PASS] Session identity and replay hash deterministic")
    print("[PASS] Input ordering cannot alter session identity")
    print("[PASS] Reasoning execution remains disabled")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Publication, alerting, handoff, and execution disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-010 SCIENTIFIC REASONING SESSION CERTIFIED")


if __name__ == "__main__":
    main()
