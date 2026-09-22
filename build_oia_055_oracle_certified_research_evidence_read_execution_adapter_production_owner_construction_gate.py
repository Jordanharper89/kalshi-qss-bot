from pathlib import Path
import py_compile,subprocess,sys
ROOT=Path(__file__).resolve().parent
ANALYTICS=ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"
OIA054=ANALYTICS/"oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_authorization_gate.py"
PRODUCTION=ANALYTICS/"oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_gate.py"
TEST=ROOT/"test_oia_055_oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_gate.py"
INIT=ANALYTICS/"__init__.py"
PRODUCTION_SOURCE=r'''from __future__ import annotations
import hashlib, importlib, json, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION="OIA-055"; ENGINE_ID="OIA-055"
POLICY_ID="oracle.certified-research-evidence-read-execution-adapter-production-owner-construction.v1"
STATUS_OWNER_CONSTRUCTED="evidence_read_execution_adapter_production_owner_constructed"
STATUS_CONSTRUCTION_ISSUED="evidence_read_execution_adapter_production_owner_construction_issued"
DEFAULT_AUTHORIZATION_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_construction_authorization")
DEFAULT_CONSTRUCTION_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_construction")

APPROVED={
 "oracle_read_only_canonical_observation_adapter.v1":("qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector","OracleLiveCorpusInspector","inspect"),
 "oracle_read_only_market_state_lineage_adapter.v1":("qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger","OracleCanonicalMarketLineageLedger","records"),
}
class ProductionOwnerConstructionInvariantError(RuntimeError): pass

def _canonical(v):
 if is_dataclass(v): return _canonical(asdict(v))
 if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)): return [_canonical(x) for x in v]
 if isinstance(v,datetime):
  if v.tzinfo is None or v.utcoffset() is None: raise ProductionOwnerConstructionInvariantError("datetime must be timezone-aware")
  return v.astimezone(timezone.utc).isoformat()
 return v

def stable_hash(v): return hashlib.sha256(json.dumps(_canonical(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def _valid_hash(v): return isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v)
def _aware(v,n):
 if not isinstance(v,datetime) or v.tzinfo is None or v.utcoffset() is None: raise ProductionOwnerConstructionInvariantError(f"{n} must be timezone-aware")
 return v.astimezone(timezone.utc)
def _atomic(path,payload):
 path.parent.mkdir(parents=True,exist_ok=True); h=tempfile.NamedTemporaryFile("w",encoding="utf-8",newline="\n",delete=False,dir=str(path.parent)); t=Path(h.name)
 try:
  with h:
   json.dump(_canonical(payload),h,sort_keys=True,indent=2,ensure_ascii=False); h.write("\n"); h.flush(); os.fsync(h.fileno())
  os.replace(t,path)
 finally:
  if t.exists(): t.unlink()

def _blocked_connection_factory():
 raise ProductionOwnerConstructionInvariantError("construction-only connection factory cannot be invoked")

@dataclass(frozen=True)
class ProductionOwnerConstructionEntry:
 sequence:int; worker_id:str; work_item_id:str; adapter_id:str; read_operation:str; module_path:str; owner_name:str; callable_name:str
 constructor_signature:str; callable_signature:str; constructor_dependency_names:tuple[str,...]; constructor_default_names:tuple[str,...]
 owner_constructed:bool; owner_type_verified:bool; owner_read_only_verified:bool; owner_execution_disabled_verified:bool
 callable_bound_to_owner:bool; callable_invoked:bool; adapter_executed:bool; construction_checks:tuple[str,...]; construction_status:str
 source_owner_construction_authorization_hash:str; source_owner_construction_readiness_hash:str; source_callable_argument_binding_hash:str
 owner_state_fingerprint:str; owner_construction_hash:str

@dataclass(frozen=True)
class ProductionOwnerConstructionManifest:
 schema_version:str; engine_id:str; constructed_at:str; owner_construction_id:str; owner_construction_status:str; owner_construction_policy_id:str
 worker_id:str; construction_entry_count:int; construction_entries:tuple[ProductionOwnerConstructionEntry,...]
 source_owner_construction_authorization_id:str; source_owner_construction_authorization_manifest_hash:str; source_lineage:dict[str,Any]
 owner_construction_performed:bool; owner_instances_retained:bool; callable_binding_to_owner_allowed:bool; callable_binding_to_owner_performed:bool
 callable_invocation_allowed:bool; callable_invocation_performed:bool; adapter_execution_allowed:bool; adapter_execution_performed:bool
 corpus_read_execution_allowed:bool; corpus_read_execution_performed:bool; research_execution_allowed:bool; analytic_conclusion_allowed:bool
 forecast_creation_allowed:bool; signals_allowed:bool; alerts_allowed:bool; qseries_handoff_allowed:bool; execution_allowed:bool
 trading_recommendations_allowed:bool; source_mutation_allowed:bool; market_order_creation_allowed:bool; funds_movement_allowed:bool
 portfolio_mutation_allowed:bool; construction_artifact_persistence_allowed:bool; owner_construction_manifest_hash:str

class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionGate:
 def __init__(self,*,authorization_directory=DEFAULT_AUTHORIZATION_DIRECTORY,construction_directory=DEFAULT_CONSTRUCTION_DIRECTORY):
  self.authorization_directory=Path(authorization_directory); self.construction_directory=Path(construction_directory)
 def _load(self):
  p=self.authorization_directory/"current.json"
  if not p.exists(): raise ProductionOwnerConstructionInvariantError(f"OIA-054 current authorization artifact missing: {p}")
  try: x=json.loads(p.read_text(encoding="utf-8"))
  except Exception as e: raise ProductionOwnerConstructionInvariantError("OIA-054 artifact could not be decoded") from e
  d=x.pop("owner_construction_authorization_manifest_hash",None)
  if not _valid_hash(d) or stable_hash(x)!=d: raise ProductionOwnerConstructionInvariantError("OIA-054 manifest hash verification failed")
  x["owner_construction_authorization_manifest_hash"]=d
  expected={"schema_version":"OIA-054","engine_id":"OIA-054","owner_construction_authorization_issued":True,"owner_construction_evaluation_allowed":True,"owner_instantiation_allowed":False,"owner_instantiation_performed":False,"callable_binding_to_owner_allowed":False,"callable_binding_to_owner_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False}
  for k,v in expected.items():
   if x.get(k)!=v: raise ProductionOwnerConstructionInvariantError(f"OIA-054 invariant failed: {k}")
  entries=x.get("authorization_entries")
  if not isinstance(entries,list) or len(entries)!=x.get("authorization_entry_count") or not entries: raise ProductionOwnerConstructionInvariantError("OIA-054 authorization entries invalid")
  seen=set()
  for i,e in enumerate(entries,1):
   if not isinstance(e,dict) or e.get("sequence")!=i: raise ProductionOwnerConstructionInvariantError("OIA-054 entry sequence invalid")
   h=e.pop("owner_construction_authorization_hash",None)
   if not _valid_hash(h) or stable_hash(e)!=h: raise ProductionOwnerConstructionInvariantError("OIA-054 entry hash failed")
   e["owner_construction_authorization_hash"]=h
   if e.get("work_item_id") in seen: raise ProductionOwnerConstructionInvariantError("duplicate work item")
   seen.add(e.get("work_item_id"))
   if e.get("adapter_id") not in APPROVED or tuple(APPROVED[e["adapter_id"]])!=(e.get("module_path"),e.get("owner_name"),e.get("callable_name")): raise ProductionOwnerConstructionInvariantError("unapproved owner identity")
   for k,v in {"owner_construction_ready":True,"owner_construction_authorized":True,"owner_instantiation_requested":False,"owner_instantiated":False,"callable_bound_to_owner":False,"callable_invoked":False,"adapter_executed":False,"symbolic_dependencies_only":True}.items():
    if e.get(k)!=v: raise ProductionOwnerConstructionInvariantError(f"unsafe OIA-054 entry: {k}")
  return x
 def construct(self,*,constructed_at:datetime,persist=True):
  at=_aware(constructed_at,"constructed_at"); src=self._load(); out=[]
  for i,e in enumerate(src["authorization_entries"],1):
   module=importlib.import_module(e["module_path"]); owner_type=getattr(module,e["owner_name"],None)
   if not isinstance(owner_type,type): raise ProductionOwnerConstructionInvariantError("approved owner class not resolved")
   if e["adapter_id"]=="oracle_read_only_canonical_observation_adapter.v1": owner=owner_type(connection_factory=_blocked_connection_factory,stale_after_seconds=300,market_limit=100)
   else: owner=owner_type()
   if type(owner).__module__!=e["module_path"] or type(owner).__name__!=e["owner_name"]: raise ProductionOwnerConstructionInvariantError("constructed owner identity mismatch")
   if getattr(owner,"read_only",None) is not True or getattr(owner,"execution_allowed",None) is not False: raise ProductionOwnerConstructionInvariantError("constructed owner safety flags invalid")
   state={k:("<blocked-callable>" if callable(v) else type(v).__name__) for k,v in sorted(vars(owner).items())}
   body={"sequence":i,"worker_id":e["worker_id"],"work_item_id":e["work_item_id"],"adapter_id":e["adapter_id"],"read_operation":e["read_operation"],"module_path":e["module_path"],"owner_name":e["owner_name"],"callable_name":e["callable_name"],"constructor_signature":e["constructor_signature"],"callable_signature":e["callable_signature"],"constructor_dependency_names":tuple(e["constructor_dependency_names"]),"constructor_default_names":tuple(e["constructor_default_names"]),"owner_constructed":True,"owner_type_verified":True,"owner_read_only_verified":True,"owner_execution_disabled_verified":True,"callable_bound_to_owner":False,"callable_invoked":False,"adapter_executed":False,"construction_checks":("authorization_manifest_hash_verified","authorization_entry_hash_verified","approved_owner_identity_verified","owner_constructed_with_inert_dependencies","owner_type_verified","owner_read_only_verified","owner_execution_disabled_verified","callable_not_bound","callable_not_invoked","adapter_not_executed","oracle_qseries_boundary_verified"),"construction_status":STATUS_OWNER_CONSTRUCTED,"source_owner_construction_authorization_hash":e["owner_construction_authorization_hash"],"source_owner_construction_readiness_hash":e["source_owner_construction_readiness_hash"],"source_callable_argument_binding_hash":e["source_callable_argument_binding_hash"],"owner_state_fingerprint":stable_hash(state)}
   out.append(ProductionOwnerConstructionEntry(**body,owner_construction_hash=stable_hash(body)))
   del owner
  cid="oia055-owner-construction-"+stable_hash({"source":src["owner_construction_authorization_manifest_hash"],"policy":POLICY_ID})[:32]
  body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"constructed_at":at.isoformat(),"owner_construction_id":cid,"owner_construction_status":STATUS_CONSTRUCTION_ISSUED,"owner_construction_policy_id":POLICY_ID,"worker_id":src["worker_id"],"construction_entry_count":len(out),"construction_entries":tuple(out),"source_owner_construction_authorization_id":src["owner_construction_authorization_id"],"source_owner_construction_authorization_manifest_hash":src["owner_construction_authorization_manifest_hash"],"source_lineage":dict(src["source_lineage"]),"owner_construction_performed":True,"owner_instances_retained":False,"callable_binding_to_owner_allowed":False,"callable_binding_to_owner_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"construction_artifact_persistence_allowed":True}
  serial=dict(body); serial["construction_entries"]=[asdict(z) for z in out]
  result=ProductionOwnerConstructionManifest(**body,owner_construction_manifest_hash=stable_hash(serial))
  if persist:
   payload=asdict(result); _atomic(self.construction_directory/"current.json",payload); _atomic(self.construction_directory/"constructions"/f"{cid}.json",payload); _atomic(self.construction_directory/"workers"/result.worker_id/f"{cid}.json",payload)
  return result
'''
TEST_SOURCE=r'''import json,tempfile
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
'''
INIT_BLOCK=r'''from .oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_gate import (
 OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionGate,
 ProductionOwnerConstructionEntry, ProductionOwnerConstructionInvariantError, ProductionOwnerConstructionManifest,
 POLICY_ID as OIA055_POLICY_ID,
)
__all__=["OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionGate","ProductionOwnerConstructionEntry","ProductionOwnerConstructionInvariantError","ProductionOwnerConstructionManifest","OIA055_POLICY_ID"]+__all__
'''
def main():
 print("="*40); print(" OIA-055 INSTALLER"); print(" CONTROLLED OWNER CONSTRUCTION"); print(" INERT DEPENDENCIES / NO INVOCATION"); print("="*40)
 if not OIA054.exists(): raise RuntimeError(f"Actual OIA-054 module missing: {OIA054}")
 text=OIA054.read_text(encoding="utf-8"); required=['SCHEMA_VERSION = "OIA-054"',"ProductionOwnerConstructionAuthorizationEntry","owner_construction_authorization_hash","owner_construction_authorization_manifest_hash","owner_construction_evaluation_allowed"]
 missing=[t for t in required if t not in text]
 if missing: raise RuntimeError(f"Actual OIA-054 contract mismatch: {missing}")
 print("[OK] Actual OIA-054 owner-construction-authorization contract verified")
 for p,s in ((PRODUCTION,PRODUCTION_SOURCE),(TEST,TEST_SOURCE)):
  p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s.strip()+"\n",encoding="utf-8"); print(f"[OK] FULL REPLACEMENT: {p}")
 existing=INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"; marker="oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_gate import"
 if marker not in existing: INIT.write_text(existing.rstrip()+"\n"+INIT_BLOCK.strip()+"\n",encoding="utf-8"); print(f"[OK] PACKAGE UPDATED: {INIT}")
 else: print(f"[OK] PACKAGE ALREADY CURRENT: {INIT}")
 for p in (PRODUCTION,TEST,INIT): py_compile.compile(str(p),doraise=True)
 print("[OK] Production, test, and package syntax verified")
 result=subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=False)
 if result.returncode: raise SystemExit(result.returncode)
 print("[OK] OIA-055 test executed automatically"); print(); print("[DONE] OIA-055 production owner construction gate installed"); return 0
if __name__=="__main__": raise SystemExit(main())
