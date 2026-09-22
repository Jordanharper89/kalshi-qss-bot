from __future__ import annotations

import hashlib, importlib, inspect, json, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

SCHEMA_VERSION="OIA-066"; ENGINE_ID="OIA-066"
POLICY_ID="oracle.certified-research-evidence-read-execution-adapter-controlled-callable-invocation.v1"
STATUS_INVOKED="evidence_read_execution_adapter_controlled_callable_invoked"
STATUS_ISSUED="evidence_read_execution_adapter_controlled_callable_invocation_issued"
DEFAULT_READINESS_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_controlled_callable_invocation_execution_readiness")
DEFAULT_INVOCATION_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_controlled_callable_invocation")
APPROVED={
 "oracle_read_only_canonical_observation_adapter.v1":{
  "module_path":"qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector","owner_name":"OracleLiveCorpusInspector","callable_name":"inspect",
  "bound_method_qualname":"OracleLiveCorpusInspector.inspect","bound_method_signature":"(*, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'"},
 "oracle_read_only_market_state_lineage_adapter.v1":{
  "module_path":"qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger","owner_name":"OracleCanonicalMarketLineageLedger","callable_name":"records",
  "bound_method_qualname":"OracleCanonicalMarketLineageLedger.records","bound_method_signature":"() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'"},
}
class ControlledCallableInvocationInvariantError(RuntimeError): pass

def _canonical(v:Any)->Any:
 if is_dataclass(v): return _canonical(asdict(v))
 if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)): return [_canonical(x) for x in v]
 if isinstance(v,datetime):
  if v.tzinfo is None or v.utcoffset() is None: raise ControlledCallableInvocationInvariantError("datetime must be timezone-aware")
  return v.astimezone(timezone.utc).isoformat()
 return v

def stable_hash(v:Any)->str: return hashlib.sha256(json.dumps(_canonical(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def _valid_hash(v): return isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v)
def _aware(v,name):
 if not isinstance(v,datetime) or v.tzinfo is None or v.utcoffset() is None: raise ControlledCallableInvocationInvariantError(f"{name} must be timezone-aware")
 return v.astimezone(timezone.utc)
def _atomic(path,payload):
 path.parent.mkdir(parents=True,exist_ok=True); rendered=json.dumps(_canonical(payload),sort_keys=True,indent=2,ensure_ascii=False)+"\n"
 h=tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",newline="\n",delete=False,dir=str(path.parent),prefix=f".{path.name}.",suffix=".tmp"); tmp=Path(h.name)
 try:
  with h: h.write(rendered); h.flush(); os.fsync(h.fileno())
  os.replace(tmp,path)
 finally:
  if tmp.exists(): tmp.unlink()

@dataclass(frozen=True)
class ControlledCallableInvocationEntry:
 sequence:int; worker_id:str; work_item_id:str; adapter_id:str; module_path:str; owner_name:str; callable_name:str; activation_nonce:str; consumption_attempt_nonce:str
 source_readiness_hash:str; invocation_argument_hash:str; invocation_arguments:dict[str,Any]; owner_reconstructed:bool; method_bound_to_owner:bool; callable_invoked:bool; adapter_executed:bool; corpus_read_executed:bool
 result_type:str; result_hash:str; result_summary:dict[str,Any]; source_mutation_performed:bool; invocation_status:str; controlled_callable_invocation_hash:str
@dataclass(frozen=True)
class ControlledCallableInvocationManifest:
 schema_version:str; engine_id:str; invoked_at:str; controlled_callable_invocation_id:str; controlled_callable_invocation_status:str; controlled_callable_invocation_policy_id:str; worker_id:str
 invocation_entry_count:int; invocation_entries:tuple[ControlledCallableInvocationEntry,...]; source_readiness_id:str; source_readiness_manifest_hash:str; source_lineage:dict[str,Any]
 readiness_consumed:bool; owner_reconstruction_performed:bool; callable_binding_to_owner_performed:bool; callable_invocation_performed:bool; adapter_execution_performed:bool; corpus_read_execution_performed:bool
 research_execution_allowed:bool; analytic_conclusion_allowed:bool; forecast_creation_allowed:bool; signals_allowed:bool; alerts_allowed:bool; qseries_handoff_allowed:bool; execution_allowed:bool
 trading_recommendations_allowed:bool; source_mutation_allowed:bool; source_mutation_performed:bool; market_order_creation_allowed:bool; funds_movement_allowed:bool; portfolio_mutation_allowed:bool
 invocation_artifact_persistence_allowed:bool; owner_instances_retained:bool; bound_methods_retained:bool; controlled_callable_invocation_manifest_hash:str

class OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationGate:
 def __init__(self,*,readiness_directory:Path|str=DEFAULT_READINESS_DIRECTORY,invocation_directory:Path|str=DEFAULT_INVOCATION_DIRECTORY,owner_factories:Mapping[str,Callable[[],Any]]|None=None):
  self.readiness_directory=Path(readiness_directory); self.invocation_directory=Path(invocation_directory); self.owner_factories=dict(owner_factories or {})
 def _load(self):
  p=self.readiness_directory/"current.json"
  if not p.exists(): raise ControlledCallableInvocationInvariantError(f"OIA-065 current readiness artifact missing: {p}")
  try: src=json.loads(p.read_text(encoding="utf-8"))
  except Exception as e: raise ControlledCallableInvocationInvariantError("OIA-065 readiness artifact could not be decoded") from e
  digest=src.pop("controlled_callable_invocation_execution_readiness_manifest_hash",None)
  if not _valid_hash(digest) or stable_hash(src)!=digest: raise ControlledCallableInvocationInvariantError("OIA-065 readiness manifest hash mismatch")
  src["controlled_callable_invocation_execution_readiness_manifest_hash"]=digest
  required={"controlled_callable_invocation_execution_readiness_issued":True,"fresh_repository_inspection_required_before_execution":True,"activation_consumption_performed":False,"owner_reconstruction_performed":False,"callable_binding_to_owner_performed":False,"callable_invocation_performed":False,"adapter_execution_performed":False,"corpus_read_execution_performed":False,"execution_allowed":False,"source_mutation_allowed":False}
  for k,v in required.items():
   if src.get(k)!=v: raise ControlledCallableInvocationInvariantError(f"unsafe or invalid OIA-065 flag: {k}")
  if src.get("readiness_entry_count")!=len(src.get("readiness_entries",[])) or not src.get("readiness_entries"): raise ControlledCallableInvocationInvariantError("OIA-065 readiness entries invalid")
  seen=set()
  for entry in src["readiness_entries"]:
   h=entry.pop("controlled_callable_invocation_execution_readiness_hash",None)
   if not _valid_hash(h) or stable_hash(entry)!=h: raise ControlledCallableInvocationInvariantError("OIA-065 readiness entry hash mismatch")
   entry["controlled_callable_invocation_execution_readiness_hash"]=h
   approved=APPROVED.get(entry.get("adapter_id"))
   if approved is None: raise ControlledCallableInvocationInvariantError("unapproved adapter")
   for f in ("module_path","owner_name","callable_name","bound_method_qualname","bound_method_signature"):
    if entry.get(f)!=approved[f]: raise ControlledCallableInvocationInvariantError(f"approved callable mismatch: {f}")
   if not entry.get("controlled_execution_ready") or not entry.get("fresh_repository_inspection_required"): raise ControlledCallableInvocationInvariantError("entry not ready")
   if any(entry.get(f) for f in ("consumption_activation_consumed","original_activation_consumed","owner_reconstruction_performed","method_binding_performed","callable_invoked","adapter_executed","corpus_read_executed")): raise ControlledCallableInvocationInvariantError("readiness entry already consumed or executed")
   key=(entry["activation_nonce"],entry["consumption_attempt_nonce"])
   if key in seen: raise ControlledCallableInvocationInvariantError("duplicate nonce pair")
   seen.add(key)
  return src
 def _owner(self,entry):
  factory=self.owner_factories.get(entry["adapter_id"])
  if factory is not None: owner=factory()
  else:
   module=importlib.import_module(entry["module_path"]); owner_type=getattr(module,entry["owner_name"],None)
   if not inspect.isclass(owner_type): raise ControlledCallableInvocationInvariantError("approved owner class unavailable")
   if entry["adapter_id"]=="oracle_read_only_canonical_observation_adapter.v1":
    resolve=getattr(module,"resolve_database_url"); connect=getattr(module,"connect_postgresql"); url=resolve()
    owner=owner_type(connection_factory=lambda:connect(url),stale_after_seconds=300,market_limit=100)
   else: owner=owner_type()
  if owner.__class__.__name__!=entry["owner_name"]: raise ControlledCallableInvocationInvariantError("owner identity mismatch")
  return owner
 def invoke(self,*,invoked_at:datetime,persist:bool=True):
  invoked_at=_aware(invoked_at,"invoked_at"); src=self._load(); results=[]
  for sequence,entry in enumerate(src["readiness_entries"],1):
   try:
    owner=self._owner(entry); method=getattr(owner,entry["callable_name"],None)
    if method is None or not callable(method): raise ControlledCallableInvocationInvariantError("approved method did not bind")
    function=getattr(method,"__func__",method)
    if getattr(function,"__module__",None)!=entry["module_path"] or getattr(function,"__qualname__",None)!=entry["bound_method_qualname"]: raise ControlledCallableInvocationInvariantError("bound method identity mismatch")
    if str(inspect.signature(method))!=entry["bound_method_signature"]: raise ControlledCallableInvocationInvariantError("bound method signature mismatch")
    certified_args=dict(entry["invocation_arguments"])
    if stable_hash(certified_args)!=entry["invocation_argument_hash"]: raise ControlledCallableInvocationInvariantError("invocation argument hash mismatch")
    args=dict(certified_args)
    if entry["adapter_id"]=="oracle_read_only_canonical_observation_adapter.v1" and args.get("inspected_at") is None: args["inspected_at"]=invoked_at
    result=method(**args)
    if result is None: raise ControlledCallableInvocationInvariantError("approved callable returned no result")
    canonical=_canonical(result); rh=stable_hash(canonical)
    if entry["adapter_id"]=="oracle_read_only_canonical_observation_adapter.v1":
     if not getattr(result,"read_only",False) or any(getattr(result,k,True) for k in ("execution_allowed","alerts_allowed","qseries_handoff_allowed")): raise ControlledCallableInvocationInvariantError("corpus report violated read-only contract")
     summary={"observation_count":int(result.observation_count),"market_count":int(result.market_count),"source_count":int(result.source_count),"acquisition_batch_count":int(result.acquisition_batch_count),"report_hash":str(result.report_hash)}
    else: summary={"record_count":len(result)}
    body={"sequence":sequence,"worker_id":entry["worker_id"],"work_item_id":entry["work_item_id"],"adapter_id":entry["adapter_id"],"module_path":entry["module_path"],"owner_name":entry["owner_name"],"callable_name":entry["callable_name"],"activation_nonce":entry["activation_nonce"],"consumption_attempt_nonce":entry["consumption_attempt_nonce"],"source_readiness_hash":entry["controlled_callable_invocation_execution_readiness_hash"],"invocation_argument_hash":entry["invocation_argument_hash"],"invocation_arguments":args,"owner_reconstructed":True,"method_bound_to_owner":True,"callable_invoked":True,"adapter_executed":True,"corpus_read_executed":True,"result_type":type(result).__name__,"result_hash":rh,"result_summary":summary,"source_mutation_performed":False,"invocation_status":STATUS_INVOKED}
    results.append(ControlledCallableInvocationEntry(**body,controlled_callable_invocation_hash=stable_hash(body)))
   finally:
    owner=None; method=None; result=None
  source_hash=src["controlled_callable_invocation_execution_readiness_manifest_hash"]
  iid="oia066-controlled-callable-invocation-"+stable_hash({"source":source_hash,"policy":POLICY_ID})[:32]
  body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"invoked_at":invoked_at.isoformat(),"controlled_callable_invocation_id":iid,"controlled_callable_invocation_status":STATUS_ISSUED,"controlled_callable_invocation_policy_id":POLICY_ID,"worker_id":src["worker_id"],"invocation_entry_count":len(results),"invocation_entries":tuple(results),"source_readiness_id":src["controlled_callable_invocation_execution_readiness_id"],"source_readiness_manifest_hash":source_hash,"source_lineage":dict(src["source_lineage"]),"readiness_consumed":True,"owner_reconstruction_performed":True,"callable_binding_to_owner_performed":True,"callable_invocation_performed":True,"adapter_execution_performed":True,"corpus_read_execution_performed":True,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"source_mutation_performed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"invocation_artifact_persistence_allowed":True,"owner_instances_retained":False,"bound_methods_retained":False}
  serial=dict(body); serial["invocation_entries"]=[asdict(x) for x in results]
  manifest=ControlledCallableInvocationManifest(**body,controlled_callable_invocation_manifest_hash=stable_hash(serial))
  if persist:
   payload=asdict(manifest); _atomic(self.invocation_directory/"current.json",payload); _atomic(self.invocation_directory/"invocations"/f"{iid}.json",payload); _atomic(self.invocation_directory/"workers"/manifest.worker_id/f"{iid}.json",payload)
  return manifest
