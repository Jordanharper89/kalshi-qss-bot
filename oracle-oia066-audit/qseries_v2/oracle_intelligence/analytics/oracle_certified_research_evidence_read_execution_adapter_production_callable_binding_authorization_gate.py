from __future__ import annotations
import hashlib, json, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION="OIA-051"; ENGINE_ID="OIA-051"
POLICY_ID="oracle.certified-research-evidence-read-execution-adapter-production-callable-binding-authorization.v1"
STATUS_BINDING_AUTHORIZED="evidence_read_execution_adapter_production_callable_binding_authorized"
STATUS_BINDING_AUTHORIZATION_ISSUED="evidence_read_execution_adapter_production_callable_binding_authorization_issued"
DEFAULT_READINESS_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_callable_binding_readiness")
DEFAULT_AUTHORIZATION_DIRECTORY=Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_callable_binding_authorization")

class ProductionCallableBindingAuthorizationInvariantError(RuntimeError): pass

def _canonical(v):
    if is_dataclass(v): return _canonical(asdict(v))
    if isinstance(v, Mapping): return {str(k):_canonical(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [_canonical(x) for x in v]
    if isinstance(v,datetime):
        if v.tzinfo is None or v.utcoffset() is None: raise ProductionCallableBindingAuthorizationInvariantError("datetime must be timezone-aware")
        return v.astimezone(timezone.utc).isoformat()
    return v

def stable_hash(v): return hashlib.sha256(json.dumps(_canonical(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def _valid_hash(v): return isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v)
def _atomic_write(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    h=tempfile.NamedTemporaryFile("w",encoding="utf-8",newline="\n",delete=False,dir=str(path.parent),prefix=f".{path.name}.",suffix=".tmp")
    t=Path(h.name)
    try:
        with h:
            json.dump(_canonical(payload),h,sort_keys=True,indent=2,ensure_ascii=False); h.write("\n"); h.flush(); os.fsync(h.fileno())
        os.replace(t,path)
    finally:
        if t.exists(): t.unlink()

def _aware(v,name):
    if not isinstance(v,datetime) or v.tzinfo is None or v.utcoffset() is None: raise ProductionCallableBindingAuthorizationInvariantError(f"{name} must be timezone-aware")
    return v.astimezone(timezone.utc)

@dataclass(frozen=True)
class ProductionCallableBindingAuthorizationEntry:
    sequence:int; worker_id:str; work_item_id:str; adapter_id:str; read_operation:str; module_path:str; owner_name:str; callable_name:str; callable_kind:str; callable_qualified_name:str
    constructor_signature:str; callable_signature:str; authorized_constructor_parameters:tuple[str,...]; authorized_callable_parameters:tuple[str,...]
    required_constructor_parameters:tuple[str,...]; optional_constructor_parameters:tuple[str,...]; required_callable_parameters:tuple[str,...]; optional_callable_parameters:tuple[str,...]
    binding_authorized:bool; owner_instantiated:bool; constructor_arguments_bound:bool; callable_arguments_bound:bool; callable_invoked:bool; adapter_executed:bool
    authorization_checks:tuple[str,...]; authorization_status:str; source_callable_binding_readiness_hash:str; source_callable_resolution_hash:str
    source_active_invocation_execution_authorization_hash:str; source_active_invocation_execution_readiness_hash:str; source_active_execution_invocation_hash:str
    source_execution_invocation_hash:str; source_authorization_entry_hash:str; source_readiness_entry_hash:str; source_active_adapter_invocation_hash:str
    callable_binding_authorization_hash:str

@dataclass(frozen=True)
class ProductionCallableBindingAuthorizationManifest:
    schema_version:str; engine_id:str; authorized_at:str; callable_binding_authorization_id:str; callable_binding_authorization_status:str; callable_binding_authorization_policy_id:str
    worker_id:str; authorization_entry_count:int; authorization_entries:tuple[ProductionCallableBindingAuthorizationEntry,...]
    source_callable_binding_readiness_id:str; source_callable_binding_readiness_manifest_hash:str; source_callable_resolution_id:str; source_callable_resolution_manifest_hash:str
    source_execution_authorization_id:str; source_execution_authorization_manifest_hash:str; source_execution_readiness_id:str; source_execution_readiness_manifest_hash:str
    source_invocation_activation_id:str; source_invocation_activation_manifest_hash:str; source_execution_invocation_manifest_id:str; source_execution_invocation_manifest_hash:str
    source_prior_execution_authorization_id:str; source_prior_execution_authorization_manifest_hash:str; source_prior_execution_readiness_id:str; source_prior_execution_readiness_manifest_hash:str
    source_activation_hash:str; source_lineage:dict[str,Any]
    callable_binding_authorization_issued:bool; constructor_argument_binding_evaluation_allowed:bool; callable_argument_binding_evaluation_allowed:bool
    owner_instantiation_allowed:bool; owner_instantiation_performed:bool; constructor_argument_binding_allowed:bool; constructor_argument_binding_performed:bool
    callable_argument_binding_allowed:bool; callable_argument_binding_performed:bool; callable_invocation_allowed:bool; callable_invocation_performed:bool
    adapter_execution_allowed:bool; adapter_execution_performed:bool; corpus_read_execution_allowed:bool; corpus_read_execution_performed:bool
    research_execution_allowed:bool; analytic_conclusion_allowed:bool; forecast_creation_allowed:bool; signals_allowed:bool; alerts_allowed:bool; qseries_handoff_allowed:bool
    execution_allowed:bool; trading_recommendations_allowed:bool; source_mutation_allowed:bool; market_order_creation_allowed:bool; funds_movement_allowed:bool; portfolio_mutation_allowed:bool
    authorization_artifact_persistence_allowed:bool; callable_binding_authorization_manifest_hash:str

class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableBindingAuthorizationGate:
    def __init__(self,*,readiness_directory=DEFAULT_READINESS_DIRECTORY,authorization_directory=DEFAULT_AUTHORIZATION_DIRECTORY):
        self.readiness_directory=Path(readiness_directory); self.authorization_directory=Path(authorization_directory)
    def _load(self):
        path=self.readiness_directory/"current.json"
        if not path.exists(): raise ProductionCallableBindingAuthorizationInvariantError(f"OIA-050 current readiness artifact missing: {path}")
        try: d=json.loads(path.read_text(encoding="utf-8"))
        except Exception as e: raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 readiness artifact could not be decoded") from e
        digest=d.pop("callable_binding_readiness_manifest_hash",None)
        if not _valid_hash(digest) or stable_hash(d)!=digest: raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 manifest hash verification failed")
        d["callable_binding_readiness_manifest_hash"]=digest
        expected={"schema_version":"OIA-050","engine_id":"OIA-050","callable_binding_readiness_issued":True,"signature_inspection_performed":True,
        "owner_instantiation_allowed":False,"owner_instantiation_performed":False,"constructor_argument_binding_allowed":False,"constructor_argument_binding_performed":False,
        "callable_argument_binding_allowed":False,"callable_argument_binding_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,
        "adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,
        "signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False}
        for k,v in expected.items():
            if d.get(k)!=v: raise ProductionCallableBindingAuthorizationInvariantError(f"OIA-050 invariant failed: {k}")
        entries=d.get("readiness_entries"); count=d.get("readiness_entry_count")
        if not isinstance(entries,list) or not isinstance(count,int) or count<1 or len(entries)!=count: raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 readiness entries invalid")
        seen=set()
        for i,e in enumerate(entries,1):
            if not isinstance(e,dict): raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 readiness entry invalid")
            h=e.pop("callable_binding_readiness_hash",None)
            if not _valid_hash(h) or stable_hash(e)!=h: raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 readiness entry hash failed")
            e["callable_binding_readiness_hash"]=h
            if e.get("sequence")!=i: raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 readiness sequence invalid")
            aid=e.get("adapter_id")
            if not isinstance(aid,str) or not aid.startswith("oracle_read_only_") or aid in seen: raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 adapter identity invalid or duplicate")
            seen.add(aid)
            for k,v in {"module_imported":True,"owner_resolved":True,"callable_resolved":True,"signature_inspection_performed":True,"owner_instantiated":False,"constructor_arguments_bound":False,"callable_arguments_bound":False,"callable_invoked":False,"adapter_executed":False}.items():
                if e.get(k)!=v: raise ProductionCallableBindingAuthorizationInvariantError(f"OIA-050 entry invariant failed: {k}")
            for k in ("required_constructor_parameters","optional_constructor_parameters","required_callable_parameters","optional_callable_parameters"):
                if not isinstance(e.get(k),list): raise ProductionCallableBindingAuthorizationInvariantError(f"OIA-050 parameter classification invalid: {k}")
            allp=e["required_constructor_parameters"]+e["optional_constructor_parameters"]+e["required_callable_parameters"]+e["optional_callable_parameters"]
            if len(allp)!=len(set(allp)): raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 duplicate parameter identity")
        if not isinstance(d.get("source_lineage"),dict) or not d["source_lineage"]: raise ProductionCallableBindingAuthorizationInvariantError("OIA-050 lineage missing")
        return d
    def authorize(self,*,authorized_at,persist=True):
        authorized_at=_aware(authorized_at,"authorized_at"); s=self._load(); out=[]
        for i,e in enumerate(s["readiness_entries"],1):
            ac=tuple(e["required_constructor_parameters"]+e["optional_constructor_parameters"])
            am=tuple(e["required_callable_parameters"]+e["optional_callable_parameters"])
            body={"sequence":i,"worker_id":e["worker_id"],"work_item_id":e["work_item_id"],"adapter_id":e["adapter_id"],"read_operation":e["read_operation"],"module_path":e["module_path"],"owner_name":e["owner_name"],"callable_name":e["callable_name"],"callable_kind":e["callable_kind"],"callable_qualified_name":e["callable_qualified_name"],"constructor_signature":e["constructor_signature"],"callable_signature":e["callable_signature"],"authorized_constructor_parameters":ac,"authorized_callable_parameters":am,"required_constructor_parameters":tuple(e["required_constructor_parameters"]),"optional_constructor_parameters":tuple(e["optional_constructor_parameters"]),"required_callable_parameters":tuple(e["required_callable_parameters"]),"optional_callable_parameters":tuple(e["optional_callable_parameters"]),"binding_authorized":True,"owner_instantiated":False,"constructor_arguments_bound":False,"callable_arguments_bound":False,"callable_invoked":False,"adapter_executed":False,"authorization_checks":("binding_readiness_manifest_hash_verified","binding_readiness_entry_hash_verified","production_signature_identity_verified","constructor_parameter_allowlist_authorized","callable_parameter_allowlist_authorized","owner_instantiation_not_performed","argument_binding_not_performed","callable_invocation_not_performed","adapter_execution_not_performed","oracle_qseries_boundary_verified"),"authorization_status":STATUS_BINDING_AUTHORIZED,"source_callable_binding_readiness_hash":e["callable_binding_readiness_hash"],"source_callable_resolution_hash":e["source_callable_resolution_hash"],"source_active_invocation_execution_authorization_hash":e["source_active_invocation_execution_authorization_hash"],"source_active_invocation_execution_readiness_hash":e["source_active_invocation_execution_readiness_hash"],"source_active_execution_invocation_hash":e["source_active_execution_invocation_hash"],"source_execution_invocation_hash":e["source_execution_invocation_hash"],"source_authorization_entry_hash":e["source_authorization_entry_hash"],"source_readiness_entry_hash":e["source_readiness_entry_hash"],"source_active_adapter_invocation_hash":e["source_active_adapter_invocation_hash"]}
            out.append(ProductionCallableBindingAuthorizationEntry(**body,callable_binding_authorization_hash=stable_hash(body)))
        aid="oia051-callable-binding-authorization-"+stable_hash({"source":s["callable_binding_readiness_manifest_hash"],"policy":POLICY_ID})[:32]
        body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"authorized_at":authorized_at.isoformat(),"callable_binding_authorization_id":aid,"callable_binding_authorization_status":STATUS_BINDING_AUTHORIZATION_ISSUED,"callable_binding_authorization_policy_id":POLICY_ID,"worker_id":s["worker_id"],"authorization_entry_count":len(out),"authorization_entries":tuple(out),"source_callable_binding_readiness_id":s["callable_binding_readiness_id"],"source_callable_binding_readiness_manifest_hash":s["callable_binding_readiness_manifest_hash"],"source_callable_resolution_id":s["source_callable_resolution_id"],"source_callable_resolution_manifest_hash":s["source_callable_resolution_manifest_hash"],"source_execution_authorization_id":s["source_execution_authorization_id"],"source_execution_authorization_manifest_hash":s["source_execution_authorization_manifest_hash"],"source_execution_readiness_id":s["source_execution_readiness_id"],"source_execution_readiness_manifest_hash":s["source_execution_readiness_manifest_hash"],"source_invocation_activation_id":s["source_invocation_activation_id"],"source_invocation_activation_manifest_hash":s["source_invocation_activation_manifest_hash"],"source_execution_invocation_manifest_id":s["source_execution_invocation_manifest_id"],"source_execution_invocation_manifest_hash":s["source_execution_invocation_manifest_hash"],"source_prior_execution_authorization_id":s["source_prior_execution_authorization_id"],"source_prior_execution_authorization_manifest_hash":s["source_prior_execution_authorization_manifest_hash"],"source_prior_execution_readiness_id":s["source_prior_execution_readiness_id"],"source_prior_execution_readiness_manifest_hash":s["source_prior_execution_readiness_manifest_hash"],"source_activation_hash":s["source_activation_hash"],"source_lineage":dict(s["source_lineage"]),"callable_binding_authorization_issued":True,"constructor_argument_binding_evaluation_allowed":True,"callable_argument_binding_evaluation_allowed":True,"owner_instantiation_allowed":False,"owner_instantiation_performed":False,"constructor_argument_binding_allowed":False,"constructor_argument_binding_performed":False,"callable_argument_binding_allowed":False,"callable_argument_binding_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"authorization_artifact_persistence_allowed":True}
        serial=dict(body); serial["authorization_entries"]=[asdict(x) for x in out]
        result=ProductionCallableBindingAuthorizationManifest(**body,callable_binding_authorization_manifest_hash=stable_hash(serial))
        if persist:
            payload=asdict(result); _atomic_write(self.authorization_directory/"current.json",payload); _atomic_write(self.authorization_directory/"authorizations"/f"{aid}.json",payload); _atomic_write(self.authorization_directory/"workers"/result.worker_id/f"{aid}.json",payload)
        return result
