from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime,timezone
import json
from .olf_006_structural_identity import resolve_structural_identity
from .olf_013_behavior_patterns import materialize_behavior_patterns

OLF_014_BUILD_ID="OLF-014"
OLF_014_REVISION="OLF_014_CONDITION_AWARE_EXPERIENCE_RESOLVER_V1"

@dataclass(frozen=True)
class ConditionAwareExperience:
    market_ticker:str
    series_key:str
    available:bool
    pattern_id:str
    observation_type:str
    samples:int
    pattern_support:float
    condition_similarity:float
    relationship_strength:float
    learner_state_hash:str
    reason:str
    directional_signal_available:bool=False
    execution_authority:bool=False

def _session(v):
    if not v:return "UNKNOWN"
    try:
        x=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        if x.tzinfo is None:x=x.replace(tzinfo=timezone.utc)
        h=x.astimezone(timezone.utc).hour
        return "UTC_00_05" if h<6 else "UTC_06_11" if h<12 else "UTC_12_17" if h<18 else "UTC_18_23"
    except Exception:return "UNKNOWN"

def resolve_condition_aware_experience(root=None,market_ticker="",source_rows=()):
    root=Path(root or Path.cwd()).resolve();ident=resolve_structural_identity(market_ticker)
    payload=materialize_behavior_patterns(root,3);rows=tuple(source_rows)
    types=set();sessions=set()
    for row in rows:
        if hasattr(row,"source_row"):row=row.source_row
        if not isinstance(row,dict):continue
        types.add(str(row.get("observation_type") or row.get("event_type") or "UNKNOWN").upper())
        sessions.add(_session(row.get("observed_at") or row.get("event_ts") or row.get("created_at")))
    candidates=[]
    for p in payload.get("patterns",[]):
        if p.get("series_key")!=ident.series_key:continue
        type_match=1.0 if str(p.get("observation_type")) in types else 0.0
        session_match=1.0 if str(p.get("dominant_utc_session")) in sessions else 0.0
        similarity=.80*type_match+.20*session_match
        if similarity<=0:continue
        strength=.75*similarity*float(p.get("support",0.0))
        candidates.append((strength,similarity,p))
    if not candidates:
        return ConditionAwareExperience(ident.market_ticker,ident.series_key,False,"","UNKNOWN",0,0.0,0.0,0.0,str(payload.get("learner_state_hash") or ""),"NO_MATCHING_HISTORICAL_CONDITIONS",False,False)
    strength,similarity,p=max(candidates,key=lambda x:(x[0],x[2]["samples"],x[2]["pattern_id"]))
    return ConditionAwareExperience(
        ident.market_ticker,ident.series_key,True,str(p["pattern_id"]),str(p["observation_type"]),
        int(p["samples"]),float(p["support"]),float(similarity),float(strength),
        str(payload.get("learner_state_hash") or ""),"MATCHED_EVIDENCE_GROUNDED_PATTERN",False,False
    )

def verify_olf_014_condition_aware_experience_resolver():
    return OLF_014_BUILD_ID=="OLF-014" and callable(resolve_condition_aware_experience)
