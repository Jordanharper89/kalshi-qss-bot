from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OAD_008_BUILD_ID="OAD-008"
OAD_008_REVISION="OAD_008_KALSHI_FULL_UNIVERSE_DISCOVERY_V1"
KALSHI_MARKET_FILTERS=("unopened","open","paused","closed","settled")

@dataclass(frozen=True)
class KalshiMarketRecord:
    ticker:str
    event_ticker:str
    status:str
    title:str
    updated_time:str
    exchange_index:int

@dataclass(frozen=True)
class KalshiUniverseSnapshot:
    markets:tuple[KalshiMarketRecord,...]
    statuses:tuple[str,...]
    page_count:int
    complete:bool
    snapshot_hash:str

def build_markets_page_request(cursor=""):
    q={"limit":1000}
    if cursor: q["cursor"]=cursor
    return MappingProxyType(q)

def normalize_market(raw):
    ticker=str(raw.get("ticker","")).strip()
    event=str(raw.get("event_ticker","")).strip()
    status=str(raw.get("status","")).strip().lower()
    if not ticker or not event or not status: raise ValueError("ticker/event_ticker/status required")
    return KalshiMarketRecord(ticker,event,status,str(raw.get("title","")),
                              str(raw.get("updated_time","")),int(raw.get("exchange_index",0)))

def build_full_universe_snapshot(pages):
    records={}
    page_count=0
    terminal=False
    for page in pages:
        page_count+=1
        for raw in page.get("markets",()):
            m=normalize_market(raw)
            if m.ticker in records and records[m.ticker]!=m: raise ValueError("conflicting duplicate market")
            records[m.ticker]=m
        terminal=not bool(page.get("cursor",""))
    if not page_count or not terminal: raise ValueError("complete cursor pagination required")
    markets=tuple(sorted(records.values(),key=lambda x:x.ticker))
    statuses=tuple(sorted({m.status for m in markets}))
    payload=[m.__dict__ for m in markets]
    h=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiUniverseSnapshot(markets,statuses,page_count,True,h)

def build_oad_008_certification_manifest():
    return MappingProxyType({"build_id":OAD_008_BUILD_ID,"revision":OAD_008_REVISION,
        "page_limit":1000,"cursor_pagination":True,"status_filter_omitted_for_full_universe":True})

def verify_oad_008_kalshi_full_universe_discovery():
    pages=({"markets":[{"ticker":"B","event_ticker":"E","status":"active"},{"ticker":"A","event_ticker":"E","status":"initialized"}],"cursor":"NEXT"},
           {"markets":[{"ticker":"C","event_ticker":"E2","status":"finalized"}],"cursor":""})
    s=build_full_universe_snapshot(pages)
    return s.complete and s.page_count==2 and tuple(x.ticker for x in s.markets)==("A","B","C") and build_markets_page_request()["limit"]==1000
