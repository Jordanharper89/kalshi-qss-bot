from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import hashlib,json
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state
OHE_001_BUILD_ID="OHE-001";OHE_001_REVISION="OHE_001_HISTORICAL_EXPERIENCE_READ_MODEL_V1"
ATTESTATION_NAME="oracle_learning_breadth_reasoning_attestation.json"
@dataclass(frozen=True)
class HistoricalExperienceContext:
    market_ticker:str;series_key:str;maturity:str;series_admitted:bool;experience_available:bool;regime_id:str;reliability:float;learner_state_hash:str;reason:str
@dataclass(frozen=True)
class HistoricalExperienceReadModel:
    cycles:int;outcomes_learned:int;learned_records:int;learner_state_hash:str;attestation_state_hash:str;attestation_hash:str;lineage_current:bool;markets_reasoned:int;experience_contexts:int;withheld_contexts:int;blind_contexts:int;learned_market_counts:tuple;learned_family_counts:tuple;contexts:tuple;read_only:bool=True;execution_authority:bool=False
def _load_json(path):
    p=Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
def _family(t):return str(t or "").split("-",1)[0] or "UNKNOWN"
def _ctx(r):
    return HistoricalExperienceContext(str(r.get("market_ticker") or ""),str(r.get("series_key") or ""),str(r.get("maturity") or "BLIND"),bool(r.get("series_admitted",False)),bool(r.get("experience_available",False)),str(r.get("regime_id") or ""),float(r.get("reliability") or 0.0),str(r.get("learner_state_hash") or ""),str(r.get("reason") or ""))
def load_historical_experience_read_model(root=None):
    root=Path(root or Path.cwd()).resolve();learned=load_production_learned_state(root)
    ap=root/"runtime_state"/ATTESTATION_NAME;att=_load_json(ap);raw=att.get("contexts",[]) if isinstance(att,dict) else []
    if not isinstance(raw,list):raw=[]
    contexts=tuple(_ctx(x) for x in raw if isinstance(x,dict));families=Counter()
    for ticker,count in learned.learned_market_counts:families[_family(ticker)]+=int(count)
    ah=str(att.get("learner_state_hash") or "") if isinstance(att,dict) else ""
    return HistoricalExperienceReadModel(int(learned.cycles),int(learned.outcomes_learned),int(learned.learned_records),str(learned.learner_state_hash),ah,hashlib.sha256(ap.read_bytes()).hexdigest() if ap.is_file() else "",bool(ah and ah==str(learned.learner_state_hash)),int(att.get("markets_reasoned",0)) if isinstance(att,dict) else 0,int(att.get("experience_contexts",0)) if isinstance(att,dict) else 0,int(att.get("withheld_contexts",0)) if isinstance(att,dict) else 0,int(att.get("blind_contexts",0)) if isinstance(att,dict) else 0,tuple(learned.learned_market_counts),tuple(sorted(families.items())),contexts,True,False)
def verify_historical_experience_read_model(x):
    if not x.read_only or x.execution_authority:raise RuntimeError("OHE read-only boundary violation")
    if x.learned_records<0 or x.outcomes_learned<0:raise RuntimeError("invalid learner counts")
    return True
