from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class SportsMarketType:
 ticker:str; market_type:str; signals:tuple[str,...]

RULES=(
 ("both_teams_to_score",("both teams to score",)),
 ("spread",("wins by over","spread")),
 ("total",("over ","under ","total points","total runs","total goals")),
 ("player_prop",("home runs","strikeouts","rebounds","assists","yards","touchdown","points scored")),
 ("team_prop",("team total","goals scored","runs scored")),
 ("match_winner",("moneyline"," to win","wins the match","wins the game")),
 ("tournament_advancement",("round of 16","quarterfinal","semifinal","advance","qualify")),
)
def resolve_sports_market_type(m):
 d=detect_sports_market(m)
 if not d.is_sports:return SportsMarketType(d.ticker,"non_sports",())
 text=" ".join(str(m.get(k,"") or "") for k in ("title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")).lower()
 hits=[]
 for typ,terms in RULES:
  found=tuple(x for x in terms if x in text)
  if found:hits.append((len(found),typ,found))
 if not hits:return SportsMarketType(d.ticker,"sports_other",d.signals)
 hits.sort(key=lambda x:(-x[0],x[1]));_,typ,found=hits[0]
 return SportsMarketType(d.ticker,typ,found)
