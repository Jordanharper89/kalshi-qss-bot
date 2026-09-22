from __future__ import annotations
import hashlib, json, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION="OIA-053"
ENGINE_ID="OIA-053"
POLICY_ID="oracle.certified-research-evidence-read-execution-adapter-production-owner-construction-readiness.v1"
STATUS_OWNER_CONSTRUCTION_READY="evidence_read_execution_adapter_production_owner_construction_ready"
STATUS_READINESS_ISSUED="evidence_read_execution_adapter_production_owner_construction_readiness_issued"
DEFAULT_BINDING_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_callable_argument_binding")
DEFAULT_READINESS_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_construction_readiness")

class ProductionOwnerConstructionReadinessInvariantError(RuntimeError): pass

def _canonical(v:Any)->Any:
    if is_dataclass(v): return _canonical(asdict(v))
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [_canonical(x) for x in v]
    if isinstance(v,datetime):
        if v.tzinfo is None or v.utcoffset() is None: raise ProductionOwnerConstructionReadinessInvariantError("datetime must be timezone-aware")
        return v.astimezone(timezone.utc).isoformat()
    return v

def stable_hash(v:Any)->str:
    return hashlib.sha256(json.dumps(_canonical(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def _valid_hash(v:Any)->bool: return isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v)
def _aware(v:datetime,name:str)->datetime:
    if not isinstance(v,datetime) or v.tzinfo is None or v.utcoffset() is None: raise ProductionOwnerConstructionReadinessInvariantError(f"{name} must be timezone-aware")
    return v.astimezone(timezone.utc)
def _atomic(path:Path,payload:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    h=tempfile.NamedTemporaryFile("w",encoding="utf-8",newline="\n",delete=False,dir=str(path.parent),prefix=f".{path.name}.",suffix=".tmp")
    tmp=Path(h.name)
    try:
        with h:
            json.dump(_canonical(payload),h,sort_keys=True,indent=2,ensure_ascii=False); h.write("\n"); h.flush(); os.fsync(h.fileno())
        os.replace(tmp,path)
    finally:
        if tmp.exists(): tmp.unlink()

@dataclass(frozen=True)
class ProductionOwnerConstructionReadinessEntry:
    sequence:int; worker_id:str; work_item_id:str; adapter_id:str; read_operation:str
    module_path:str; owner_name:str; callable_name:str; constructor_signature:str; callable_signature:str
    bound_constructor_arguments:dict[str,Any]; bound_callable_arguments:dict[str,Any]
    constructor_binding_hash:str; callable_binding_hash:str
    constructor_dependency_names:tuple[str,...]; constructor_default_names:tuple[str,...]
    symbolic_dependencies_only:bool; owner_construction_ready:bool; owner_instantiated:bool
    callable_bound_to_owner:bool; callable_invoked:bool; adapter_executed:bool
    readiness_checks:tuple[str,...]; readiness_status:str
    source_callable_argument_binding_hash:str; source_callable_binding_authorization_hash:str
    source_callable_binding_readiness_hash:str; source_callable_resolution_hash:str
    source_active_invocation_execution_authorization_hash:str; source_active_invocation_execution_readiness_hash:str
    source_active_execution_invocation_hash:str; source_execution_invocation_hash:str
    source_authorization_entry_hash:str; source_readiness_entry_hash:str; source_active_adapter_invocation_hash:str
    owner_construction_readiness_hash:str

@dataclass(frozen=True)
class ProductionOwnerConstructionReadinessManifest:
    schema_version:str; engine_id:str; evaluated_at:str; owner_construction_readiness_id:str
    owner_construction_readiness_status:str; owner_construction_readiness_policy_id:str
    worker_id:str; readiness_entry_count:int; readiness_entries:tuple[ProductionOwnerConstructionReadinessEntry,...]
    source_callable_argument_binding_id:str; source_callable_argument_binding_manifest_hash:str
    source_lineage:dict[str,Any]
    owner_construction_readiness_issued:bool; owner_construction_authorization_evaluation_allowed:bool
    owner_instantiation_allowed:bool; owner_instantiation_performed:bool
    callable_binding_to_owner_allowed:bool; callable_binding_to_owner_performed:bool
    callable_invocation_allowed:bool; callable_invocation_performed:bool
    adapter_execution_allowed:bool; adapter_execution_performed:bool
    corpus_read_execution_allowed:bool; corpus_read_execution_performed:bool
    research_execution_allowed:bool; analytic_conclusion_allowed:bool; forecast_creation_allowed:bool
    signals_allowed:bool; alerts_allowed:bool; qseries_handoff_allowed:bool; execution_allowed:bool
    trading_recommendations_allowed:bool; source_mutation_allowed:bool; market_order_creation_allowed:bool
    funds_movement_allowed:bool; portfolio_mutation_allowed:bool; readiness_artifact_persistence_allowed:bool
    owner_construction_readiness_manifest_hash:str

class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionReadinessGate:
    def __init__(self,*,binding_directory:Path|str=DEFAULT_BINDING_DIRECTORY,readiness_directory:Path|str=DEFAULT_READINESS_DIRECTORY)->None:
        self.binding_directory=Path(binding_directory); self.readiness_directory=Path(readiness_directory)
    def _load(self)->dict[str,Any]:
        path=self.binding_directory/"current.json"
        if not path.exists(): raise ProductionOwnerConstructionReadinessInvariantError(f"OIA-052 current binding artifact missing: {path}")
        try: p=json.loads(path.read_text(encoding="utf-8"))
        except Exception as e: raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 binding artifact could not be decoded") from e
        digest=p.pop("callable_argument_binding_manifest_hash",None)
        if not _valid_hash(digest) or stable_hash(p)!=digest: raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 manifest hash verification failed")
        p["callable_argument_binding_manifest_hash"]=digest
        expected={"schema_version":"OIA-052","engine_id":"OIA-052","symbolic_binding_only":True,"owner_instantiation_allowed":False,"owner_instantiation_performed":False,"constructor_argument_binding_performed":True,"callable_argument_binding_performed":True,"callable_invocation_evaluation_allowed":True,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False}
        for k,v in expected.items():
            if p.get(k)!=v: raise ProductionOwnerConstructionReadinessInvariantError(f"OIA-052 invariant failed: {k}")
        entries=p.get("binding_entries"); count=p.get("binding_entry_count")
        if not isinstance(entries,list) or not isinstance(count,int) or isinstance(count,bool) or count<1 or len(entries)!=count: raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 binding entries invalid")
        seen=set()
        for i,e in enumerate(entries,1):
            if not isinstance(e,dict): raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 binding entry invalid")
            h=e.pop("callable_argument_binding_hash",None)
            if not _valid_hash(h) or stable_hash(e)!=h: raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 binding entry hash verification failed")
            e["callable_argument_binding_hash"]=h
            if e.get("sequence")!=i: raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 sequence invalid")
            aid=e.get("adapter_id")
            if not isinstance(aid,str) or not aid.startswith("oracle_read_only_") or aid in seen: raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 adapter unknown or duplicate")
            seen.add(aid)
            for k,v in {"owner_instantiated":False,"callable_bound_to_owner":False,"callable_invoked":False,"adapter_executed":False}.items():
                if e.get(k)!=v: raise ProductionOwnerConstructionReadinessInvariantError(f"OIA-052 entry invariant failed: {k}")
            for k in ("constructor_binding_hash","callable_binding_hash"):
                if not _valid_hash(e.get(k)): raise ProductionOwnerConstructionReadinessInvariantError(f"OIA-052 invalid hash: {k}")
            if stable_hash(e.get("bound_constructor_arguments"))!=e["constructor_binding_hash"]: raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 constructor binding changed")
            if stable_hash(e.get("bound_callable_arguments"))!=e["callable_binding_hash"]: raise ProductionOwnerConstructionReadinessInvariantError("OIA-052 callable binding changed")
        return p
    def evaluate(self,*,evaluated_at:datetime,persist:bool=True)->ProductionOwnerConstructionReadinessManifest:
        evaluated_at=_aware(evaluated_at,"evaluated_at"); source=self._load(); out=[]
        for i,e in enumerate(source["binding_entries"],1):
            ctor=dict(e["bound_constructor_arguments"])
            dependency_names=tuple(k for k,v in ctor.items() if isinstance(v,str) and v.startswith("symbolic://"))
            default_names=tuple(k for k in ctor if k not in dependency_names)
            if any(isinstance(v,str) and ("password" in v.lower() or "secret" in v.lower() or "token" in v.lower()) for v in ctor.values()): raise ProductionOwnerConstructionReadinessInvariantError("Unsafe constructor material detected")
            body={"sequence":i,"worker_id":e["worker_id"],"work_item_id":e["work_item_id"],"adapter_id":e["adapter_id"],"read_operation":e["read_operation"],"module_path":e["module_path"],"owner_name":e["owner_name"],"callable_name":e["callable_name"],"constructor_signature":e["constructor_signature"],"callable_signature":e["callable_signature"],"bound_constructor_arguments":ctor,"bound_callable_arguments":dict(e["bound_callable_arguments"]),"constructor_binding_hash":e["constructor_binding_hash"],"callable_binding_hash":e["callable_binding_hash"],"constructor_dependency_names":dependency_names,"constructor_default_names":default_names,"symbolic_dependencies_only":all(isinstance(ctor[n],str) and ctor[n].startswith("symbolic://") for n in dependency_names),"owner_construction_ready":True,"owner_instantiated":False,"callable_bound_to_owner":False,"callable_invoked":False,"adapter_executed":False,"readiness_checks":("oia052_manifest_hash_verified","oia052_entry_hash_verified","constructor_binding_hash_verified","callable_binding_hash_verified","constructor_dependencies_classified","symbolic_dependencies_preserved","owner_not_instantiated","callable_not_bound_to_owner","callable_not_invoked","adapter_not_executed","oracle_qseries_boundary_verified"),"readiness_status":STATUS_OWNER_CONSTRUCTION_READY,"source_callable_argument_binding_hash":e["callable_argument_binding_hash"],"source_callable_binding_authorization_hash":e["source_callable_binding_authorization_hash"],"source_callable_binding_readiness_hash":e["source_callable_binding_readiness_hash"],"source_callable_resolution_hash":e["source_callable_resolution_hash"],"source_active_invocation_execution_authorization_hash":e["source_active_invocation_execution_authorization_hash"],"source_active_invocation_execution_readiness_hash":e["source_active_invocation_execution_readiness_hash"],"source_active_execution_invocation_hash":e["source_active_execution_invocation_hash"],"source_execution_invocation_hash":e["source_execution_invocation_hash"],"source_authorization_entry_hash":e["source_authorization_entry_hash"],"source_readiness_entry_hash":e["source_readiness_entry_hash"],"source_active_adapter_invocation_hash":e["source_active_adapter_invocation_hash"]}
            out.append(ProductionOwnerConstructionReadinessEntry(**body,owner_construction_readiness_hash=stable_hash(body)))
        source_hash=source["callable_argument_binding_manifest_hash"]
        rid="oia053-owner-construction-readiness-"+stable_hash({"source":source_hash,"policy":POLICY_ID})[:32]
        body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"evaluated_at":evaluated_at.isoformat(),"owner_construction_readiness_id":rid,"owner_construction_readiness_status":STATUS_READINESS_ISSUED,"owner_construction_readiness_policy_id":POLICY_ID,"worker_id":source["worker_id"],"readiness_entry_count":len(out),"readiness_entries":tuple(out),"source_callable_argument_binding_id":source["callable_argument_binding_id"],"source_callable_argument_binding_manifest_hash":source_hash,"source_lineage":dict(source.get("source_lineage",{})),"owner_construction_readiness_issued":True,"owner_construction_authorization_evaluation_allowed":True,"owner_instantiation_allowed":False,"owner_instantiation_performed":False,"callable_binding_to_owner_allowed":False,"callable_binding_to_owner_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"readiness_artifact_persistence_allowed":True}
        serial=dict(body); serial["readiness_entries"]=[asdict(x) for x in out]
        result=ProductionOwnerConstructionReadinessManifest(**body,owner_construction_readiness_manifest_hash=stable_hash(serial))
        if persist:
            payload=asdict(result); _atomic(self.readiness_directory/"current.json",payload); _atomic(self.readiness_directory/"readiness"/f"{rid}.json",payload); _atomic(self.readiness_directory/"workers"/result.worker_id/f"{rid}.json",payload)
        return result
