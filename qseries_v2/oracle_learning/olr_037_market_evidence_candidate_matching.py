from __future__ import annotations
from dataclasses import dataclass
from .olr_036_outcome_evidence_linkage_foundation import build_outcome_evidence_key,normalize_text
OLR_037_BUILD_ID="OLR-037"
OLR_037_REVISION="OLR_037_MARKET_EVIDENCE_CANDIDATE_MATCHING_V1"

@dataclass(frozen=True)
class EvidenceMatch:
    matched:bool
    method:str
    score:int
    candidate:object|None

def _get(obj,key,default=None):
    if hasattr(obj,"get"):return obj.get(key,default)
    return getattr(obj,key,default)

def score_candidate(outcome,candidate):
    key=build_outcome_evidence_key(outcome)
    score=0
    obs=normalize_text(_get(candidate,"observation_id",""))
    ticker=normalize_text(_get(candidate,"ticker","") or _get(candidate,"market_ticker",""))
    market=normalize_text(_get(candidate,"market_id","") or ticker)
    if key.observation_id and obs==key.observation_id:score+=100
    if key.ticker and ticker==key.ticker:score+=50
    if key.market_id and market==key.market_id:score+=50
    return score

def match_outcome_to_evidence(outcome,candidates):
    ranked=sorted(((score_candidate(outcome,c),c) for c in candidates),key=lambda x:x[0],reverse=True)
    if not ranked or ranked[0][0]<=0:return EvidenceMatch(False,"NONE",0,None)
    score,candidate=ranked[0]
    method="OBSERVATION_ID" if score>=100 and build_outcome_evidence_key(outcome).observation_id else "MARKET_ID"
    return EvidenceMatch(True,method,score,candidate)

def verify_olr_037_market_evidence_candidate_matching(root=None):
    m=match_outcome_to_evidence({"ticker":"X"},[{"ticker":"X"}])
    return OLR_037_BUILD_ID=="OLR-037" and m.matched and m.score>=50
