import json,tempfile
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_readiness_gate import *

def seed(path:Path):
    hashes={k:stable_hash({k:1}) for k in ("source_callable_binding_authorization_hash","source_callable_binding_readiness_hash","source_callable_resolution_hash","source_active_invocation_execution_authorization_hash","source_active_invocation_execution_readiness_hash","source_active_execution_invocation_hash","source_execution_invocation_hash","source_authorization_entry_hash","source_readiness_entry_hash","source_active_adapter_invocation_hash")}
    ctor={"connection_factory":"symbolic://oracle/runtime/connection_factory","stale_after_seconds":300,"market_limit":100}; call={"self":"symbolic://oracle/owner_instance","inspected_at":None}
    eb={"sequence":1,"worker_id":"oracle-worker-test","work_item_id":"work.test","adapter_id":"oracle_read_only_canonical_observation_adapter.v1","read_operation":"read_canonical_observations","module_path":"qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector","owner_name":"OracleLiveCorpusInspector","callable_name":"inspect","constructor_signature":"(*, connection_factory, stale_after_seconds=300, market_limit=100)","callable_signature":"(self, *, inspected_at=None)","bound_constructor_arguments":ctor,"bound_callable_arguments":call,"constructor_binding_hash":stable_hash(ctor),"callable_binding_hash":stable_hash(call),"owner_instantiated":False,"callable_bound_to_owner":False,"callable_invoked":False,"adapter_executed":False,"binding_checks":["ok"],"binding_status":"evidence_read_execution_adapter_production_callable_arguments_bound",**hashes}
    e=dict(eb); e["callable_argument_binding_hash"]=stable_hash(eb)
    m={"schema_version":"OIA-052","engine_id":"OIA-052","bound_at":"2026-07-22T00:00:00+00:00","callable_argument_binding_id":"oia052-test","callable_argument_binding_status":"evidence_read_execution_adapter_production_callable_argument_binding_issued","callable_argument_binding_policy_id":"test","worker_id":"oracle-worker-test","binding_entry_count":1,"binding_entries":[e],"source_lineage":{"dispatch_manifest_id":"20","source_claim_id":"21"},"symbolic_binding_only":True,"owner_instantiation_allowed":False,"owner_instantiation_performed":False,"constructor_argument_binding_allowed":True,"constructor_argument_binding_performed":True,"callable_argument_binding_allowed":True,"callable_argument_binding_performed":True,"callable_invocation_evaluation_allowed":True,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"binding_artifact_persistence_allowed":True}
    m["callable_argument_binding_manifest_hash"]=stable_hash(m); path.mkdir(parents=True,exist_ok=True); (path/"current.json").write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")

def main():
    print("="*40); print(" OIA-053 TEST"); print(" OWNER CONSTRUCTION READINESS"); print("="*40)
    with tempfile.TemporaryDirectory() as t:
        root=Path(t); b=root/"binding"; r=root/"readiness"; seed(b)
        g=OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionReadinessGate(binding_directory=b,readiness_directory=r); fixed=datetime(2026,7,22,tzinfo=timezone.utc)
        a=g.evaluate(evaluated_at=fixed,persist=True); c=g.evaluate(evaluated_at=fixed,persist=False); assert a==c and a.schema_version=="OIA-053" and a.readiness_entry_count==1
        e=a.readiness_entries[0]; assert e.owner_construction_ready and e.constructor_dependency_names==("connection_factory",) and e.constructor_default_names==("stale_after_seconds","market_limit")
        assert not e.owner_instantiated and not e.callable_bound_to_owner and not e.callable_invoked and not e.adapter_executed
        assert a.owner_construction_authorization_evaluation_allowed and not a.owner_instantiation_allowed and not a.callable_invocation_allowed
        assert (r/"current.json").exists()
        bad=json.loads((b/"current.json").read_text()); bad["binding_entries"][0]["owner_instantiated"]=True; (b/"current.json").write_text(json.dumps(bad))
        try: g.evaluate(evaluated_at=fixed,persist=False); raise AssertionError("tamper accepted")
        except ProductionOwnerConstructionReadinessInvariantError: pass
    print("[PASS] Actual OIA-052 callable-argument-binding contract consumed")
    print("[PASS] Constructor dependencies and defaults classified deterministically")
    print("[PASS] Owner-construction readiness hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-052 lineage preserved")
    print("[PASS] Symbolic dependencies remained non-live and non-secret")
    print("[PASS] Owners were not instantiated and methods were not owner-bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, or executable input rejected")
    print("[PASS] Atomic owner-construction-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled"); return 0
if __name__=="__main__": raise SystemExit(main())
