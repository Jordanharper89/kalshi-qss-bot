from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib,json

OLR_036_BUILD_ID="OLR-036"
OLR_036_REVISION="OLR_036_OUTCOME_EVIDENCE_LINKAGE_FOUNDATION_V1"

@dataclass(frozen=True)
class OutcomeEvidenceKey:
    market_id:str
    ticker:str
    observation_id:str|None
    settled_at:str|None

def normalize_text(value):
    return "" if value is None else str(value).strip()

def build_outcome_evidence_key(record):
    getter=record.get if hasattr(record,"get") else lambda k,d=None:getattr(record,k,d)
    market_id=normalize_text(getter("market_id","") or getter("market_ticker","") or getter("ticker",""))
    ticker=normalize_text(getter("ticker","") or getter("market_ticker","") or market_id)
    observation_id=normalize_text(getter("observation_id","")) or None
    settled_at=normalize_text(getter("settled_at","") or getter("resolved_at","")) or None
    return OutcomeEvidenceKey(market_id,ticker,observation_id,settled_at)

def deterministic_linkage_id(key):
    payload=json.dumps(key.__dict__,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()

def verify_olr_036_outcome_evidence_linkage_foundation(root=None):
    k=build_outcome_evidence_key({"ticker":"KXTEST","observation_id":"abc"})
    return OLR_036_BUILD_ID=="OLR-036" and k.market_id=="KXTEST" and len(deterministic_linkage_id(k))==64
