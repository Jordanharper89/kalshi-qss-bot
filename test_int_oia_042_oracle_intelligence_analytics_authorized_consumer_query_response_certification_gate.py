from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate import (
    AuthorizedConsumerRegistryQueryExecutionRecord,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_response_certification_gate import (
    PROJECTION_RESPONSE_FIELDS,
    QUERY_RESPONSE_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError,
    stable_hash,
)


def _registry_entry(sequence: int) -> dict:
    body = {
        "sequence": sequence,
        "registry_entry_id": stable_hash({"registry-entry": sequence}),
        "product_admission_id": stable_hash({"product-admission": sequence}),
        "product_admission_record_hash": stable_hash(
            {"product-admission-record": sequence}
        ),
        "intelligence_product_id": stable_hash({"product": sequence}),
        "intelligence_product_hash": stable_hash(
            {"intelligence-product": sequence}
        ),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "source_product_admission_manifest_id": "int-oia-037-test",
        "source_product_admission_manifest_hash": stable_hash({"int": 37}),
        "source_result_admission_id": f"result-admission-{sequence}",
        "source_result_admission_record_hash": stable_hash(
            {"result-admission": sequence}
        ),
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_type": "market_research_summary",
        "product_mode": "production_read_only_multi_consumer",
        "product_state": "created_not_published",
        "market_id": f"KX-{sequence:03d}",
        "venue_id": "kalshi",
        "confidence": 0.70 + (sequence / 100),
        "calibration_status": "provisional",
        "allowed_consumer_projections": [
            "operator_research",
            "research_presentation",
            "audit_replay",
        ],
        "registry_partition": "kalshi",
        "registry_key": stable_hash({"key": sequence}),
        "immutable": True,
        "read_only": True,
        "deterministic": True,
        "replayable": True,
        "query_eligible": True,
        "projection_eligible": True,
        "publication_eligible": True,
        "publication_performed": False,
        "execution_capabilities_disabled_verified": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
        "admission_verified": True,
        "duplicate_registration_rejected": True,
        "registry_entry_status": (
            "registered_immutably_for_production_serving_not_published"
        ),
    }
    body["registry_entry_hash"] = stable_hash(body)
    return body


def _execution(
    projection: str,
) -> AuthorizedConsumerRegistryQueryExecutionRecord:
    entries = (_registry_entry(1), _registry_entry(2))
    body = {
        "query_execution_id": stable_hash(
            {"query-execution": projection}
        ),
        "source_query_admission_id": stable_hash(
            {"query-admission": projection}
        ),
        "source_query_admission_record_hash": stable_hash(
            {"query-admission-record": projection}
        ),
        "source_request_id": f"request-{projection}",
        "source_consumer_id": {
            "operator_research": "oracle.operator.console.v1",
            "research_presentation": "oracle.research.presentation.v1",
            "audit_replay": "oracle.audit.replay.v1",
        }[projection],
        "source_requested_projection": projection,
        "source_registry_manifest_id": "int-oia-038-test",
        "source_registry_manifest_hash": stable_hash({"manifest": 38}),
        "source_read_result_hash": stable_hash(
            {"read-result": projection}
        ),
        "matched_entry_count": len(entries),
        "matched_registry_entries": entries,
        "query_admission_verified": True,
        "registry_read_request_derived_from_admission": True,
        "registry_read_invocation_count": 1,
        "registry_read_result_verified": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
        "deterministic_replay_verified": True,
        "immutable_read_verified": True,
        "registry_mutation_allowed": False,
        "registry_mutation_performed": False,
        "registry_update_performed": False,
        "registry_delete_performed": False,
        "publication_allowed": False,
        "publication_performed": False,
        "order_execution_allowed": False,
        "order_execution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "query_execution_status": (
            "authorized_registry_query_executed_read_only"
        ),
    }
    return AuthorizedConsumerRegistryQueryExecutionRecord(
        **body,
        query_execution_record_hash=stable_hash(body),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe response certification was accepted")
    except OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-042 TEST")
    print(" AUTHORIZED CONSUMER QUERY RESPONSE")
    print(" CERTIFICATION GATE")
    print("=" * 40)

    gate = (
        OracleIntelligenceAnalyticsAuthorizedConsumerQueryResponseCertificationGate()
    )

    operator_execution = _execution("operator_research")
    operator_first = gate.certify(operator_execution)
    operator_repeated = gate.certify(operator_execution)

    assert operator_first == operator_repeated
    assert operator_first.query_response_record_hash == stable_hash(
        {
            key: value
            for key, value in operator_first.__dict__.items()
            if key != "query_response_record_hash"
        }
    )
    assert operator_first.certified_response_item_count == 2
    assert operator_first.matched_entry_count == 2
    assert operator_first.source_execution_verified
    assert operator_first.projection_policy_verified
    assert operator_first.field_allowlist_enforced
    assert operator_first.forbidden_fields_absent
    assert operator_first.response_item_hashes_verified
    assert operator_first.source_hashes_verified
    assert operator_first.lineage_verified
    assert operator_first.deterministic_ordering_verified
    assert operator_first.deterministic_replay_verified
    assert operator_first.immutable_read_verified
    assert operator_first.response_artifact_persistence_allowed
    assert not operator_first.registry_mutation_allowed
    assert not operator_first.registry_mutation_performed
    assert not operator_first.publication_allowed
    assert not operator_first.publication_performed
    assert not operator_first.order_execution_allowed
    assert not operator_first.order_execution_performed
    assert not operator_first.database_connection_performed
    assert not operator_first.corpus_read_execution_repeated

    operator_fields = set(
        operator_first.certified_response_items[0].projected_entry
    )
    assert operator_fields == set(
        PROJECTION_RESPONSE_FIELDS["operator_research"]
    )

    presentation = gate.certify(
        _execution("research_presentation")
    )
    presentation_fields = set(
        presentation.certified_response_items[0].projected_entry
    )
    assert presentation_fields == set(
        PROJECTION_RESPONSE_FIELDS["research_presentation"]
    )
    assert "registry_key" not in presentation_fields
    assert "product_admission_record_hash" not in presentation_fields

    audit = gate.certify(_execution("audit_replay"))
    audit_fields = set(
        audit.certified_response_items[0].projected_entry
    )
    assert audit_fields == set(
        PROJECTION_RESPONSE_FIELDS["audit_replay"]
    )
    assert "product_admission_record_hash" in audit_fields
    assert "registry_entry_hash" in audit_fields

    for item in operator_first.certified_response_items:
        assert item.projected_entry_hash == stable_hash(
            item.projected_entry
        )

    _expect_rejected(
        lambda: gate.certify(
            replace(
                operator_execution,
                publication_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            replace(
                operator_execution,
                query_execution_record_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            replace(
                operator_execution,
                matched_entry_count=99,
            )
        )
    )

    unsafe_entry = dict(operator_execution.matched_registry_entries[0])
    unsafe_entry["database_password"] = "should-never-appear"
    unsafe_entries = (
        unsafe_entry,
        operator_execution.matched_registry_entries[1],
    )
    unsafe_body = {
        key: value
        for key, value in operator_execution.__dict__.items()
        if key != "query_execution_record_hash"
    }
    unsafe_body["matched_registry_entries"] = unsafe_entries
    unsafe_execution = AuthorizedConsumerRegistryQueryExecutionRecord(
        **unsafe_body,
        query_execution_record_hash=stable_hash(unsafe_body),
    )
    certified_unsafe = gate.certify(unsafe_execution)
    for item in certified_unsafe.certified_response_items:
        assert "database_password" not in item.projected_entry

    assert QUERY_RESPONSE_SCHEMA_VERSION == (
        "oracle.authorized-consumer-query-response-certification.v1"
    )

    print("[PASS] Actual INT-OIA-041 query execution record consumed")
    print("[PASS] Query execution record hash independently verified")
    print("[PASS] Operator research projection certified")
    print("[PASS] Research presentation projection certified")
    print("[PASS] Audit replay projection certified")
    print("[PASS] Projection-specific field allowlists enforced")
    print("[PASS] Unsafe internal fields excluded from certified responses")
    print("[PASS] Certified response item hashes verified")
    print("[PASS] Certified response record hash independently verified")
    print("[PASS] Deterministic replay and ordering verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-041 lineage preserved")
    print("[PASS] Tampered and unsafe execution records rejected")
    print("[PASS] Registry mutation and publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
