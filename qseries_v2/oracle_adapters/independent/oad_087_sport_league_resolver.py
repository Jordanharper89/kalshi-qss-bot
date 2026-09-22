from __future__ import annotations
from dataclasses import dataclass
import re
from qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class SportLeagueResolution:
 ticker:str; sport:str; league:str; evidence:tuple[str,...]

RULES=(
 ("american_football","NFL",("NFL","touchdown","passing yards","rushing yards")),
 ("american_football","NCAA_FOOTBALL",("NCAAF","college football")),
 ("basketball","NBA",("NBA","rebounds","assists","three pointers")),
 ("basketball","WNBA",("WNBA",)),
 ("baseball","MLB",("MLB","home runs","strikeouts","runs","innings")),
 ("ice_hockey","NHL",("NHL","goals","shots on goal")),
 ("tennis","ATP_WTA",("ATP","WTA","sets","aces","break points")),
 ("combat_sports","UFC_MMA",("UFC","MMA","submission","knockout","round")),
 ("boxing","BOXING",("boxing","bout","knockout")),
 ("soccer","SOCCER",("both teams to score","champions league","premier league","la liga","bundesliga","serie a","ligue 1","mls","goals")),
)
def _text(m):return " ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","series_ticker","title","subtitle","rules_primary","rules_secondary"))
def resolve_sport_league(m):
 d=detect_sports_market(m); text=_text(m); low=text.lower(); upper=text.upper()
 if not d.is_sports:return SportLeagueResolution(d.ticker,"non_sports","NONE",())
 hits=[]
 for sport,league,terms in RULES:
  found=tuple(x for x in terms if (x in upper if x.isupper() else x.lower() in low))
  if found:hits.append((len(found),sport,league,found))
 if not hits:return SportLeagueResolution(d.ticker,"sports_unresolved","UNKNOWN",d.signals)
 hits.sort(key=lambda x:(-x[0],x[1],x[2]));_,sport,league,found=hits[0]
 return SportLeagueResolution(d.ticker,sport,league,tuple(found))
