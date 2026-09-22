from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import snapshot_markets
from qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market
from qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import resolve_sport_league
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
FIELDS=("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")
@dataclass(frozen=True,slots=True)
class UnresolvedSportsAudit:
 count:int;field_nonempty:tuple;series_prefixes:tuple;samples:tuple
def audit_unresolved_sports(snapshot,sample_limit=30):
 rows=[];non=Counter();prefix=Counter()
 for m in snapshot_markets(snapshot):
  if not detect_sports_market(m).is_sports:continue
  if resolve_sport_league(m).league!="UNKNOWN":continue
  rows.append(m)
  for f in FIELDS:
   if str(m.get(f,"") or "").strip():non[f]+=1
  raw=str(m.get("series_ticker","") or m.get("event_ticker","") or m.get("ticker",""))
  token=raw.split("-")[0][:40]
  if token:prefix[token]+=1
 samples=tuple((str(m.get("ticker","")),str(m.get("series_ticker","")),str(m.get("event_ticker","")),str(m.get("title",""))[:220]) for m in rows[:sample_limit])
 return UnresolvedSportsAudit(len(rows),tuple(non.most_common()),tuple(prefix.most_common(30)),samples)
