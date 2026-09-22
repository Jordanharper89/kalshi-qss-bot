from collections import Counter
from pathlib import Path
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_054_proven_current_trader_analytics import read_latest_current_trader_analytics
OIAR_079_BUILD_ID="OIAR-079"
def audit_research_direction_provenance(root=None):
 x=read_latest_current_trader_analytics(root)
 if not x:raise RuntimeError("OIAR-054 snapshot unavailable")
 rows=[];dirs=Counter();reasons=Counter()
 for m in x.get("markets",[]):
  c=m.get("candidate",{});u=m.get("usefulness",{});d=str(c.get("research_direction") or "neutral").lower();dirs[d]+=1
  for r in c.get("reason_codes",[]) or []:reasons[str(r)]+=1
  rows.append({"market_id":m["market_id"],"research_direction":d,"candidate_disposition":c.get("disposition"),"usefulness_classification":u.get("classification"),"provenance":"OIA-006_MARKET_DERIVED_FEATURE_CLASSIFICATION","independent_external_evidence":False})
 return {"schema_version":"OIAR-079","market_count":len(rows),"direction_counts":dict(dirs),"candidate_reason_counts":dict(reasons),"market_derived_direction_count":len(rows),"independent_direction_count":0,"markets":rows,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=audit_research_direction_provenance(root);return {"markets":x["market_count"],"directions":x["direction_counts"],"candidate_reasons":x["candidate_reason_counts"],"market_derived_direction_count":x["market_derived_direction_count"],"independent_direction_count":0,"probability_enabled":False,"execution_authority":False}
