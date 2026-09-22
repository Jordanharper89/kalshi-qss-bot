from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .opc_028_activity_tier_refresh_policy import classify_market_refresh_tier
OPC_026_BUILD_ID="OPC-026"; OPC_026_REVISION="OPC_026_FRESHNESS_LIFECYCLE_ADMISSION_RECERTIFIED"
@dataclass(frozen=True)
class FullPageCoverageAdmission:
    page_markets:int; already_covered:int; missing_markets:int; admitted_tickers:tuple; full_page_mode:bool=True; execution_authority:bool=False
def _utc(v):
    if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if v:return datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return None
def admit_full_page_coverage(markets,recent_tickers=None,*,freshness=None,now=None):
    now=now or datetime.now(timezone.utc); recent={str(x) for x in (recent_tickers or ())}; freshness=freshness or {}
    admitted=[]; covered=0; seen=set()
    for row in markets:
        if not isinstance(row,dict):continue
        ticker=str(row.get("ticker") or "")
        if not ticker or ticker in seen:continue
        seen.add(ticker); tier=classify_market_refresh_tier(row,now); last=_utc(freshness.get(ticker))
        fresh=bool(last and (now-last).total_seconds() < tier.refresh_seconds)
        if freshness:
            if fresh:covered+=1
            else:admitted.append((tier.priority,ticker))
        elif ticker in recent:covered+=1
        else:admitted.append((tier.priority,ticker))
    admitted.sort(key=lambda x:(-x[0],x[1]))
    tickers=tuple(t for _,t in admitted)
    return FullPageCoverageAdmission(len(seen),covered,len(tickers),tickers,True,False)
def verify_opc_026_full_page_coverage_admission():
    now=datetime(2026,8,27,12,tzinfo=timezone.utc)
    rows=({"ticker":"KXSOON","close_time":"2026-08-27T12:30:00Z"},{"ticker":"KXLATER","close_time":"2026-08-29T12:00:00Z"})
    x=admit_full_page_coverage(rows,freshness={"KXSOON":"2026-08-27T11:58:00Z","KXLATER":"2026-08-27T11:58:00Z"},now=now)
    return x.admitted_tickers==("KXSOON",) and x.already_covered==1 and not x.execution_authority
