from __future__ import annotations

from dataclasses import replace

from test_oop_019_oracle_operator_research_response_materialization_readiness_gate import (
    _consumption,
)

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_readiness_gate import (
    OracleOperatorResearchResponseMaterializationReadinessGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_gate import (
    AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE,
    OracleOperatorResearchResponseMaterializationAuthorizationGate,
    OracleOperatorResearchResponseMaterializationAuthorizationInvariantError,
    stable_hash,
)


def _readiness():
    return OracleOperatorResearchResponseMaterializationReadinessGate().evaluate(
        consumption=_consumption()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe materialization authorization accepted")
    except OracleOperatorResearchResponseMaterializationAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-020 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    readiness = _readiness()
    gate = OracleOperatorResearchResponseMaterializationAuthorizationGate()

    first = gate.authorize(readiness=readiness)
    repeated = gate.authorize(readiness=readiness)

    assert first == repeated
    assert first.research_response_materialization_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_authorization_hash"
        }
    )

    assert first.source_research_response_materialization_readiness_id == readiness.research_response_materialization_readiness_id
    assert first.source_research_response_materialization_readiness_hash == readiness.research_response_materialization_readiness_hash
    assert first.authorization_type == AUTHORIZATION_TYPE
    assert first.authorized_entry_count == readiness.response_entry_count
    assert first.authorized_result_count == readiness.response_result_count
    assert first.authorized_response_artifact_entry_ids == readiness.response_artifact_entry_ids
    assert first.authorized_query_response_ids == readiness.response_query_response_ids
    assert first.authorized_result_hashes == readiness.response_result_hashes
    assert first.authorized_result_payloads == readiness.response_result_payloads

    assert first.readiness_type_verified
    assert first.readiness_identity_verified
    assert first.readiness_hash_verified
    assert first.readiness_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.response_input_package_verified
    assert first.response_schema_inputs_verified
    assert first.response_content_inputs_verified
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.single_use_authorization_verified
    assert first.deterministic_authorization_verified

    assert first.query_subsystem_complete
    assert first.research_response_handoff_ready
    assert first.research_response_handoff_authorized
    assert first.research_response_handoff_consumed
    assert first.research_response_materialization_ready
    assert first.research_response_materialization_authorized
    assert first.research_response_materialization_allowed
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
    assert first.authorization_status == AUTHORIZATION_STATUS

    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                research_response_materialization_readiness_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                readiness_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                response_result_hashes=("0" * 64,) * readiness.response_result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                response_result_count=readiness.response_result_count + 1,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                research_response_materialization_authorized=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-019 materialization readiness consumed")
    print("[PASS] OOP-019 identity, hash, status, and lineage verified")
    print("[PASS] Response payload hashes recomputed and verified")
    print("[PASS] Exact response identities and cardinality preserved")
    print("[PASS] Frozen Research Response scope preserved")
    print("[PASS] Single-use materialization authorization created")
    print("[PASS] Research Response materialization is now allowed")
    print("[PASS] Research Response materialization not yet performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, replayed, malformed, and unsafe readiness rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
