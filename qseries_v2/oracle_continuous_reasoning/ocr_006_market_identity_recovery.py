from __future__ import annotations
from dataclasses import dataclass
import json,re

OCR_006_BUILD_ID="OCR-006"
OCR_006_REVISION="OCR_006_CANONICAL_MARKET_IDENTITY_RECOVERY_V1"
KALSHI_RE=re.compile(r"\bKX[A-Z0-9][A-Z0-9\-]*\b",re.I)

@dataclass(frozen=True)
class RecoveredMarketIdentity:
    observation_id:str
    market_ticker:str
    venue:str
    recovery_path:str
    recovered:bool=True

def _json_or_value(v):
    if isinstance(v,str):
        s=v.strip()
        if s and s[0] in "[{\"":
            try:return json.loads(s)
            except Exception:return v
    return v

def _walk(value,path="$"):
    value=_json_or_value(value)
    if isinstance(value,dict):
        preferred=("market_ticker","ticker","source_market_id","venue_market_id","market_id")
        for k in preferred:
            if k in value:
                v=str(value[k]).strip()
                if KALSHI_RE.fullmatch(v):return v,path+"."+k
        for k in sorted(value):
            got=_walk(value[k],path+"."+str(k))
            if got:return got
    elif isinstance(value,(list,tuple)):
        for i,v in enumerate(value):
            got=_walk(v,f"{path}[{i}]")
            if got:return got
    elif isinstance(value,str):
        m=KALSHI_RE.search(value)
        if m:return m.group(0),path
    return None

def recover_market_identity(row):
    row=dict(row)
    oid=str(row.get("observation_id") or row.get("id") or "").strip()
    if not oid:raise ValueError("observation_id required")
    got=_walk(row)
    if not got:return RecoveredMarketIdentity(oid,"","kalshi","unresolved",False)
    ticker,path=got
    return RecoveredMarketIdentity(oid,ticker.upper(),"kalshi",path,True)

def recover_batch_market_identities(rows):
    return tuple(recover_market_identity(r) for r in rows)

def verify_ocr_006_canonical_market_identity_recovery():
    x=recover_market_identity({"observation_id":"o","payload":{"msg":{"market_ticker":"KXBTC15M-TEST"}}})
    return x.recovered and x.market_ticker=="KXBTC15M-TEST"
