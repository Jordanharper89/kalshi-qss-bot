from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort, snapshot_markets
from qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import decompose_mixed_market

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

SPORT_SOURCES={
 "NHL":("NHL official game/stat sources",),
 "MLB":("MLB official game/stat sources",),
 "SOCCER":("Competition/club official match sources",),
 "ATP_WTA":("ATP/WTA official tournament/result sources",),
 "UFC_MMA":("UFC/commission official bout/result sources",),
 "BOXING":("Sanctioning-body/commission official bout sources",),
 "NFL":("NFL official game/stat/injury sources",),
 "NCAA_FOOTBALL":("NCAA/conference/team official sources",),
 "NBA":("NBA official game/stat/injury sources",),
 "WNBA":("WNBA official game/stat/injury sources",),
 "NCAA_BASKETBALL":("NCAA/conference/team official basketball sources",),
 "UNKNOWN":("Sport-specific authoritative source unresolved",),
}
DOMAIN_SOURCES={
 "financial_markets":("Independent underlying asset/reference-price source",),
 "macroeconomics":("BLS","BEA","Federal Reserve/FRED"),
 "politics_elections":("Official election authorities","FEC"),
 "corporate_finance":("SEC EDGAR","Issuer investor relations"),
 "crypto":("Coinbase/chain RPC/indexers",),
 "weather":("NWS/NOAA",),
 "energy_commodities":("EIA","USDA"),
 "legal_regulatory":("Federal Register","Official courts"),
 "health":("CDC","FDA"),
 "transport":("FAA","TSA","Maritime/port authorities"),
 "science_space":("NASA",),
 "geopolitics":("State/Defense/UN official releases",),
 "technology":("Issuer official releases","SEC EDGAR"),
 "entertainment_awards":("Official award/event organizations",),
}

@dataclass(frozen=True, slots=True)
class DemandRow:
    rank:int
    domain:str
    subdomain:str
    legs:int
    source_families:tuple[str,...]

@dataclass(frozen=True, slots=True)
class FinalDecompositionGate:
    snapshot_id:str
    markets:int
    legs:int
    unresolved_legs:int
    sports_none:int
    demand_without_source:int
    priorities:tuple[DemandRow,...]

def final_decomposition_source_demand_gate(limit=1000):
    snap=capture_current_market_cohort(limit)
    counts=Counter(); unresolved=0; sports_none=0
    for market in snapshot_markets(snap):
        legs=decompose_mixed_market(market)
        if not legs:
            unresolved += 1
            continue
        for leg in legs:
            if leg.state=="UNRESOLVED":
                unresolved += 1
            if leg.domain=="sports" and leg.subdomain in ("","NONE"):
                sports_none += 1
            counts[(leg.domain,leg.subdomain)] += 1
    raw=[]
    no_source=0
    for (domain,sub),n in counts.items():
        if domain=="other":
            continue
        sources=SPORT_SOURCES.get(sub,()) if domain=="sports" else DOMAIN_SOURCES.get(domain,())
        if not sources:
            no_source += n
        raw.append((n,domain,sub,sources))
    raw.sort(key=lambda x:(-x[0],x[1],x[2]))
    rows=tuple(DemandRow(i+1,d,s,n,src) for i,(n,d,s,src) in enumerate(raw))
    return FinalDecompositionGate(snap.snapshot_id,snap.market_count,sum(counts.values()),unresolved,sports_none,no_source,rows)
