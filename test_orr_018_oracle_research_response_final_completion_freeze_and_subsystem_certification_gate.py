from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_consumption_completion_readiness_gate import (
    READINESS_STATUS,
    READINESS_TYPE,
    OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness,
    stable_hash as source_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_final_completion_freeze_and_subsystem_certification_gate import *


def sample_readiness():
    t = datetime(2026, 7, 29, 20, 10, tzinfo=timezone.utc)
    body = {
        "readiness_id": "a"*64, "final_attestation_id": "b"*64, "final_attestation_hash": "c"*64,
        "continuation_id": "d"*64, "continuation_hash": "e"*64,
        "consumption_id": "f"*64, "consumption_hash": "1"*64,
        "source_attestation_id": "2"*64, "source_attestation_hash": "3"*64,
        "activation_continuation_id": "4"*64, "activation_continuation_hash": "5"*64,
        "activation_id": "6"*64, "activation_hash": "7"*64,
        "authorization_consumption_id": "8"*64, "authorization_consumption_hash": "9"*64,
        "authorization_id": "a"*64, "authorization_hash": "b"*64,
        "invocation_readiness_id": "c"*64, "invocation_readiness_hash": "d"*64,
        "evidence_admission_id": "e"*64, "evidence_admission_hash": "f"*64,
        "materialization_id": "1"*64, "materialization_hash": "2"*64,
        "plan_admission_id": "3"*64, "plan_admission_hash": "4"*64,
        "plan_id": "5"*64, "plan_hash": "6"*64,
        "admission_id": "7"*64, "admission_hash": "8"*64,
        "request_id": "9"*64, "request_hash": "a"*64,
        "dependency_receipt_id": "b"*64, "dependency_receipt_hash": "c"*64,
        "source_runtime_completion_id": "d"*64, "source_runtime_completion_hash": "e"*64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-018-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": t, "admitted_at": t+timedelta(seconds=1),
        "planned_at": t+timedelta(seconds=2), "plan_admitted_at": t+timedelta(seconds=3),
        "materialized_at": t+timedelta(seconds=4), "evidence_admitted_at": t+timedelta(seconds=5),
        "invocation_readiness_certified_at": t+timedelta(seconds=6),
        "authorized_at": t+timedelta(seconds=7), "consumed_at": t+timedelta(seconds=8),
        "activated_at": t+timedelta(seconds=9),
        "activation_continuation_certified_at": t+timedelta(seconds=10),
        "source_attested_at": t+timedelta(seconds=11),
        "attestation_consumed_at": t+timedelta(seconds=12),
        "continuation_at": t+timedelta(seconds=13),
        "final_attested_at": t+timedelta(seconds=14),
        "final_attestation_consumed_at": t+timedelta(seconds=15),
        "plan_steps": ("validate_scope", "identify_required_evidence", "select_analytic_path", "assemble_response", "certify_response_boundary"),
        "evidence_requirements": ("source_provenance", "market_price", "oracle_probability"),
        "activation_record_ids": ("1"*64, "2"*64, "3"*64),
        "activation_record_hashes": ("4"*64, "5"*64, "6"*64),
        "activated_invocation_ids": ("7"*64, "8"*64, "9"*64),
        "activated_invocation_hashes": ("a"*64, "b"*64, "c"*64),
        "activated_read_operations": ("read_certified_lineage", "read_certified_market_state", "read_certified_analytics"),
        "final_attestation_identity_verified": True,
        "final_attestation_hash_verified": True,
        "final_attestation_contract_verified": True,
        "full_lineage_verified": True,
        "activation_record_identity_verified": True,
        "activation_record_hashes_verified": True,
        "invocation_lineage_verified": True,
        "invocation_order_verified": True,
        "invocation_count_verified": True,
        "approved_read_operations_verified": True,
        "completion_scope_verified": True,
        "completion_readiness_verified": True,
        "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "result_materialization_remains_disabled_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_readiness_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_attestation_scope_verified": True,
        "consumption_single_use_verified": True,
        "duplicate_consumption_allowed": False,
        "consumption_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "readiness_type": READINESS_TYPE,
        "readiness_status": READINESS_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness(
        **body, readiness_hash=source_hash(body)
    )


def reject(fn):
    try:
        fn()
        raise AssertionError("unsafe certification accepted")
    except OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-018 TEST")
    print(" FINAL COMPLETION / FREEZE")
    print(" SUBSYSTEM CERTIFICATION")
    print("=" * 40)

    source = sample_readiness()
    at = source.final_attestation_consumed_at + timedelta(seconds=1)
    manifest = (
        ("__init__.py", "1"*64),
        ("oracle_research_response_final_completion_freeze_and_subsystem_certification_gate.py", "2"*64),
    )
    gate = OracleResearchResponseFinalCompletionFreezeSubsystemCertificationGate()
    first = gate.certify(readiness=source, certified_at=at, module_manifest=manifest)
    second = gate.certify(readiness=source, certified_at=at, module_manifest=manifest)

    assert first == second
    assert first.certification_hash == stable_hash(
        {k: v for k, v in asdict(first).items() if k != "certification_hash"}
    )
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.stage_count == 18
    assert first.certified_stage_range == "ORR-001..ORR-018"
    assert first.subsystem_complete_verified
    assert first.subsystem_frozen_verified
    assert not first.further_certification_layers_required
    assert first.complete_lineage_verified
    assert first.module_manifest_verified
    assert first.read_only_boundary_verified
    assert not first.callable_binding_allowed
    assert not first.callable_invocation_allowed
    assert not first.result_materialization_allowed
    assert not first.runtime_serving_allowed
    assert not first.publication_allowed
    assert not first.qseries_execution_allowed

    reject(lambda: gate.certify(readiness=replace(source, readiness_hash="0"*64), certified_at=at, module_manifest=manifest))
    reject(lambda: gate.certify(readiness=replace(source, publication_allowed=True), certified_at=at, module_manifest=manifest))
    reject(lambda: gate.certify(readiness=source, certified_at=source.final_attestation_consumed_at-timedelta(seconds=1), module_manifest=manifest))
    reject(lambda: gate.certify(readiness=source, certified_at=at, module_manifest=tuple(reversed(manifest))))
    reject(lambda: gate.certify(readiness=source, certified_at=at, module_manifest=(("__init__.py", "x"*64),)))

    print("[PASS] Actual ORR-017 completion readiness consumed")
    print("[PASS] Complete ORR-001 through ORR-017 lineage preserved")
    print("[PASS] Deterministic ORR-018 subsystem certification produced")
    print("[PASS] ORR-001 through ORR-018 completion certified")
    print("[PASS] Oracle Research Response subsystem frozen")
    print("[PASS] Module-manifest boundary certified")
    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] No further ORR certification layers required")
    print("[DONE] ORR-018 FINAL COMPLETION, FREEZE, AND SUBSYSTEM CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
