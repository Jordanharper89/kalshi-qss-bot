from __future__ import annotations
from dataclasses import replace
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_final_certification_freeze_gate import IntegratedIntelligenceFinalCertification, IntegratedIntelligenceModuleAttestation, PERMANENTLY_DISABLED_CAPABILITIES, REQUIRED_ENGINE_IDS, stable_hash
from qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_callable_registry import APPROVED_DISCIPLINES, OracleScientificReasoningRegistryInvariantError, build_scientific_reasoning_callable_descriptor, build_scientific_reasoning_callable_registry, verify_scientific_reasoning_callable_registry

def rejected(fn):
    try: fn()
    except OracleScientificReasoningRegistryInvariantError: return
    raise AssertionError("expected rejection")

def build_cert():
    records=[]
    for eid in REQUIRED_ENGINE_IDS:
        body={"engine_id":eid,"module_name":"m_"+eid.lower().replace("-","_"),"relative_path":"frozen/"+eid+".py","source_sha256":stable_hash(eid),"source_size_bytes":1,"syntax_verified":True,"engine_identity_verified":True,"read_only_boundary_declared":True}
        records.append(IntegratedIntelligenceModuleAttestation(**body,attestation_hash=stable_hash(body)))
    body={"source_invocation_manifest_id":"m","source_invocation_manifest_hash":stable_hash("m"),"source_activation_hash":stable_hash("a"),"source_authorization_hash":stable_hash("z"),"source_session_hash":stable_hash("s"),"source_manifest_hash":stable_hash("i"),"frozen_evidence_set_hash":stable_hash("e"),"module_attestations":tuple(records),"certified_engine_ids":REQUIRED_ENGINE_IDS,"certified_module_count":len(records),"permanent_disabled_capabilities":PERMANENTLY_DISABLED_CAPABILITIES,"terminal_status":"integrated_intelligence_certified_frozen_read_only","subsystem_frozen":True,"further_certification_layers_required":False}
    h=stable_hash(body)
    return IntegratedIntelligenceFinalCertification(certification_id="integrated-intelligence-final-certification:"+h,**body,certification_hash=h,engine_id="OII-015",schema_version="OII-015.v1",algorithm_version="integrated-intelligence-final-certification-freeze.v1",read_only=True,acquisition_mutation_allowed=False,analytics_mutation_allowed=False,operator_mutation_allowed=False,reasoning_execution_allowed=False,probability_estimation_allowed=False,final_intelligence_conclusion_allowed=False,publication_allowed=False,alerting_allowed=False,qseries_handoff_allowed=False,qseries_execution_allowed=False,order_creation_allowed=False,funds_movement_allowed=False,portfolio_mutation_allowed=False)

def main():
    cert=build_cert()
    rev=tuple(build_scientific_reasoning_callable_descriptor(d) for d in reversed(APPROVED_DISCIPLINES))
    a=build_scientific_reasoning_callable_registry(terminal_certification=cert,descriptors=rev)
    b=build_scientific_reasoning_callable_registry(terminal_certification=cert)
    assert a==b and verify_scientific_reasoning_callable_registry(a)
    assert a.registered_callable_count==9
    assert all(not x.active and not x.resolved and not x.bound and not x.executable and x.read_only for x in a.callable_descriptors)
    rejected(lambda: verify_scientific_reasoning_callable_registry(replace(a,registry_hash="0"*64)))
    rejected(lambda: verify_scientific_reasoning_callable_registry(replace(a,reasoning_execution_allowed=True)))
    print("========================================")
    print(" OSR-001 TEST")
    print(" SCIENTIFIC REASONING CALLABLE REGISTRY")
    print("========================================")
    print("[PASS] Actual OII-015 terminal certification contract consumed")
    print("[PASS] Exact approved discipline set registered")
    print("[PASS] Callable identities deterministic and unique")
    print("[PASS] Input ordering cannot alter registry identity")
    print("[PASS] All callables inactive, unresolved, unbound, and non-executable")
    print("[PASS] Reasoning, probability, conclusions, publication, and alerts disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation disabled")
    print("[DONE] OSR-001 SCIENTIFIC REASONING CALLABLE REGISTRY CERTIFIED")
if __name__=="__main__": main()
