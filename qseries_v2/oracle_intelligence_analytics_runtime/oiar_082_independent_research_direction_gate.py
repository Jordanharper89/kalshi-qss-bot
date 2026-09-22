from qseries_v2.oracle_intelligence_analytics_runtime.oiar_079_research_direction_provenance_audit import audit_research_direction_provenance
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_081_current_independent_evidence_availability import build_current_independent_evidence_availability
OIAR_082_BUILD_ID="OIAR-082"
def build_independent_research_direction_gate(root=None):
 p=audit_research_direction_provenance(root);e=build_current_independent_evidence_availability(root);emap={x["market_id"]:x for x in e["markets"]};rows=[]
 for r in p["markets"]:
  a=emap.get(r["market_id"],{});available=bool(a.get("independent_evidence_available"))
  rows.append({"market_id":r["market_id"],"market_derived_direction":r["research_direction"],"independent_evidence_available":available,"independent_research_direction":"neutral","direction_status":"EVIDENCE_PRESENT_DIRECTION_NOT_CERTIFIED" if available else "NO_INDEPENDENT_EVIDENCE","market_direction_may_not_substitute":True})
 return {"schema_version":"OIAR-082","market_count":len(rows),"independent_direction_certified":0,"markets":rows,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=build_independent_research_direction_gate(root);return {"markets":x["market_count"],"independent_evidence_present":sum(m["independent_evidence_available"] for m in x["markets"]),"independent_direction_certified":0,"probability_enabled":False,"execution_authority":False}
