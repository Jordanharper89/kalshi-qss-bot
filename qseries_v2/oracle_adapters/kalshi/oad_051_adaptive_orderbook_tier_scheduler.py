from __future__ import annotations
from dataclasses import dataclass

OAD_051_BUILD_ID="OAD-051"
OAD_051_REVISION="OAD_051_ADAPTIVE_ORDERBOOK_TIER_SCHEDULER_V1"

TIER_PRIORITY={"ULTRA_HOT":100,"HOT":90,"ACTIVE":70,"WARM":40,"COLD":20,"DORMANT":10,"DEAD":0}

@dataclass(frozen=True)
class OrderbookTierPlan:
    active_tickers:tuple[str,...]
    standby_tickers:tuple[str,...]
    excluded_tickers:tuple[str,...]
    max_active_markets:int

def build_adaptive_orderbook_tier_plan(tier_by_ticker,max_active_markets=300):
    limit=int(max_active_markets)
    if limit<1:
        raise ValueError("max_active_markets must be positive")
    ranked=[]
    excluded=[]
    for ticker,tier in dict(tier_by_ticker).items():
        ticker=str(ticker).strip()
        tier=str(tier).upper()
        if not ticker:
            continue
        if tier not in TIER_PRIORITY:
            raise ValueError("unknown surveillance tier: "+tier)
        if tier=="DEAD":
            excluded.append(ticker)
        else:
            ranked.append((TIER_PRIORITY[tier],ticker,tier))
    ranked.sort(key=lambda x:(-x[0],x[1]))
    active=tuple(x[1] for x in ranked[:limit])
    standby=tuple(x[1] for x in ranked[limit:])
    return OrderbookTierPlan(active,standby,tuple(sorted(excluded)),limit)

def verify_oad_051_adaptive_orderbook_tier_scheduler():
    p=build_adaptive_orderbook_tier_plan({"B":"ACTIVE","A":"HOT","C":"DEAD"},1)
    return p.active_tickers==("A",) and p.standby_tickers==("B",) and p.excluded_tickers==("C",)
