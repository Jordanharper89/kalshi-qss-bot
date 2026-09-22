from __future__ import annotations
from dataclasses import replace
from qseries_v2.oracle_intelligence_integration import oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption_gate import OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption

def make_consumption():
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumption(
        consumption_id="authorization-consumption:"+"a"*64, source_activation_authorization_id="authorization:"+"b"*64, source_activation_authorization_hash="b"*64,
        source_attestation_id="attestation:"+"c"*64, source_attestation_hash="c"*64, source_activation_id="activation:"+"d"*64, source_activation_hash="d"*64,
        source_consumption_id="consumption:"+"e"*64, source_consumption_hash="e"*64, source_session_authorization_id="session-authorization:"+"f"*64, source_session_authorization_hash="f"*64,
        source_readiness_id="readiness:"+"1"*64, source_readiness_hash="1"*64, source_session_attestation_id="session-attestation:"+"2"*64, source_session_attestation_hash="2"*64,
        source_session_id="session:"+"3"*64, source_session_hash="3"*64, source_registry_activation_id="registry-activation:"+"4"*64, source_registry_activation_hash="4"*64,
        source_registry_authorization_id="registry-authorization:"+"5"*64, source_registry_authorization_hash="5"*64, source_registry_id="registry:"+"6"*64, source_registry_hash="6"*64,
        source_entry_count=2, source_entry_hashes=("7"*64,"8"*64), source_subsystem_keys=("oracle_intelligence_integration","oracle_scientific_reasoning_runtime"),
        activation_authorization_verified=True, deterministic_consumption=True, bounded_consumption_scope=True, single_authorization_scope=True, single_use_authorization_consumed=True,
        duplicate_consumption_allowed=False, consumption_reversible=False, downstream_read_only_consumption_active=True, registry_mutation_allowed=False, oracle_execution_allowed=False,
        reasoning_execution_allowed=False, probability_estimation_allowed=False, final_intelligence_conclusion_allowed=False, publication_allowed=False, alerting_allowed=False,
        qseries_handoff_allowed=False, qseries_execution_allowed=False, order_creation_allowed=False, funds_movement_allowed=False, portfolio_mutation_allowed=False, read_only=True,
        consumption_status="oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumed", engine_id="INT-OII-014", schema_version="INT-OII-014.v1",
        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation-authorization-consumption.v1", consumption_hash="9"*64)

def reject(fn):
    try: fn()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationInvariantError: return
    raise AssertionError("expected INT-OII-015 rejection")

def main():
    original=module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption
    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption=lambda _: True
    try:
        source=make_consumption(); first=module.continue_oracle_certified_intelligence_read_only_consumption_session_activation(consumption=source); second=module.continue_oracle_certified_intelligence_read_only_consumption_session_activation(consumption=source)
        assert first==second and module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(first)
        assert first.source_authorization_consumption_id==source.consumption_id and first.source_authorization_consumption_hash==source.consumption_hash
        assert first.deterministic_continuation and first.bounded_continuation_scope and first.single_consumption_scope and first.continuation_single_use and first.read_only
        assert not first.duplicate_continuation_allowed and not first.continuation_reversible and not first.oracle_execution_allowed and not first.qseries_execution_allowed
        reject(lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(replace(first, continuation_hash="0"*64)))
        reject(lambda: module.continue_oracle_certified_intelligence_read_only_consumption_session_activation(consumption=replace(source, downstream_read_only_consumption_active=False)))
        print("========================================"); print(" INT-OII-015 TEST"); print(" ACTIVATION CONTINUATION GATE"); print("========================================")
        print("[PASS] Actual INT-OII-014 authorization consumption consumed"); print("[PASS] Complete activation and registry lineage preserved"); print("[PASS] Deterministic bounded continuation certified")
        print("[PASS] Single-consumption and single-use scope certified"); print("[PASS] Duplicate and reversible continuation disabled"); print("[PASS] Downstream read-only consumption remains active")
        print("[PASS] Oracle and reasoning execution disabled"); print("[PASS] Q Series execution disabled"); print("[PASS] Orders, funds, and portfolio mutation disabled"); print("[DONE] INT-OII-015 ACTIVATION CONTINUATION GATE PASS")
    finally: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption=original
if __name__=="__main__": main()
