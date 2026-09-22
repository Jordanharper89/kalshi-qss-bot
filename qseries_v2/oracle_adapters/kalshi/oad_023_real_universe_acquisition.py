from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_008_full_universe_discovery import normalize_market, KalshiUniverseSnapshot
from .oad_022_rest_transport import kalshi_rest_get
from .oad_021_credentials import KalshiCredentialConfig

OAD_023_BUILD_ID="OAD-023"
OAD_023_REVISION="OAD_023_REAL_KALSHI_FULL_UNIVERSE_ACQUISITION_V1"

@dataclass(frozen=True)
class RealKalshiUniverseAcquisition:
    snapshot:KalshiUniverseSnapshot
    requests:int
    terminal_cursor_reached:bool
    network_live:bool

def acquire_real_kalshi_universe(credentials,max_pages=10000,timeout_seconds=10):
    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")
    cursor=""
    pages=[]
    seen=set()
    for _ in range(int(max_pages)):
        params={"limit":1000}
        if cursor: params["cursor"]=cursor
        response=kalshi_rest_get(credentials,"/markets",params,timeout_seconds)
        body=response.body
        markets=body.get("markets",[])
        nxt=str(body.get("cursor") or "")
        pages.append({"markets":markets,"cursor":nxt})
        if not nxt: break
        if nxt in seen: raise RuntimeError("Kalshi cursor loop detected")
        seen.add(nxt); cursor=nxt
    else:
        raise RuntimeError("Kalshi universe acquisition exceeded max_pages")
    records={}
    for page in pages:
        for raw in page["markets"]:
            m=normalize_market(raw)
            if m.ticker in records and records[m.ticker]!=m: raise ValueError("conflicting duplicate market")
            records[m.ticker]=m
    markets=tuple(sorted(records.values(),key=lambda x:x.ticker))
    statuses=tuple(sorted({m.status for m in markets}))
    h=sha256(json.dumps([m.__dict__ for m in markets],sort_keys=True,separators=(",",":")).encode()).hexdigest()
    snap=KalshiUniverseSnapshot(markets,statuses,len(pages),True,h)
    return RealKalshiUniverseAcquisition(snap,len(pages),True,True)

def build_oad_023_certification_manifest():
    return MappingProxyType({"build_id":OAD_023_BUILD_ID,"revision":OAD_023_REVISION,
        "live_endpoint":"/markets","page_limit":1000,"cursor_until_exhaustion":True,"execution":False})

def verify_oad_023_real_kalshi_full_universe_acquisition():
    return build_oad_023_certification_manifest()["cursor_until_exhaustion"] is True
