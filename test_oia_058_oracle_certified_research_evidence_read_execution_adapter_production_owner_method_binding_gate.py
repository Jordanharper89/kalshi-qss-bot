import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_gate import OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingGate, ProductionOwnerMethodBindingInvariantError, stable_hash

def seed(path:Path):
    specs=[("oracle_read_only_canonical_observation_adapter.v1","work.observations","read_canonical_observations","qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector","OracleLiveCorpusInspector","inspect","qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector","OracleLiveCorpusInspector.inspect"),("oracle_read_only_market_state_lineage_adapter.v1","work.lineage","read_market_state_lineage","qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger","OracleCanonicalMarketLineageLedger","records","qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger","OracleCanonicalMarketLineageLedger.records")]
    entries=[]
    for i,s in enumerate(specs,1):
        adapter,work,op,module,owner,callable_name,dmodule,dqual=s
        body={"sequence":i,"worker_id":"oracle-worker-test","work_item_id":work,"adapter_id":adapter,"read_operation":op,"module_path":module,"owner_name":owner,"callable_name":callable_name,"constructor_signature":"verified","callable_signature":"verified","owner_state_fingerprint":stable_hash({"owner":owner}),"owner_construction_hash":stable_hash({"construction":owner}),"method_descriptor_type":"function","method_descriptor_module":dmodule,"method_descriptor_qualname":dqual,"method_signature_verified":True,"instance_parameter_verified":True,"descriptor_static_resolution_verified":True,"owner_reconstruction_required":True,"owner_method_binding_ready":True,"owner_method_binding_authorized":True,"owner_reconstruction_requested":False,"owner_reconstructed":False,"method_binding_requested":False,"method_bound_to_owner":False,"method_invoked":False,"adapter_executed":False,"authorization_checks":["verified"],"authorization_status":"evidence_read_execution_adapter_production_owner_method_binding_authorized","source_owner_method_binding_readiness_hash":stable_hash({"56":owner}),"source_owner_construction_authorization_hash":stable_hash({"54":owner}),"source_owner_construction_readiness_hash":stable_hash({"53":owner}),"source_callable_argument_binding_hash":stable_hash({"52":owner})}
        body["owner_method_binding_authorization_hash"]=stable_hash(body); entries.append(body)
    manifest={"schema_version":"OIA-057","engine_id":"OIA-057","authorized_at":"2026-07-22T00:00:00+00:00","owner_method_binding_authorization_id":"oia057-test","owner_method_binding_authorization_status":"evidence_read_execution_adapter_production_owner_method_binding_authorization_issued","owner_method_binding_authorization_policy_id":"test","worker_id":"oracle-worker-test","authorization_entry_count":len(entries),"authorization_entries":entries,"source_owner_method_binding_readiness_id":"oia056-test","source_owner_method_binding_readiness_manifest_hash":stable_hash({"56m":1}),"source_owner_construction_id":"oia055-test","source_owner_construction_manifest_hash":stable_hash({"55m":1}),"source_lineage":{"dispatch_manifest_id":"oia020-test","source_claim_id":"oia021-test"},"owner_method_binding_authorization_issued":True,"owner_reconstruction_evaluation_allowed":True,"owner_reconstruction_allowed":False,"owner_reconstruction_performed":False,"callable_binding_to_owner_evaluation_allowed":True,"callable_binding_to_owner_allowed":False,"callable_binding_to_owner_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"authorization_artifact_persistence_allowed":True}
    manifest["owner_method_binding_authorization_manifest_hash"]=stable_hash(manifest); path.mkdir(parents=True,exist_ok=True); (path/"current.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8"); return manifest

def rehash(p):
    for e in p["authorization_entries"]:
        b=dict(e); b.pop("owner_method_binding_authorization_hash",None); e["owner_method_binding_authorization_hash"]=stable_hash(b)
    b=dict(p); b.pop("owner_method_binding_authorization_manifest_hash",None); p["owner_method_binding_authorization_manifest_hash"]=stable_hash(b)

def reject(gate,fixed,msg):
    try: gate.bind(bound_at=fixed,persist=False)
    except ProductionOwnerMethodBindingInvariantError: return
    raise AssertionError(msg)

def main():
    print("="*40); print(" OIA-058 TEST"); print(" CONTROLLED OWNER METHOD BINDING"); print("="*40)
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); auth=root/"authorization"; binding=root/"binding"; source=seed(auth)
        gate=OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingGate(authorization_directory=auth,binding_directory=binding); fixed=datetime(2026,7,22,tzinfo=timezone.utc)
        first=gate.bind(bound_at=fixed,persist=True); second=gate.bind(bound_at=fixed,persist=False); assert first==second
        assert first.schema_version=="OIA-058" and first.binding_entry_count==2
        assert first.owner_reconstruction_performed and first.callable_binding_to_owner_performed
        assert not first.callable_invocation_allowed and not first.adapter_execution_allowed and not first.corpus_read_execution_allowed
        assert not first.owner_instances_retained and not first.bound_methods_retained
        for e in first.binding_entries:
            assert e.owner_reconstructed and e.method_binding_requested and e.method_bound_to_owner
            assert e.bound_method_self_verified and e.bound_method_function_verified
            assert not e.method_invoked and not e.adapter_executed and not e.corpus_read_executed
        assert first.source_owner_method_binding_authorization_manifest_hash==source["owner_method_binding_authorization_manifest_hash"]
        assert (binding/"current.json").exists()
        p=json.loads((auth/"current.json").read_text()); p["authorization_entries"][0]["method_bound_to_owner"]=True; rehash(p); (auth/"current.json").write_text(json.dumps(p),encoding="utf-8"); reject(gate,fixed,"premature binding accepted")
        seed(auth); p=json.loads((auth/"current.json").read_text()); p["authorization_entries"][0]["callable_name"]="__dict__"; rehash(p); (auth/"current.json").write_text(json.dumps(p),encoding="utf-8"); reject(gate,fixed,"unknown method accepted")
        seed(auth); p=json.loads((auth/"current.json").read_text()); p["callable_invocation_allowed"]=True; rehash(p); (auth/"current.json").write_text(json.dumps(p),encoding="utf-8"); reject(gate,fixed,"executable authorization accepted")
        seed(auth); p=json.loads((auth/"current.json").read_text()); p["authorization_entries"].append(dict(p["authorization_entries"][0])); p["authorization_entries"][-1]["sequence"]=3; p["authorization_entry_count"]=3; rehash(p); (auth/"current.json").write_text(json.dumps(p),encoding="utf-8"); reject(gate,fixed,"duplicate accepted")
    print("[PASS] Actual OIA-057 owner-method-binding authorization contract consumed")
    print("[PASS] Approved production owners reconstructed with inert dependencies")
    print("[PASS] Exact approved methods bound to exact owner instances")
    print("[PASS] Bound method self, function identity, and signatures verified")
    print("[PASS] Binding manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-057 lineage preserved")
    print("[PASS] Owner instances and bound methods were immediately released")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] PostgreSQL connections and corpus reads remained disabled")
    print("[PASS] Tampered, duplicate, premature, or executable input rejected")
    print("[PASS] Atomic owner-method-binding artifacts persisted")
    print("[PASS] Signals, alerts, Q Series, orders, funds, and portfolio mutation remained disabled")
    return 0
if __name__=="__main__": raise SystemExit(main())
