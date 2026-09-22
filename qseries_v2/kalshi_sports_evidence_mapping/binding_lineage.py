from dataclasses import dataclass
import hashlib,json

@dataclass(frozen=True)
class BindingLineage:
    lineage_id:str
    ticker:str
    proposition_type:str
    league:str
    canonical_event_id:str|None
    binding_status:str
    source_modules:tuple
    reasons:tuple
    execution_authority:bool=False

def make_lineage(*,ticker,proposition_type,league,canonical_event_id,binding_status,source_modules=(),reasons=()):
    payload={"ticker":str(ticker),"proposition_type":str(proposition_type),"league":str(league),"canonical_event_id":canonical_event_id,"binding_status":str(binding_status),"source_modules":tuple(source_modules),"reasons":tuple(reasons)}
    lid=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return BindingLineage(lid,payload["ticker"],payload["proposition_type"],payload["league"],canonical_event_id,payload["binding_status"],payload["source_modules"],payload["reasons"],False)
