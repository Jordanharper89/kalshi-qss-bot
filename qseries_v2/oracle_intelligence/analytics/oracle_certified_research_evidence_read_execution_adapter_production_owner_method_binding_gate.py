from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIA-058"
ENGINE_ID = "OIA-058"
POLICY_ID = "oracle.certified-research-evidence-read-execution-adapter-production-owner-method-binding.v1"
STATUS_METHOD_BOUND = "evidence_read_execution_adapter_production_owner_method_bound"
STATUS_BINDING_ISSUED = "evidence_read_execution_adapter_production_owner_method_binding_issued"
DEFAULT_AUTHORIZATION_DIRECTORY = Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_method_binding_authorization")
DEFAULT_BINDING_DIRECTORY = Path("runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_method_binding")

APPROVED = {
    "oracle_read_only_canonical_observation_adapter.v1": (
        "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "OracleLiveCorpusInspector", "inspect",
        "(*, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",
    ),
    "oracle_read_only_market_state_lineage_adapter.v1": (
        "qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger",
        "OracleCanonicalMarketLineageLedger", "records",
        "() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'",
    ),
}

class ProductionOwnerMethodBindingInvariantError(RuntimeError):
    pass

def _canonical(value: Any) -> Any:
    if is_dataclass(value): return _canonical(asdict(value))
    if isinstance(value, Mapping): return {str(k): _canonical(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None: raise ProductionOwnerMethodBindingInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    return value

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def _valid_hash(value: Any) -> bool:
    return isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value)

def _aware(value: datetime, name: str) -> datetime:
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None: raise ProductionOwnerMethodBindingInvariantError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)

def _atomic_write(path: Path, payload: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    handle=tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",newline="\n",delete=False,dir=str(path.parent)); temporary=Path(handle.name)
    try:
        with handle:
            json.dump(_canonical(payload),handle,sort_keys=True,indent=2,ensure_ascii=False); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary,path)
    finally:
        if temporary.exists(): temporary.unlink()

def _blocked_connection_factory():
    raise ProductionOwnerMethodBindingInvariantError("inert connection factory cannot connect")

@dataclass(frozen=True)
class ProductionOwnerMethodBindingEntry:
    sequence: int; worker_id: str; work_item_id: str; adapter_id: str; read_operation: str
    module_path: str; owner_name: str; callable_name: str; owner_state_fingerprint: str
    owner_construction_hash: str; method_descriptor_module: str; method_descriptor_qualname: str
    bound_method_type: str; bound_method_module: str; bound_method_qualname: str; bound_method_signature: str
    bound_method_self_verified: bool; bound_method_function_verified: bool
    owner_reconstructed: bool; method_binding_requested: bool; method_bound_to_owner: bool
    method_invoked: bool; adapter_executed: bool; corpus_read_executed: bool
    binding_checks: tuple[str,...]; binding_status: str
    source_owner_method_binding_authorization_hash: str; source_owner_method_binding_readiness_hash: str
    source_owner_construction_authorization_hash: str; source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str; owner_method_binding_hash: str

@dataclass(frozen=True)
class ProductionOwnerMethodBindingManifest:
    schema_version: str; engine_id: str; bound_at: str; owner_method_binding_id: str
    owner_method_binding_status: str; owner_method_binding_policy_id: str; worker_id: str
    binding_entry_count: int; binding_entries: tuple[ProductionOwnerMethodBindingEntry,...]
    source_owner_method_binding_authorization_id: str; source_owner_method_binding_authorization_manifest_hash: str
    source_owner_method_binding_readiness_id: str; source_owner_method_binding_readiness_manifest_hash: str
    source_owner_construction_id: str; source_owner_construction_manifest_hash: str; source_lineage: dict[str,Any]
    owner_reconstruction_allowed: bool; owner_reconstruction_performed: bool
    callable_binding_to_owner_allowed: bool; callable_binding_to_owner_performed: bool
    callable_invocation_allowed: bool; callable_invocation_performed: bool
    adapter_execution_allowed: bool; adapter_execution_performed: bool
    corpus_read_execution_allowed: bool; corpus_read_execution_performed: bool
    research_execution_allowed: bool; analytic_conclusion_allowed: bool; forecast_creation_allowed: bool
    signals_allowed: bool; alerts_allowed: bool; qseries_handoff_allowed: bool; execution_allowed: bool
    trading_recommendations_allowed: bool; source_mutation_allowed: bool; market_order_creation_allowed: bool
    funds_movement_allowed: bool; portfolio_mutation_allowed: bool; binding_artifact_persistence_allowed: bool
    owner_instances_retained: bool; bound_methods_retained: bool; owner_method_binding_manifest_hash: str

class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingGate:
    def __init__(self,*,authorization_directory:Path|str=DEFAULT_AUTHORIZATION_DIRECTORY,binding_directory:Path|str=DEFAULT_BINDING_DIRECTORY):
        self.authorization_directory=Path(authorization_directory); self.binding_directory=Path(binding_directory)

    def _load_authorization(self)->dict[str,Any]:
        path=self.authorization_directory/"current.json"
        if not path.exists(): raise ProductionOwnerMethodBindingInvariantError(f"OIA-057 current authorization artifact missing: {path}")
        try: source=json.loads(path.read_text(encoding="utf-8"))
        except Exception as error: raise ProductionOwnerMethodBindingInvariantError("OIA-057 authorization artifact could not be decoded") from error
        manifest_hash=source.pop("owner_method_binding_authorization_manifest_hash",None)
        if not _valid_hash(manifest_hash) or stable_hash(source)!=manifest_hash: raise ProductionOwnerMethodBindingInvariantError("OIA-057 authorization manifest hash verification failed")
        source["owner_method_binding_authorization_manifest_hash"]=manifest_hash
        required_flags={"owner_method_binding_authorization_issued":True,"owner_reconstruction_allowed":False,"owner_reconstruction_performed":False,"callable_binding_to_owner_allowed":False,"callable_binding_to_owner_performed":False,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False}
        for field,expected in required_flags.items():
            if source.get(field)!=expected: raise ProductionOwnerMethodBindingInvariantError(f"unsafe OIA-057 authorization manifest: {field}")
        entries=source.get("authorization_entries")
        if not isinstance(entries,list) or not entries or source.get("authorization_entry_count")!=len(entries): raise ProductionOwnerMethodBindingInvariantError("OIA-057 authorization entry count invalid")
        seen=set()
        for entry in entries:
            entry_hash=entry.pop("owner_method_binding_authorization_hash",None)
            if not _valid_hash(entry_hash) or stable_hash(entry)!=entry_hash: raise ProductionOwnerMethodBindingInvariantError("OIA-057 authorization entry hash verification failed")
            entry["owner_method_binding_authorization_hash"]=entry_hash
            adapter_id=entry.get("adapter_id"); approved=APPROVED.get(adapter_id)
            if approved is None or (entry.get("module_path"),entry.get("owner_name"),entry.get("callable_name"))!=approved[:3]: raise ProductionOwnerMethodBindingInvariantError("unapproved OIA-057 owner method identity")
            key=(entry.get("worker_id"),entry.get("work_item_id"),adapter_id)
            if key in seen: raise ProductionOwnerMethodBindingInvariantError("duplicate OIA-057 owner method authorization")
            seen.add(key)
            safe={"owner_method_binding_ready":True,"owner_method_binding_authorized":True,"owner_reconstruction_requested":False,"owner_reconstructed":False,"method_binding_requested":False,"method_bound_to_owner":False,"method_invoked":False,"adapter_executed":False}
            for field,expected in safe.items():
                if entry.get(field)!=expected: raise ProductionOwnerMethodBindingInvariantError(f"unsafe OIA-057 authorization entry: {field}")
            for hf in ("owner_state_fingerprint","owner_construction_hash","source_owner_method_binding_readiness_hash","source_owner_construction_authorization_hash","source_owner_construction_readiness_hash","source_callable_argument_binding_hash"):
                if not _valid_hash(entry.get(hf)): raise ProductionOwnerMethodBindingInvariantError(f"OIA-057 entry hash invalid: {hf}")
        if not isinstance(source.get("source_lineage"),dict) or not source["source_lineage"]: raise ProductionOwnerMethodBindingInvariantError("OIA-057 source lineage missing")
        return source

    def bind(self,*,bound_at:datetime,persist:bool=True)->ProductionOwnerMethodBindingManifest:
        bound_at=_aware(bound_at,"bound_at"); source=self._load_authorization(); results=[]
        for sequence,entry in enumerate(source["authorization_entries"],start=1):
            module=importlib.import_module(entry["module_path"]); owner_type=getattr(module,entry["owner_name"],None)
            if not inspect.isclass(owner_type): raise ProductionOwnerMethodBindingInvariantError("approved owner class could not be resolved")
            if entry["adapter_id"]=="oracle_read_only_canonical_observation_adapter.v1":
                owner=owner_type(connection_factory=_blocked_connection_factory,stale_after_seconds=300,market_limit=100)
            else: owner=owner_type()
            try:
                method=getattr(owner,entry["callable_name"],None)
                if method is None or not inspect.ismethod(method): raise ProductionOwnerMethodBindingInvariantError("approved method did not bind to owner")
                approved=APPROVED[entry["adapter_id"]]
                if method.__self__ is not owner: raise ProductionOwnerMethodBindingInvariantError("bound method owner identity mismatch")
                function=method.__func__
                if function.__module__!=approved[0] or function.__qualname__!=f"{approved[1]}.{approved[2]}": raise ProductionOwnerMethodBindingInvariantError("bound method function identity mismatch")
                bound_signature=str(inspect.signature(method))
                if bound_signature!=approved[3]: raise ProductionOwnerMethodBindingInvariantError("bound method signature mismatch")
                body={"sequence":sequence,"worker_id":entry["worker_id"],"work_item_id":entry["work_item_id"],"adapter_id":entry["adapter_id"],"read_operation":entry["read_operation"],"module_path":entry["module_path"],"owner_name":entry["owner_name"],"callable_name":entry["callable_name"],"owner_state_fingerprint":entry["owner_state_fingerprint"],"owner_construction_hash":entry["owner_construction_hash"],"method_descriptor_module":entry["method_descriptor_module"],"method_descriptor_qualname":entry["method_descriptor_qualname"],"bound_method_type":type(method).__name__,"bound_method_module":function.__module__,"bound_method_qualname":function.__qualname__,"bound_method_signature":bound_signature,"bound_method_self_verified":True,"bound_method_function_verified":True,"owner_reconstructed":True,"method_binding_requested":True,"method_bound_to_owner":True,"method_invoked":False,"adapter_executed":False,"corpus_read_executed":False,"binding_checks":("oia057_authorization_manifest_hash_verified","oia057_authorization_entry_hash_verified","approved_owner_reconstructed_with_inert_dependencies","approved_method_bound_to_exact_owner","bound_method_self_identity_verified","bound_method_function_identity_verified","bound_method_signature_verified","method_not_invoked","adapter_not_executed","corpus_not_read","oracle_qseries_boundary_verified"),"binding_status":STATUS_METHOD_BOUND,"source_owner_method_binding_authorization_hash":entry["owner_method_binding_authorization_hash"],"source_owner_method_binding_readiness_hash":entry["source_owner_method_binding_readiness_hash"],"source_owner_construction_authorization_hash":entry["source_owner_construction_authorization_hash"],"source_owner_construction_readiness_hash":entry["source_owner_construction_readiness_hash"],"source_callable_argument_binding_hash":entry["source_callable_argument_binding_hash"]}
                results.append(ProductionOwnerMethodBindingEntry(**body,owner_method_binding_hash=stable_hash(body)))
            finally:
                method=None; owner=None
        source_hash=source["owner_method_binding_authorization_manifest_hash"]
        binding_id="oia058-owner-method-binding-"+stable_hash({"source":source_hash,"policy":POLICY_ID})[:32]
        body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"bound_at":bound_at.isoformat(),"owner_method_binding_id":binding_id,"owner_method_binding_status":STATUS_BINDING_ISSUED,"owner_method_binding_policy_id":POLICY_ID,"worker_id":source["worker_id"],"binding_entry_count":len(results),"binding_entries":tuple(results),"source_owner_method_binding_authorization_id":source["owner_method_binding_authorization_id"],"source_owner_method_binding_authorization_manifest_hash":source_hash,"source_owner_method_binding_readiness_id":source["source_owner_method_binding_readiness_id"],"source_owner_method_binding_readiness_manifest_hash":source["source_owner_method_binding_readiness_manifest_hash"],"source_owner_construction_id":source["source_owner_construction_id"],"source_owner_construction_manifest_hash":source["source_owner_construction_manifest_hash"],"source_lineage":dict(source["source_lineage"]),"owner_reconstruction_allowed":True,"owner_reconstruction_performed":True,"callable_binding_to_owner_allowed":True,"callable_binding_to_owner_performed":True,"callable_invocation_allowed":False,"callable_invocation_performed":False,"adapter_execution_allowed":False,"adapter_execution_performed":False,"corpus_read_execution_allowed":False,"corpus_read_execution_performed":False,"research_execution_allowed":False,"analytic_conclusion_allowed":False,"forecast_creation_allowed":False,"signals_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"execution_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"market_order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"binding_artifact_persistence_allowed":True,"owner_instances_retained":False,"bound_methods_retained":False}
        serial=dict(body); serial["binding_entries"]=[asdict(e) for e in results]
        result=ProductionOwnerMethodBindingManifest(**body,owner_method_binding_manifest_hash=stable_hash(serial))
        if persist:
            payload=asdict(result); _atomic_write(self.binding_directory/"current.json",payload); _atomic_write(self.binding_directory/"bindings"/f"{binding_id}.json",payload); _atomic_write(self.binding_directory/"workers"/result.worker_id/f"{binding_id}.json",payload)
        return result
