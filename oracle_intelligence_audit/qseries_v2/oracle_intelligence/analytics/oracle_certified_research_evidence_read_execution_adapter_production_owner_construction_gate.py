from __future__ import annotations
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
