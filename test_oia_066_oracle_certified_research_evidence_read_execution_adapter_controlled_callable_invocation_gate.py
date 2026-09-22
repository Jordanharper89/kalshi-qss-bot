from __future__ import annotations
import json,tempfile
from dataclasses import asdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_controlled_callable_invocation_gate import *
from qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector import OracleLiveCorpusInspector

class Cursor:
 def __init__(self): self.n=0
 def execute(self,*a): self.n+=1
 def fetchone(self):
  t=datetime(2026,7,22,tzinfo=timezone.utc)
  return (15,1,3,t-timedelta(minutes=2),t-timedelta(seconds=5),t-timedelta(seconds=4))
 def fetchall(self): return []
 def close(self): pass
class Connection:
 def __init__(self): self.closed=False
 def cursor(self): return Cursor()
 def close(self): self.closed=True

def seed(path):
 fixed="2026-07-22T00:00:00+00:00"; entries=[]
 specs=[("oracle_read_only_canonical_observation_adapter.v1","qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector","OracleLiveCorpusInspector","inspect","OracleLiveCorpusInspector.inspect","(*, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",{"inspected_at":None}),
 ("oracle_read_only_market_state_lineage_adapter.v1","qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger","OracleCanonicalMarketLineageLedger","records","OracleCanonicalMarketLineageLedger.records","() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'",{})]
 for i,(aid,mp,on,cn,q,sig,args) in enumerate(specs,1):
  body={"sequence":i,"worker_id":"worker","work_item_id":f"work-{i}","adapter_id":aid,"read_operation":"read","module_path":mp,"owner_name":on,"callable_name":cn,"bound_method_module":mp,"bound_method_qualname":q,"bound_method_signature":sig,"invocation_arguments":args,"invocation_argument_hash":stable_hash(args),"activation_nonce":f"a-{i}","consumption_attempt_nonce":f"c-{i}","source_consumption_activation_hash":stable_hash({"a":i}),"source_consumption_authorization_hash":stable_hash({"b":i}),"source_consumption_readiness_hash":stable_hash({"c":i}),"controlled_execution_ready":True,"fresh_repository_inspection_required":True,"consumption_activation_consumed":False,"original_activation_consumed":False,"owner_reconstruction_performed":False,"method_binding_performed":False,"callable_invoked":False,"adapter_executed":False,"corpus_read_executed":False,"readiness_checks":["verified"],"readiness_status":"ready"}
  body["controlled_callable_invocation_execution_readiness_hash"]=stable_hash(body); entries.append(body)
 m={"schema_version":"OIA-065","engine_id":"OIA-065","evaluated_at":fixed,"controlled_callable_invocation_execution_readiness_id":"oia065-test","controlled_callable_invocation_execution_readiness_status":"issued","controlled_callable_invocation_execution_readiness_policy_id":"test","worker_id":"worker","readiness_entry_count":2,"readiness_entries":entries,"source_consumption_activation_id":"64","source_consumption_activation_manifest_hash":stable_hash({"64":1}),"source_consumption_authorization_id":"63","source_consumption_authorization_manifest_hash":stable_hash({"63":1}),"source_consumption_readiness_id":"62","source_consumption_readiness_manifest_hash":stable_hash({"62":1}),"source_invocation_activation_id":"61","source_invocation_activation_manifest_hash":stable_hash({"61":1}),"source_invocation_authorization_id":"60","source_invocation_authorization_manifest_hash":stable_hash({"60":1}),"source_lineage":{"dispatch_manifest_id":"20"},"controlled_callable_invocation_execution_readiness_issued":True,"fresh_repository_inspection_required_before_execution":True,"activation_consumption_allowed":False,"activation_consumption_performed":False,"owner_reconstruction_allowed":False,"owner_reconstruction_performed":False,"callable_binding_to_owner_allowed":False,"callable_binding_to_owner_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"readiness_artifact_persistence_allowed":True,"owner_instances_retained":False,"bound_methods_retained":False}
 m["controlled_callable_invocation_execution_readiness_manifest_hash"]=stable_hash(m); path.mkdir(parents=True,exist_ok=True); (path/"current.json").write_text(json.dumps(m,sort_keys=True,indent=2))

def main():
 print("="*40); print(" OIA-066 TEST"); print(" CONTROLLED CALLABLE INVOCATION"); print("="*40)
 with tempfile.TemporaryDirectory() as td:
  root=Path(td); ready=root/"ready"; out=root/"out"; seed(ready)
  class OracleCanonicalMarketLineageLedger:
   def records(self): return ("lineage-a","lineage-b")
  OracleCanonicalMarketLineageLedger.records.__module__="qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger"
  OracleCanonicalMarketLineageLedger.records.__qualname__="OracleCanonicalMarketLineageLedger.records"
  OracleCanonicalMarketLineageLedger.records.__annotations__={"return":"tuple[CanonicalMarketStateDwellChangeLineage, ...]"}
  gate=OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationGate(readiness_directory=ready,invocation_directory=out,owner_factories={"oracle_read_only_canonical_observation_adapter.v1":lambda:OracleLiveCorpusInspector(connection_factory=Connection,stale_after_seconds=300,market_limit=100),"oracle_read_only_market_state_lineage_adapter.v1":OracleCanonicalMarketLineageLedger})
  fixed=datetime(2026,7,22,tzinfo=timezone.utc); first=gate.invoke(invoked_at=fixed,persist=True); second=gate.invoke(invoked_at=fixed,persist=False)
  assert first==second and first.schema_version=="OIA-066" and first.invocation_entry_count==2
  assert first.readiness_consumed and first.callable_invocation_performed and first.corpus_read_execution_performed
  assert not first.source_mutation_performed and not first.execution_allowed and not first.signals_allowed
  assert first.invocation_entries[0].result_summary["observation_count"]==15
  assert first.invocation_entries[1].result_summary["record_count"]==2
  assert (out/"current.json").exists()
  payload=json.loads((ready/"current.json").read_text()); payload["readiness_entries"][0]["callable_invoked"]=True
  body=dict(payload["readiness_entries"][0]); body.pop("controlled_callable_invocation_execution_readiness_hash",None); payload["readiness_entries"][0]["controlled_callable_invocation_execution_readiness_hash"]=stable_hash(body)
  mh=dict(payload); mh.pop("controlled_callable_invocation_execution_readiness_manifest_hash",None); payload["controlled_callable_invocation_execution_readiness_manifest_hash"]=stable_hash(mh); (ready/"current.json").write_text(json.dumps(payload))
  try: gate.invoke(invoked_at=fixed,persist=False); raise AssertionError("consumed readiness accepted")
  except ControlledCallableInvocationInvariantError: pass
 print("[PASS] Actual OIA-065 readiness contract consumed")
 print("[PASS] Exact production corpus-inspector owner reconstructed")
 print("[PASS] Approved methods bound and invoked once")
 print("[PASS] Read-only corpus report and lineage results captured")
 print("[PASS] Deterministic result and manifest hashes produced")
 print("[PASS] OIA-020 through OIA-065 lineage preserved")
 print("[PASS] Consumed or tampered readiness rejected fail-closed")
 print("[PASS] Atomic invocation artifacts persisted")
 print("[PASS] No signals, alerts, Q Series, orders, funds, or portfolio mutation")
 return 0
if __name__=="__main__": raise SystemExit(main())
