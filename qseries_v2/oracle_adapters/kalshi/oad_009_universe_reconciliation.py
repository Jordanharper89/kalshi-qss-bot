from dataclasses import dataclass
from types import MappingProxyType
from .oad_008_full_universe_discovery import KalshiUniverseSnapshot

OAD_009_BUILD_ID="OAD-009"
OAD_009_REVISION="OAD_009_KALSHI_UNIVERSE_RECONCILIATION_LIFECYCLE_V1"

@dataclass(frozen=True)
class KalshiMarketLifecycleClass:
    ticker:str
    raw_status:str
    lifecycle_class:str
    high_speed_eligible:bool
    surveillance_eligible:bool
    terminal:bool

@dataclass(frozen=True)
class KalshiUniverseReconciliation:
    added:tuple[str,...]
    removed:tuple[str,...]
    changed:tuple[str,...]
    active_fast_lane:tuple[str,...]
    broad_surveillance:tuple[str,...]
    terminal_markets:tuple[str,...]

def classify_market(m):
    s=m.status.lower()
    if s in ("active","open"): return KalshiMarketLifecycleClass(m.ticker,s,"LIVE",True,True,False)
    if s in ("inactive","paused"): return KalshiMarketLifecycleClass(m.ticker,s,"PAUSED",False,True,False)
    if s in ("initialized","unopened"): return KalshiMarketLifecycleClass(m.ticker,s,"PREOPEN",False,True,False)
    if s in ("closed","determined","disputed","amended"): return KalshiMarketLifecycleClass(m.ticker,s,"POST_CLOSE",False,True,False)
    if s in ("finalized","settled"): return KalshiMarketLifecycleClass(m.ticker,s,"TERMINAL",False,False,True)
    return KalshiMarketLifecycleClass(m.ticker,s,"UNKNOWN",False,True,False)

def reconcile_universe(previous,current):
    if not isinstance(previous,KalshiUniverseSnapshot) or not isinstance(current,KalshiUniverseSnapshot):
        raise ValueError("certified universe snapshots required")
    a={m.ticker:m for m in previous.markets}; b={m.ticker:m for m in current.markets}
    added=tuple(sorted(set(b)-set(a))); removed=tuple(sorted(set(a)-set(b)))
    changed=tuple(sorted(k for k in set(a)&set(b) if a[k]!=b[k]))
    classes=tuple(classify_market(m) for m in current.markets)
    fast=tuple(sorted(x.ticker for x in classes if x.high_speed_eligible))
    broad=tuple(sorted(x.ticker for x in classes if x.surveillance_eligible))
    terminal=tuple(sorted(x.ticker for x in classes if x.terminal))
    return KalshiUniverseReconciliation(added,removed,changed,fast,broad,terminal)

def build_oad_009_certification_manifest():
    return MappingProxyType({"build_id":OAD_009_BUILD_ID,"revision":OAD_009_REVISION,
        "two_speed_classification":True,"terminal_markets_excluded_from_live_surveillance":True})

def verify_oad_009_kalshi_universe_reconciliation_lifecycle():
    from .oad_008_full_universe_discovery import build_full_universe_snapshot
    p=build_full_universe_snapshot(({"markets":[{"ticker":"A","event_ticker":"E","status":"active"}],"cursor":""},))
    c=build_full_universe_snapshot(({"markets":[{"ticker":"A","event_ticker":"E","status":"finalized"},{"ticker":"B","event_ticker":"E","status":"active"}],"cursor":""},))
    r=reconcile_universe(p,c)
    return r.added==("B",) and r.active_fast_lane==("B",) and r.terminal_markets==("A",)
