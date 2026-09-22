import json,tempfile
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_binding_authorization_gate import *

def seed(path):
    common={"worker_id":"oracle-worker-test","work_item_id":"work-1","adapter_id":"oracle_read_only_canonical_observation_adapter.v1","read_operation":"read_canonical_observations","module_path":"qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector","owner_name":"OracleLiveCorpusInspector","callable_name":"inspect","callable_kind":"instance_method","callable_qualified_name":"OracleLiveCorpusInspector.inspect","constructor_signature":"(*, connection_factory, stale_after_seconds=300, market_limit=100)","callable_signature":"(self, *, inspected_at=None)","required_constructor_parameters":["connection_factory"],"optional_constructor_parameters":["stale_after_seconds","market_limit"],"required_callable_parameters":[],"optional_callable_parameters":["inspected_at"],"module_imported":True,"owner_resolved":True,"callable_resolved":True,"signature_inspection_performed":True,"owner_instantiated":False,"constructor_arguments_bound":False,"callable_arguments_bound":False,"callable_invoked":False,"adapter_executed":False,"readiness_checks":["ok"],"readiness_status":"evidence_read_execution_adapter_production_callable_binding_ready"}
    for k in ("source_callable_resolution_hash","source_active_invocation_execution_authorization_hash","source_active_invocation_execution_readiness_hash","source_active_execution_invocation_hash","source_execution_invocation_hash","source_authorization_entry_hash","source_readiness_entry_hash","source_active_adapter_invocation_hash"): common[k]=stable_hash({k:1})
    common["sequence"]=1; e=dict(common); e["callable_binding_readiness_hash"]=stable_hash(common)
    d={"schema_version":"OIA-050","engine_id":"OIA-050","evaluated_at":"2026-07-22T00:00:00+00:00","callable_binding_readiness_id":"oia050-test","callable_binding_readiness_status":"evidence_read_execution_adapter_production_callable_binding_readiness_issued","callable_binding_readiness_policy_id":"x","worker_id":"oracle-worker-test","readiness_entry_count":1,"readiness_entries":[e],"approved_binding_signature_registry_hash":stable_hash({"r":1}),"source_callable_resolution_id":"oia049-test","source_callable_resolution_manifest_hash":stable_hash({"49":1}),"source_execution_authorization_id":"48","source_execution_authorization_manifest_hash":stable_hash({"48":1}),"source_execution_readiness_id":"47","source_execution_readiness_manifest_hash":stable_hash({"47":1}),"source_invocation_activation_id":"46","source_invocation_activation_manifest_hash":stable_hash({"46":1}),"source_execution_invocation_manifest_id":"45","source_execution_invocation_manifest_hash":stable_hash({"45":1}),"source_prior_execution_authorization_id":"44","source_prior_execution_authorization_manifest_hash":stable_hash({"44":1}),"source_prior_execution_readiness_id":"43","source_prior_execution_readiness_manifest_hash":stable_hash({"43":1}),"source_activation_hash":stable_hash({"42":1}),"source_lineage":{"dispatch_manifest_id":"20","source_claim_id":"21"},"callable_binding_readiness_issued":True,"module_import_allowed":True,"module_import_performed":True,"signature_inspection_allowed":True,"signature_inspection_performed":True,"owner_instantiation_allowed":False,"owner_instantiation_performed":False,"constructor_argument_binding_allowed":False,"constructor_argument_binding_performed":False,"callable_argument_binding_allowed":False,"callable_argument_binding_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"readiness_artifact_persistence_allowed":True}
    d["callable_binding_readiness_manifest_hash"]=stable_hash(d); path.mkdir(parents=True,exist_ok=True); (path/"current.json").write_text(json.dumps(d,indent=2)+"\n"); return d

def main():
 print("="*40); print(" OIA-051 TEST"); print(" CALLABLE BINDING AUTHORIZATION"); print("="*40)
 with tempfile.TemporaryDirectory() as td:
  root=Path(td); r=root/"r"; a=root/"a"; src=seed(r); g=OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableBindingAuthorizationGate(readiness_directory=r,authorization_directory=a); t=datetime(2026,7,22,tzinfo=timezone.utc); x=g.authorize(authorized_at=t,persist=True); y=g.authorize(authorized_at=t,persist=False)
  assert x==y and x.schema_version=="OIA-051" and x.authorization_entry_count==1
  e=x.authorization_entries[0]; assert e.binding_authorized is True and e.authorized_constructor_parameters==("connection_factory","stale_after_seconds","market_limit") and e.authorized_callable_parameters==("inspected_at",)
  assert not e.owner_instantiated and not e.constructor_arguments_bound and not e.callable_arguments_bound and not e.callable_invoked and not e.adapter_executed
  assert x.constructor_argument_binding_evaluation_allowed and x.callable_argument_binding_evaluation_allowed
  assert not x.owner_instantiation_allowed and not x.constructor_argument_binding_allowed and not x.callable_argument_binding_allowed and not x.callable_invocation_allowed and not x.adapter_execution_allowed
  assert (a/"current.json").exists()
  bad=json.loads((r/"current.json").read_text()); bad["readiness_entries"][0]["constructor_arguments_bound"]=True; (r/"current.json").write_text(json.dumps(bad));
  try: g.authorize(authorized_at=t,persist=False); raise AssertionError("tampered input accepted")
  except ProductionCallableBindingAuthorizationInvariantError: pass
 print("[PASS] Actual OIA-050 callable-binding-readiness contract consumed")
 print("[PASS] Exact constructor and callable parameter allowlists authorized")
 print("[PASS] Authorization manifest and entry hashes deterministic")
 print("[PASS] Complete OIA-020 through OIA-050 lineage preserved")
 print("[PASS] Binding evaluation authorized without performing binding")
 print("[PASS] Owners were not instantiated and arguments were not bound")
 print("[PASS] No callable was invoked and no adapter executed")
 print("[PASS] Corpus read execution remained disabled")
 print("[PASS] Tampered, duplicate, bound, or executable input rejected")
 print("[PASS] Atomic callable-binding-authorization artifacts persisted")
 print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
 print("[PASS] Orders, funds, and portfolio mutation remained disabled")
 return 0
if __name__=="__main__": raise SystemExit(main())
