from pathlib import Path
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_052_proven_current_canonical_trader_cohort import read_latest_current_trader_cohort
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_080_current_observation_source_independence_probe import classify_current_observation_sources
OIAR_081_BUILD_ID="OIAR-081"
def build_current_independent_evidence_availability(root=None):
 c=read_latest_current_trader_cohort(root);p=classify_current_observation_sources(root)
 if not c:raise RuntimeError("OIAR-052 cohort unavailable")
 ids={m["market_ticker"] for m in c["markets"]};by={k:[] for k in ids}
 for r in p["independent_candidates"]:
  t=str(r.get("ticker") or "")
  if t in by:by[t].append(r)
 rows=[{"market_id":k,"independent_evidence_rows":len(v),"independent_evidence_available":bool(v),"evidence":v} for k,v in sorted(by.items())]
 return {"schema_version":"OIAR-081","market_count":len(rows),"markets_with_independent_evidence":sum(x["independent_evidence_available"] for x in rows),"markets":rows,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=build_current_independent_evidence_availability(root);return {"markets":x["market_count"],"markets_with_independent_evidence":x["markets_with_independent_evidence"],"probability_enabled":False,"execution_authority":False}
