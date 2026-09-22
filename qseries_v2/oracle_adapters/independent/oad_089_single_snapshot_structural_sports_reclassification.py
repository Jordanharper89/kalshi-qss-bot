from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import snapshot_markets
from qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import deep_classify_market
from qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market
from qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import resolve_sport_league
from qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver import resolve_sports_market_type
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class SportsReclassificationResult:
 market_count:int; baseline_sports:int; structural_sports:int; rescued_from_other:int; unresolved:int; sport_counts:tuple; market_type_counts:tuple

def reclassify_snapshot_with_structural_sports(snapshot):
 markets=snapshot_markets(snapshot); baseline=0; structural=0; rescued=0; unresolved=0
 sports=Counter(); types=Counter()
 for m in markets:
  b=deep_classify_market(m); d=detect_sports_market(m)
  if b.topic=="sports":baseline+=1
  if d.is_sports:
   structural+=1
   if b.topic=="other":rescued+=1
   r=resolve_sport_league(m);t=resolve_sports_market_type(m);sports[(r.sport,r.league)]+=1;types[t.market_type]+=1
  elif b.topic=="other":unresolved+=1
 return SportsReclassificationResult(len(markets),baseline,structural,rescued,unresolved,tuple(sports.most_common()),tuple(types.most_common()))
