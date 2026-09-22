from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import snapshot_markets
from qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import deep_classify_market
from qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
FIELDS=("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")
@dataclass(frozen=True,slots=True)
class RemainingOtherAudit:
 count:int;field_nonempty:tuple;prefixes:tuple;samples:tuple
def audit_remaining_other(snapshot,sample_limit=40):
 rows=[];non=Counter();pre=Counter()
 for m in snapshot_markets(snapshot):
  if deep_classify_market(m).topic!="other" or detect_sports_market(m).is_sports:continue
  rows.append(m)
  for f in FIELDS:
   if str(m.get(f,"") or "").strip():non[f]+=1
  raw=str(m.get("series_ticker","") or m.get("event_ticker","") or m.get("ticker",""))
  if raw:pre[raw.split("-")[0][:50]]+=1
 samples=tuple((str(m.get("ticker","")),str(m.get("series_ticker","")),str(m.get("event_ticker","")),str(m.get("title",""))[:240]) for m in rows[:sample_limit])
 return RemainingOtherAudit(len(rows),tuple(non.most_common()),tuple(pre.most_common(40)),samples)
