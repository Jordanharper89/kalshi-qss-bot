from __future__ import annotations

from dataclasses import replace

from test_oop_017_oracle_operator_query_resolution_research_response_handoff_authorization_gate import (
    _certification,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_research_response_handoff_authorization_gate import (
    OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_handoff_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    RESPONSE_INPUT_PACKAGE_TYPE,
    OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate,
    OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate().authorize(
        certification=_certification()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe handoff consumption accepted")
    except OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-018 TEST")
    print(" RESEARCH RESPONSE HANDOFF")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.research_response_handoff_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_handoff_consumption_hash"
        }
    )

    assert first.source_research_response_handoff_authorization_id == authorization.research_response_handoff_authorization_id
    assert first.source_research_response_handoff_authorization_hash == authorization.research_response_handoff_authorization_hash
    assert first.response_input_package_type == RESPONSE_INPUT_PACKAGE_TYPE
    assert first.consumed_entry_count == authorization.handoff_entry_count
    assert first.consumed_result_count == authorization.handoff_result_count
    assert first.consumed_response_artifact_entry_ids == authorization.handoff_response_artifact_entry_ids
    assert first.consumed_query_response_ids == authorization.handoff_query_response_ids
    assert first.consumed_result_hashes == authorization.handoff_result_hashes
    assert first.consumed_result_payloads == authorization.handoff_result_payloads

    assert first.handoff_type_verified
    assert first.handoff_identity_verified
    assert first.handoff_hash_verified
    assert first.handoff_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.single_use_consumption_verified
    assert first.deterministic_consumption_verified

    assert first.query_subsystem_complete
    assert first.research_response_handoff_ready
    assert first.research_response_handoff_authorized
    assert first.research_response_handoff_consumed
    assert not first.research_response_materialization_ready
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
    assert first.consumption_status == CONSUMPTION_STATUS

    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                research_response_handoff_authorization_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                handoff_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                handoff_result_hashes=("0" * 64,) * authorization.handoff_result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                research_response_handoff_consumed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                research_response_materialization_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-017 handoff authorization consumed")
    print("[PASS] OOP-017 identity, hash, status, and lineage verified")
    print("[PASS] Certified result hashes recomputed and verified")
    print("[PASS] Frozen handoff scope preserved")
    print("[PASS] Single-use immutable response input package created")
    print("[PASS] Research Response handoff marked consumed")
    print("[PASS] Research Response materialization remains gated")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, replayed, malformed, and unsafe handoffs rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
