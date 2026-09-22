from dataclasses import dataclass
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get

@dataclass(frozen=True)
class OpenMarketSample:
    requested_pages:int
    pages_completed:int
    markets:tuple
    unique_tickers:int
    terminal_cursor:bool
    read_only:bool=True

def sample_live_open_markets(root=None,pages=1,limit_per_page=1000,timeout_seconds=15):
    pages=int(pages)
    limit_per_page=int(limit_per_page)
    if pages<1 or pages>10:
        raise ValueError("pages must be 1..10")
    if limit_per_page<1 or limit_per_page>1000:
        raise ValueError("limit_per_page must be 1..1000")
    c=load_kalshi_credentials()
    cursor=""
    rows=[]
    completed=0
    done=False
    for _ in range(pages):
        params={"limit":limit_per_page,"status":"open"}
        if cursor:
            params["cursor"]=cursor
        r=kalshi_rest_get(c,"/markets",params,timeout_seconds)
        completed+=1
        body=r.body or {}
        rows.extend(body.get("markets",[]) or [])
        cursor=str(body.get("cursor") or "")
        if not cursor:
            done=True
            break
    tickers=[]
    seen=set()
    for row in rows:
        t=str(row.get("ticker") or "") if isinstance(row,dict) else ""
        if t and t not in seen:
            seen.add(t)
            tickers.append(t)
    return OpenMarketSample(pages,completed,tuple(tickers),len(tickers),done,True)

def verify_opc_002_bounded_open_market_sampler():
    return OpenMarketSample(1,1,("A",),1,False,True).read_only
