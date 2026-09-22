from __future__ import annotations
from dataclasses import dataclass
import json, hashlib
from pathlib import Path
from .oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord
READ_ONLY=True
EXECUTION_AUTHORITY=False
@dataclass(frozen=True, slots=True)
class VerifiedRuntimeCaseDiscovery:
    files_scanned:int; verified_cases:tuple; rejected_unverified:int; execution_authority:bool=False
def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir(): return q
    raise RuntimeError("repo root not found")
def _records(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            if isinstance(v,(dict,list)): yield from _records(v)
    elif isinstance(obj,list):
        for v in obj: yield from _records(v)
def _case(d):
    low={str(k).lower():v for k,v in d.items()}
    verified=bool(low.get("verified",False)) or str(low.get("outcome_state","")).upper() in ("VERIFIED","OUTCOME_VERIFIED")
    outcome=str(low.get("outcome",low.get("direction",""))).upper()
    source=str(low.get("evidence_source",low.get("source","")))
    if not verified or outcome not in ("UP","DOWN","FLAT") or "SOLANA" not in source.upper(): return None
    case_id=str(low.get("case_id",low.get("id","")))
    h=int(low.get("horizon_seconds",low.get("horizon",0)) or 0)
    if not case_id or h<=0: return None
    ret=float(low.get("return_fraction",low.get("return",0.0)) or 0.0)
    payload={"case_id":case_id,"behavior_type":str(low.get("behavior_type",low.get("event_type","UNKNOWN"))),"protocol":low.get("protocol"),"primary_asset":low.get("primary_asset",low.get("mint")),"secondary_asset":low.get("secondary_asset"),"horizon_seconds":h,"outcome":outcome,"return_fraction":ret,"evidence_source":source,"learning_namespace":"EXISTING_OCL"}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    return SolanaLearnedExperienceRecord("SOLANA-EXP-"+digest[:24],case_id,payload["behavior_type"],payload["protocol"],payload["primary_asset"],payload["secondary_asset"],h,outcome,ret,source,digest,"EXISTING_OCL",False)
def discover_verified_runtime_cases(root=None,max_cases=128):
    r=Path(root or _root()); bases=[r/"runtime_state",r/"runtime"/"oracle_live_shadow"]
    files=0; found=[]; rejected=0; ids=set()
    for base in bases:
        if not base.is_dir(): continue
        for p in list(base.rglob("*.json"))+list(base.rglob("*.jsonl")):
            if "test" in str(p).lower(): continue
            files+=1
            try:
                texts=p.read_text(encoding="utf-8").splitlines() if p.suffix.lower()==".jsonl" else [p.read_text(encoding="utf-8")]
                for text in texts:
                    if not text.strip(): continue
                    obj=json.loads(text)
                    for d in _records(obj):
                        c=_case(d)
                        if c is None:
                            if "outcome" in {str(k).lower() for k in d}: rejected+=1
                            continue
                        if c.experience_id not in ids:
                            ids.add(c.experience_id); found.append(c)
                            if len(found)>=max_cases: return VerifiedRuntimeCaseDiscovery(files,tuple(found),rejected,False)
            except Exception: continue
    return VerifiedRuntimeCaseDiscovery(files,tuple(found),rejected,False)
