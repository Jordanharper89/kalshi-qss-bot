from __future__ import annotations
from dataclasses import dataclass
import re
from qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import resolve_sport_league
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class ExpandedSportResolution:
 ticker:str;sport:str;league:str;evidence:tuple[str,...]
PATTERNS=(
 ("combat_sports","UFC_MMA",("ufc","mma","fight night","bout","submission","ko/tko")),
 ("boxing","BOXING",("boxing","bout","wbc","wba","ibf","wbo")),
 ("tennis","ATP_WTA",("tennis","atp","wta","set 1","sets won","aces")),
 ("american_football","NCAA_FOOTBALL",("college football","fbs","fcs","ncaa football")),
 ("basketball","NCAA_BASKETBALL",("college basketball","ncaa basketball","march madness")),
 ("soccer","SOCCER",("both teams to score","clean sheet","first half","1st half","draw","tie")),
 ("baseball","MLB",("runs","home run","strikeout","innings","rbi")),
 ("ice_hockey","NHL",("shots on goal","power play","puck","period goals")),
)
def expanded_resolve_sport_league(m):
 b=resolve_sport_league(m)
 if b.league!="UNKNOWN":return ExpandedSportResolution(b.ticker,b.sport,b.league,b.evidence)
 text=" ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")).lower()
 hits=[]
 for sport,league,terms in PATTERNS:
  found=tuple(x for x in terms if x in text)
  if found:hits.append((len(found),sport,league,found))
 if not hits:return ExpandedSportResolution(b.ticker,"sports_unresolved","UNKNOWN",b.evidence)
 hits.sort(key=lambda x:(-x[0],x[1],x[2]));_,sport,league,found=hits[0]
 return ExpandedSportResolution(b.ticker,sport,league,found)
