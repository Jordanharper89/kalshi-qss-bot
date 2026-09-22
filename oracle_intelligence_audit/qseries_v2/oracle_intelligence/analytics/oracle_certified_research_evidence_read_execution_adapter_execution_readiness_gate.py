from __future__ import annotations
import hashlib,json,os,tempfile
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from pathlib import Path
SCHEMA_VERSION="OIA-043"; ENGINE_ID="OIA-043"; POLICY_ID="oracle.certified-research-evidence-read-execution-adapter-execution-readiness.v1"; STATUS_READY="evidence_read_execution_adapter_execution_ready"; STATUS_ISSUED="evidence_read_execution_adapter_execution_readiness_issued"
DEFAULT_ACTIVE_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_active_evidence_read_execution_adapter_invocations"); DEFAULT_OUTPUT_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_execution_readiness")
class AdapterExecutionReadinessInvariantError(RuntimeError): pass
def stable_hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def atomic_write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True); h=tempfile.NamedTemporaryFile("w",encoding="utf-8",delete=False,dir=p.parent); q=Path(h.name)
 try:
  with h: json.dump(v,h,sort_keys=True,indent=2); h.write("\n"); h.flush(); os.fsync(h.fileno())
  os.replace(q,p)
 finally:
  if q.exists(): q.unlink()
@dataclass(frozen=True)
class AdapterExecutionReadinessEntry:
 sequence:int; worker_id:str; work_item_id:str; adapter_id:str; read_operation:str; invocation_arguments:dict; checks:tuple[str,...]; status:str; source_active_adapter_invocation_hash:str; entry_hash:str
@dataclass(frozen=True)
class AdapterExecutionReadinessManifest:
 schema_version:str; engine_id:str; evaluated_at:str; readiness_id:str; status:str; worker_id:str; entries:tuple[AdapterExecutionReadinessEntry,...]; source_activation_hash:str; source_lineage:dict; corpus_read_execution_allowed:bool; research_execution_allowed:bool; signals_allowed:bool; alerts_allowed:bool; qseries_handoff_allowed:bool; execution_allowed:bool; source_mutation_allowed:bool; market_order_creation_allowed:bool; funds_movement_allowed:bool; portfolio_mutation_allowed:bool; manifest_hash:str
class OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionReadinessGate:
 def __init__(self,*,active_directory=DEFAULT_ACTIVE_DIRECTORY,output_directory=DEFAULT_OUTPUT_DIRECTORY): self.a=Path(active_directory); self.o=Path(output_directory)
 def _load(self):
  p=self.a/"current.json"
  if not p.exists(): raise AdapterExecutionReadinessInvariantError(f"OIA-042 current activation missing: {p}")
  x=json.loads(p.read_text()); h=x.pop("evidence_read_execution_adapter_invocation_activation_hash",None)
  if not isinstance(h,str) or len(h)!=64 or stable_hash(x)!=h: raise AdapterExecutionReadinessInvariantError("OIA-042 activation hash failed")
  x["evidence_read_execution_adapter_invocation_activation_hash"]=h
  for k,v in {"schema_version":"OIA-042","engine_id":"OIA-042","corpus_read_execution_allowed":False,"research_execution_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False}.items():
   if x.get(k)!=v: raise AdapterExecutionReadinessInvariantError(f"OIA-042 invariant failed: {k}")
  es=x.get("active_adapter_invocations")
  if not isinstance(es,list) or not es or x.get("active_adapter_invocation_count")!=len(es): raise AdapterExecutionReadinessInvariantError("active invocation records invalid")
  for e in es:
   eh=e.pop("active_adapter_invocation_hash",None)
   if not isinstance(eh,str) or len(eh)!=64 or stable_hash(e)!=eh: raise AdapterExecutionReadinessInvariantError("active invocation hash failed")
   e["active_adapter_invocation_hash"]=eh; a=e.get("invocation_arguments",{})
   if e.get("activation_status")!="evidence_read_execution_adapter_invocation_active" or not str(e.get("adapter_id","")).startswith("oracle_read_only_") or not str(e.get("read_operation","")).startswith("read_") or a.get("activated") is not True or a.get("read_only") is not True or a.get("execute") is not False: raise AdapterExecutionReadinessInvariantError("unsafe active invocation")
  return x
 def evaluate(self,*,evaluated_at:datetime,persist=True):
  if evaluated_at.tzinfo is None: raise AdapterExecutionReadinessInvariantError("evaluated_at must be timezone-aware")
  s=self._load(); es=[]
  for n,e in enumerate(s["active_adapter_invocations"],1):
   b={"sequence":n,"worker_id":e["worker_id"],"work_item_id":e["work_item_id"],"adapter_id":e["adapter_id"],"read_operation":e["read_operation"],"invocation_arguments":dict(e["invocation_arguments"]),"checks":("activation_hash_verified","adapter_read_only_verified","operation_read_only_verified","invocation_non_executing_verified","corpus_execution_disabled"),"status":STATUS_READY,"source_active_adapter_invocation_hash":e["active_adapter_invocation_hash"]}; es.append(AdapterExecutionReadinessEntry(**b,entry_hash=stable_hash(b)))
  sh=s["evidence_read_execution_adapter_invocation_activation_hash"]; rid="oia043-adapter-execution-readiness-"+stable_hash({"source":sh,"policy":POLICY_ID})[:32]; line={k:v for k,v in s.items() if k.startswith("source_") or k.endswith("_id") or k in ("dispatch_manifest_id","selected_batch_id","selected_batch_number")}
  b={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"evaluated_at":evaluated_at.astimezone(timezone.utc).isoformat(),"readiness_id":rid,"status":STATUS_ISSUED,"worker_id":s["worker_id"],"entries":tuple(es),"source_activation_hash":sh,"source_lineage":line,"corpus_read_execution_allowed":False,"research_execution_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False}; serial=dict(b); serial["entries"]=[asdict(x) for x in es]; r=AdapterExecutionReadinessManifest(**b,manifest_hash=stable_hash(serial))
  if persist:
   p=asdict(r); atomic_write(self.o/"current.json",p); atomic_write(self.o/"manifests"/f"{rid}.json",p); atomic_write(self.o/"workers"/r.worker_id/f"{rid}.json",p)
  return r
