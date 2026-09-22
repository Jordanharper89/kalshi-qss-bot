from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort,snapshot_markets
from qseries_v2.oracle_adapters.independent.oad_092_expanded_structural_sport_league_resolver import expanded_resolve_sport_league
from qseries_v2.oracle_adapters.independent.oad_094_expanded_universal_domain_classifier import expanded_domain_classify
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
SOURCE_DEMAND={
 "sports":("SPORT_SPECIFIC",),
 "macroeconomics":("BLS","BEA","Federal Reserve/FRED"),
 "politics_elections":("Official election authorities","FEC"),
 "corporate_finance":("SEC EDGAR","Issuer investor relations"),
 "crypto":("Coinbase/chain RPC/indexers",),
 "weather":("NWS/NOAA",),
 "energy_commodities":("EIA","USDA"),
 "legal_regulatory":("Federal Register","CourtListener/official courts"),
 "health":("CDC","FDA"),
 "transport":("FAA","TSA","Maritime/port authorities"),
 "science_space":("NASA",),
 "geopolitics":("State/Defense/UN official releases",),
 "technology":("Issuer official releases","SEC EDGAR"),
 "entertainment_awards":("Official award/event organizations",),
}
SPORT_SOURCES={
 "NHL":("NHL official game/stat sources",),"MLB":("MLB official game/stat sources",),
 "SOCCER":("Competition/club official match sources",),"ATP_WTA":("ATP/WTA official tournament/result sources",),
 "UFC_MMA":("UFC/commission official bout/result sources",),"BOXING":("Sanctioning-body/commission official bout sources",),
 "NFL":("NFL official game/stat/injury sources",),"NCAA_FOOTBALL":("NCAA/conference/team official sources",),
 "NBA":("NBA official game/stat/injury sources",),"WNBA":("WNBA official game/stat/injury sources",),
 "NCAA_BASKETBALL":("NCAA/conference/team official basketball sources",),
 "UNKNOWN":("Sport-specific authoritative source unresolved",),
}
@dataclass(frozen=True,slots=True)
class UniversalPriority:
 rank:int;domain:str;subdomain:str;live_markets:int;source_families:tuple[str,...]
@dataclass(frozen=True,slots=True)
class UniversalGate:
 snapshot_id:str;evaluated_markets:int;unresolved:int;priorities:tuple[UniversalPriority,...]
def build_universal_source_demand_gate(limit=1000):
 s=capture_current_market_cohort(limit);c=Counter()
 for m in snapshot_markets(s):
  d=expanded_domain_classify(m)
  if d.domain=="sports":
   r=expanded_resolve_sport_league(m);c[("sports",r.league)]+=1
  else:c[(d.domain,"")]+=1
 unresolved=c.get(("other",""),0);rows=[]
 for (domain,sub),count in c.items():
  if domain=="other":continue
  src=SPORT_SOURCES.get(sub,()) if domain=="sports" else SOURCE_DEMAND.get(domain,())
  rows.append((count,domain,sub,src))
 rows.sort(key=lambda x:(-x[0],x[1],x[2]))
 return UniversalGate(s.snapshot_id,s.market_count,unresolved,tuple(UniversalPriority(i+1,d,sub,n,src) for i,(n,d,sub,src) in enumerate(rows)))
