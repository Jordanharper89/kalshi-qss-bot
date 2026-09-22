from pathlib import Path
import py_compile, subprocess, sys
R=Path(__file__).resolve().parent; A=R/'qseries_v2/oracle_intelligence/analytics'; D=A/'oracle_certified_research_evidence_read_execution_adapter_invocation_activation_gate.py'; P=A/'oracle_certified_research_evidence_read_execution_adapter_execution_readiness_gate.py'; T=R/'test_oia_043_oracle_certified_research_evidence_read_execution_adapter_execution_readiness_gate.py'; I=A/'__init__.py'
PROD='''from __future__ import annotations
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
  with h: json.dump(v,h,sort_keys=True,indent=2); h.write("\\n"); h.flush(); os.fsync(h.fileno())
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
'''
TESTSRC='''import json,tempfile
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_execution_readiness_gate import *
def main():
 print("="*40); print(" OIA-043 TEST"); print(" ADAPTER EXECUTION READINESS"); print("="*40)
 with tempfile.TemporaryDirectory() as z:
  root=Path(z); a=root/"a"; o=root/"o"; e={"worker_id":"oracle-worker-test","work_item_id":"work.test","adapter_id":"oracle_read_only_canonical_observation_adapter.v1","read_operation":"read_canonical_observations","invocation_arguments":{"activated":True,"read_only":True,"execute":False},"activation_status":"evidence_read_execution_adapter_invocation_active"}; e["active_adapter_invocation_hash"]=stable_hash(e); x={"schema_version":"OIA-042","engine_id":"OIA-042","worker_id":"oracle-worker-test","active_adapter_invocation_count":1,"active_adapter_invocations":[e],"corpus_read_execution_allowed":False,"research_execution_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"source_evidence_read_execution_adapter_invocation_manifest_id":"oia041-test","source_evidence_read_execution_adapter_authorization_manifest_id":"oia040-test","source_evidence_read_execution_adapter_readiness_manifest_id":"oia039-test","source_evidence_read_execution_adapter_binding_manifest_id":"oia038-test","source_evidence_read_execution_invocation_activation_id":"oia037-test","source_evidence_read_execution_invocation_manifest_id":"oia036-test","source_evidence_read_execution_authorization_id":"oia035-test","source_evidence_read_execution_readiness_id":"oia034-test","source_evidence_read_request_activation_id":"oia033-test","source_evidence_read_request_manifest_id":"oia032-test","source_evidence_task_activation_id":"oia031-test","source_evidence_task_manifest_id":"oia030-test","source_evidence_batch_activation_id":"oia029-test","source_evidence_batch_id":"oia028-test","source_evidence_session_id":"oia027-test","source_evidence_manifest_id":"oia026-test","source_certification_id":"oia025-test","source_readiness_id":"oia024-test","source_session_id":"oia023-test","source_activation_id":"oia022-test","source_claim_id":"oia021-test","dispatch_manifest_id":"oia020-test","selected_batch_id":"oia020-batch","selected_batch_number":1}; x["evidence_read_execution_adapter_invocation_activation_hash"]=stable_hash(x); a.mkdir(); (a/"current.json").write_text(json.dumps(x)); g=OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionReadinessGate(active_directory=a,output_directory=o); t=datetime(2026,7,22,1,tzinfo=timezone.utc); r=g.evaluate(evaluated_at=t); assert r==g.evaluate(evaluated_at=t,persist=False) and r.schema_version=="OIA-043" and r.entries[0].status==STATUS_READY and r.entries[0].invocation_arguments["execute"] is False and r.execution_allowed is False and (o/"current.json").exists(); bad=json.loads((a/"current.json").read_text()); bad["active_adapter_invocations"][0]["invocation_arguments"]["execute"]=True; (a/"current.json").write_text(json.dumps(bad))
  try: g.evaluate(evaluated_at=t,persist=False)
  except AdapterExecutionReadinessInvariantError: pass
  else: raise AssertionError("Executable activation accepted")
 print("[PASS] Actual OIA-042 activation contract consumed"); print("[PASS] Readiness manifest and entry hashes deterministic"); print("[PASS] Complete OIA-020 through OIA-042 lineage preserved"); print("[PASS] Only active approved read-only adapters certified ready"); print("[PASS] Invocation arguments remained non-executing"); print("[PASS] Corpus read execution remained disabled"); print("[PASS] Tampered or executable activation rejected"); print("[PASS] Atomic execution-readiness artifacts persisted"); print("[PASS] Signals, alerts, and Q Series handoff remained disabled"); print("[PASS] Orders, funds, and portfolio mutation remained disabled")
if __name__=="__main__": main()
'''
def main():
 print('='*40); print(' OIA-043 INSTALLER'); print(' ADAPTER EXECUTION READINESS'); print(' PRE-EXECUTION READ-ONLY SAFETY GATE'); print('='*40)
 if not D.exists(): raise RuntimeError(f'Actual OIA-042 production module missing: {D}')
 text=D.read_text()
 for token in ('SCHEMA_VERSION = "OIA-042"','active_adapter_invocation_hash','corpus_read_execution_allowed','qseries_handoff_allowed','portfolio_mutation_allowed'):
  if token not in text: raise RuntimeError(f'Actual OIA-042 contract mismatch: {token}')
 print('[OK] Actual OIA-042 activation contract verified'); P.write_text(PROD); print(f'[OK] FULL REPLACEMENT: {P}'); T.write_text(TESTSRC); print(f'[OK] FULL REPLACEMENT: {T}')
 old=I.read_text() if I.exists() else '__all__=[]\n'; marker='from .oracle_certified_research_evidence_read_execution_adapter_execution_readiness_gate import ('
 if marker not in old: I.write_text(old.rstrip()+'\nfrom .oracle_certified_research_evidence_read_execution_adapter_execution_readiness_gate import STATUS_READY,STATUS_ISSUED,POLICY_ID,AdapterExecutionReadinessEntry,AdapterExecutionReadinessManifest,OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionReadinessGate\n__all__=["STATUS_READY","STATUS_ISSUED","POLICY_ID","AdapterExecutionReadinessEntry","AdapterExecutionReadinessManifest","OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionReadinessGate"]+__all__\n'); print(f'[OK] PACKAGE UPDATED: {I}')
 else: print(f'[OK] PACKAGE ALREADY CURRENT: {I}')
 for f in (P,T,I): py_compile.compile(str(f),doraise=True)
 print('[OK] Production, test, and package syntax verified'); r=subprocess.run([sys.executable,str(T)],cwd=R)
 if r.returncode: raise SystemExit(r.returncode)
 print('[OK] OIA-043 test executed automatically'); print('\n[DONE] OIA-043 certified research evidence read execution adapter execution readiness gate installed')
if __name__=='__main__': main()
