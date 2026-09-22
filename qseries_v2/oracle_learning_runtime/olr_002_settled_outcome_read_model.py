from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import json
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
OLR_002_BUILD_ID="OLR-002"
OLR_002_REVISION="OLR_002_KALSHI_SETTLED_OUTCOME_READ_MODEL_V1"

@dataclass(frozen=True)
class SettledMarketOutcome:
    ticker:str
    result:str
    settlement_ts:str
    source_hash:str
    raw:dict

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def normalize_settled_market(market):
    m=dict(market)
    ticker=str(m.get("ticker") or "").strip()
    result=str(m.get("result") or "").lower().strip()
    ts=str(m.get("settlement_ts") or m.get("settled_ts") or m.get("settled_time") or "").strip()
    if not ticker or result not in ("yes","no","scalar") or not ts:
        return None
    return SettledMarketOutcome(ticker,result,ts,_h(m),m)

def fetch_recent_settled_markets(root=None,limit=100):
    root=Path(root or Path.cwd()).resolve()
    c=load_kalshi_credentials(root=root)
    r=kalshi_rest_get(c,"/markets",{"limit":max(1,min(int(limit),1000)),"status":"settled"},10)
    rows=tuple(x for x in (normalize_settled_market(m) for m in r.body.get("markets",())) if x is not None)
    return tuple(sorted(rows,key=lambda x:(x.settlement_ts,x.ticker)))

def verify_olr_002_kalshi_settled_outcome_read_model():
    x=normalize_settled_market({"ticker":"KXTEST","result":"yes","settlement_ts":"2026-08-14T00:00:00Z"})
    return x is not None and x.result=="yes" and len(x.source_hash)==64
