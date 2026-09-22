from __future__ import annotations
from collections import Counter,defaultdict
from dataclasses import dataclass

from qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import classify_snapshot

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

EXISTING_FAMILIES={
 "weather":("NWS/NOAA",),
 "legal_regulatory":("Federal Register",),
 "geological":("USGS",),
}
MISSING_FAMILIES={
 "sports":("Official league/team feeds",),
 "crypto":("Coinbase/chain RPC/indexers",),
 "macroeconomics":("BLS","BEA","Federal Reserve/FRED"),
 "politics_elections":("Official election authorities","FEC"),
 "corporate_finance":("SEC EDGAR","Issuer investor relations"),
 "energy_commodities":("EIA","USDA"),
 "legal_regulatory":("CourtListener/official courts",),
 "health":("CDC","FDA"),
 "transport":("FAA","TSA","Maritime/port authorities"),
 "science_space":("NASA",),
 "geopolitics":("State/Defense/UN official releases",),
 "entertainment_awards":("Official award/event organizations",),
 "technology":("Issuer official releases","SEC EDGAR"),
}

@dataclass(frozen=True,slots=True)
class SourceDemand:
    topic:str
    live_markets:int
    existing_families:tuple[str,...]
    missing_families:tuple[str,...]
    state:str

def source_demand_from_snapshot(snapshot):
    rows,counts=classify_snapshot(snapshot)
    out=[]
    for topic,count in counts:
        if topic=="other":
            out.append(SourceDemand(topic,count,(),(),"UNMAPPED"))
            continue
        existing=EXISTING_FAMILIES.get(topic,())
        missing=MISSING_FAMILIES.get(topic,())
        state="NOT_COVERED" if missing else ("COVERED" if existing else "UNMAPPED")
        out.append(SourceDemand(topic,count,existing,missing,state))
    return tuple(sorted(out,key=lambda x:(-x.live_markets,x.topic)))
