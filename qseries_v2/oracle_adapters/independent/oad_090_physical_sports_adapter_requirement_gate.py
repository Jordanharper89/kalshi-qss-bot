from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort,snapshot_markets
from qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market
from qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import resolve_sport_league
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False

SOURCE_BY_LEAGUE={
 "NFL":("NFL official game/stat/injury sources",),
 "NCAA_FOOTBALL":("NCAA/conference/team official sources",),
 "NBA":("NBA official game/stat/injury sources",),
 "WNBA":("WNBA official game/stat/injury sources",),
 "MLB":("MLB official game/stat sources",),
 "NHL":("NHL official game/stat sources",),
 "ATP_WTA":("ATP/WTA official tournament/result sources",),
 "UFC_MMA":("UFC/commission official bout/result sources",),
 "BOXING":("Sanctioning-body/commission official bout sources",),
 "SOCCER":("Competition/club official match sources",),
 "UNKNOWN":("Sport-specific authoritative source unresolved",),
}
@dataclass(frozen=True,slots=True)
class SportsAdapterRequirement:
 rank:int;sport:str;league:str;live_markets:int;source_families:tuple[str,...]

def build_sports_adapter_requirements(limit=1000):
 s=capture_current_market_cohort(limit);c=Counter()
 for m in snapshot_markets(s):
  if detect_sports_market(m).is_sports:
   r=resolve_sport_league(m);c[(r.sport,r.league)]+=1
 rows=[]
 for i,((sport,league),count) in enumerate(sorted(c.items(),key=lambda kv:(-kv[1],kv[0])),1):
  rows.append(SportsAdapterRequirement(i,sport,league,count,SOURCE_BY_LEAGUE.get(league,SOURCE_BY_LEAGUE["UNKNOWN"])))
 return s,tuple(rows)
