from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone

OPC_028_BUILD_ID="OPC-028"
OPC_028_REVISION="OPC_028_LIFECYCLE_AWARE_REFRESH_POLICY_RECERTIFIED"
@dataclass(frozen=True)
class CoverageRefreshTier:
    tier:str; refresh_seconds:int; priority:int; execution_authority:bool=False
def _dt(v):
    if not v:return None
    try:
        d=datetime.fromisoformat(str(v).replace("Z","+00:00")); return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:return None
def classify_market_refresh_tier(market,now=None):
    if not isinstance(market,dict):return CoverageRefreshTier("QUIET",21600,10,False)
    now=now or datetime.now(timezone.utc)
    close=_dt(market.get("close_time") or market.get("expiration_time"))
    if close:
        sec=(close-now).total_seconds()
        if sec<=3600:return CoverageRefreshTier("SETTLEMENT_IMMINENT",60,120,False)
        if sec<=21600:return CoverageRefreshTier("CLOSING_SOON",300,110,False)
        if sec<=86400:return CoverageRefreshTier("PRE_SETTLEMENT",900,100,False)
    volume=float(market.get("volume_fp") or market.get("volume") or 0); v24=float(market.get("volume_24h_fp") or market.get("volume_24h") or 0); oi=float(market.get("open_interest_fp") or market.get("open_interest") or 0)
    if v24>=10000 or volume>=10000:return CoverageRefreshTier("ULTRA_HOT",60,100,False)
    if v24>=1000 or volume>=1000:return CoverageRefreshTier("HOT",300,80,False)
    if v24>0 or volume>0 or oi>0:return CoverageRefreshTier("ACTIVE",1800,50,False)
    return CoverageRefreshTier("QUIET",21600,10,False)
def rank_markets_by_refresh_priority(markets,now=None):
    rows=[]
    for row in markets:
        if not isinstance(row,dict) or not row.get("ticker"):continue
        tier=classify_market_refresh_tier(row,now); rows.append((tier.priority,str(row["ticker"]),tier))
    rows.sort(key=lambda x:(-x[0],x[1])); return tuple((t,tier) for _,t,tier in rows)
def verify_opc_028_activity_tier_refresh_policy():
    now=datetime(2026,8,27,12,0,tzinfo=timezone.utc)
    a=classify_market_refresh_tier({"close_time":"2026-08-27T12:30:00Z"},now)
    b=classify_market_refresh_tier({"close_time":"2026-08-27T16:00:00Z"},now)
    c=classify_market_refresh_tier({"volume_24h":20000},now)
    return a.tier=="SETTLEMENT_IMMINENT" and b.tier=="CLOSING_SOON" and c.tier=="ULTRA_HOT" and not a.execution_authority
