from __future__ import annotations

from dataclasses import replace

from test_oop_016_oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import (
    _execution,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import (
    OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_research_response_handoff_authorization_gate import (
    HANDOFF_STATUS,
    HANDOFF_TYPE,
    OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate,
    OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError,
    stable_hash,
)


def _certification():
    return (
        OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate()
    ).certify(
        execution=_execution()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe research-response handoff accepted")
    except OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-017 TEST")
    print(" QUERY TO RESEARCH RESPONSE HANDOFF")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate()

    first = gate.authorize(certification=certification)
    repeated = gate.authorize(certification=certification)

    assert first == repeated
    assert first.research_response_handoff_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_handoff_authorization_hash"
        }
    )

    assert first.source_execution_result_certification_id == certification.execution_result_certification_id
    assert first.source_execution_result_certification_hash == certification.execution_result_certification_hash
    assert first.handoff_type == HANDOFF_TYPE
    assert first.handoff_entry_count == certification.certified_entry_count
    assert first.handoff_result_count == certification.certified_result_count
    assert first.handoff_response_artifact_entry_ids == certification.certified_response_artifact_entry_ids
    assert first.handoff_query_response_ids == certification.certified_query_response_ids
    assert first.handoff_result_hashes == certification.certified_result_hashes
    assert first.handoff_result_payloads == certification.certified_result_payloads

    assert first.certification_type_verified
    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.certified_result_type_verified
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.deterministic_handoff_verified

    assert first.query_subsystem_complete
    assert first.research_response_handoff_ready
    assert first.research_response_handoff_authorized
    assert not first.research_response_handoff_consumed
    assert not first.research_response_materialization_allowed
    assert not first.research_response_materialization_performed
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed
    assert first.handoff_status == HANDOFF_STATUS

    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                execution_result_certification_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                certification_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                certified_result_hashes=("0" * 64,) * certification.certified_result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                research_response_materialization_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                operator_session_construction_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-016 certified result consumed")
    print("[PASS] OOP-016 identity, hash, status, and lineage verified")
    print("[PASS] Certified payload hashes recomputed and verified")
    print("[PASS] Frozen query-result scope preserved")
    print("[PASS] Query subsystem completion certified")
    print("[PASS] Research Response handoff authorized")
    print("[PASS] Research Response materialization not yet performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe certifications rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
