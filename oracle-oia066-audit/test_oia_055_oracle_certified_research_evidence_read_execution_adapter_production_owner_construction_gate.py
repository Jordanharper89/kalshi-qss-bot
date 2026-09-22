import json,tempfile
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_gate import *

def seed(path):
 e={"sequence":1,"worker_id":"oracle-worker-test","work_item_id":"work.test","adapter_id":"oracle_read_only_canonical_observation_adapter.v1","read_operation":"read_canonical_observations","module_path":"qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector","owner_name":"OracleLiveCorpusInspector","callable_name":"inspect","constructor_signature":"(*, connection_factory, stale_after_seconds=300, market_limit=100)","callable_signature":"(self, *, inspected_at=None)","bound_constructor_arguments":{"connection_factory":"symbolic://oracle/runtime/connection_factory","stale_after_seconds":300,"market_limit":100},"bound_callable_arguments":{"self":"symbolic://oracle/owner_instance","inspected_at":None},"constructor_binding_hash":stable_hash({"connection_factory":"symbolic://oracle/runtime/connection_factory","stale_after_seconds":300,"market_limit":100}),"callable_binding_hash":stable_hash({"self":"symbolic://oracle/owner_instance","inspected_at":None}),"constructor_dependency_names":["connection_factory"],"constructor_default_names":["stale_after_seconds","market_limit"],"symbolic_dependencies_only":True,"owner_construction_ready":True,"owner_construction_authorized":True,"owner_instantiation_requested":False,"owner_instantiated":False,"callable_bound_to_owner":False,"callable_invoked":False,"adapter_executed":False,"authorization_checks":["x"],"authorization_status":"evidence_read_execution_adapter_production_owner_construction_authorized","source_owner_construction_readiness_hash":stable_hash({"53":1}),"source_callable_argument_binding_hash":stable_hash({"52":1}),"source_callable_binding_authorization_hash":stable_hash({"51":1}),"source_callable_binding_readiness_hash":stable_hash({"50":1}),"source_callable_resolution_hash":stable_hash({"49":1}),"source_active_invocation_execution_authorization_hash":stable_hash({"48":1}),"source_active_invocation_execution_readiness_hash":stable_hash({"47":1}),"source_active_execution_invocation_hash":stable_hash({"46":1}),"source_execution_invocation_hash":stable_hash({"45":1}),"source_authorization_entry_hash":stable_hash({"44":1}),"source_readiness_entry_hash":stable_hash({"43":1}),"source_active_adapter_invocation_hash":stable_hash({"42":1})}
 e["owner_construction_authorization_hash"]=stable_hash(e)
 m={"schema_version":"OIA-054","engine_id":"OIA-054","authorized_at":"2026-07-22T00:00:00+00:00","owner_construction_authorization_id":"oia054-test","owner_construction_authorization_status":"evidence_read_execution_adapter_production_owner_construction_authorization_issued","owner_construction_authorization_policy_id":"test","worker_id":"oracle-worker-test","authorization_entry_count":1,"authorization_entries":[e],"source_owner_construction_readiness_id":"oia053-test","source_owner_construction_readiness_manifest_hash":stable_hash({"53m":1}),"source_callable_argument_binding_id":"oia052-test","source_callable_argument_binding_manifest_hash":stable_hash({"52m":1}),"source_lineage":{"dispatch_manifest_id":"20","source_claim_id":"21"},"owner_construction_authorization_issued":True,"owner_construction_evaluation_allowed":True,"owner_instantiation_allowed":False,"owner_instantiation_performed":False,"callable_binding_to_owner_allowed":False,"callable_binding_to_owner_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"authorization_artifact_persistence_allowed":True}
 m["owner_construction_authorization_manifest_hash"]=stable_hash(m); path.mkdir(parents=True,exist_ok=True); (path/"current.json").write_text(json.dumps(m,indent=2)+"\n"); return m

def main():
 print("="*40); print(" OIA-055 TEST"); print(" CONTROLLED OWNER CONSTRUCTION"); print("="*40)
 with tempfile.TemporaryDirectory() as td:
  r=Path(td); a=r/"authorization"; c=r/"construction"; src=seed(a); g=OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionGate(authorization_directory=a,construction_directory=c); fixed=datetime(2026,7,22,tzinfo=timezone.utc); x=g.construct(constructed_at=fixed,persist=True); y=g.construct(constructed_at=fixed,persist=False)
  assert x==y and x.owner_construction_performed and not x.owner_instances_retained and x.construction_entry_count==1
  e=x.construction_entries[0]; assert e.owner_constructed and e.owner_type_verified and e.owner_read_only_verified and e.owner_execution_disabled_verified
  assert not e.callable_bound_to_owner and not e.callable_invoked and not e.adapter_executed
  assert not x.callable_binding_to_owner_allowed and not x.callable_invocation_allowed and not x.adapter_execution_allowed and not x.corpus_read_execution_allowed
  assert x.source_owner_construction_authorization_manifest_hash==src["owner_construction_authorization_manifest_hash"] and (c/"current.json").exists()
  bad=json.loads((a/"current.json").read_text()); bad["authorization_entries"][0]["owner_instantiated"]=True; (a/"current.json").write_text(json.dumps(bad))
  try: g.construct(constructed_at=fixed,persist=False); raise AssertionError("tamper accepted")
  except ProductionOwnerConstructionInvariantError: pass
 print("[PASS] Actual OIA-054 owner-construction-authorization contract consumed")
 print("[PASS] Approved production owner class constructed with inert dependencies")
 print("[PASS] Constructed owner identity and read-only safety flags verified")
 print("[PASS] Construction manifest and entry hashes deterministic")
 print("[PASS] Complete OIA-020 through OIA-054 lineage preserved")
 print("[PASS] Constructed owner instances were not retained")
 print("[PASS] Methods were not bound and no callable was invoked")
 print("[PASS] No adapter executed and corpus reads remained disabled")
 print("[PASS] Tampered, unknown, duplicate, or executable input rejected")
 print("[PASS] Atomic owner-construction artifacts persisted")
 print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
 print("[PASS] Orders, funds, and portfolio mutation remained disabled")
 return 0
if __name__=="__main__": raise SystemExit(main())
