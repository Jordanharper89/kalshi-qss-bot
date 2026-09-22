from qseries_v2.oracle_intelligence_analytics_runtime.oiar_074_current_repeated_history_temporal_evidence import build_current_temporal_evidence
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_082_independent_research_direction_gate import build_independent_research_direction_gate
OIAR_083_BUILD_ID="OIAR-083"
def certify_directional_reasoning_input(root=None):
 t=build_current_temporal_evidence(root);g=build_independent_research_direction_gate(root);gm={x["market_id"]:x for x in g["markets"]};rows=[]
 for m in t["markets"]:
  q=gm.get(m["market_id"],{});ind=str(q.get("independent_research_direction") or "neutral").lower();temp="bull" if m["temporal_direction"]=="UP" else "bear" if m["temporal_direction"]=="DOWN" else "neutral";cert=ind in ("bull","bear")
  rows.append({"market_id":m["market_id"],"temporal_market_direction":temp,"independent_research_direction":ind,"independent_direction_certified":cert,"reasoning_input_ready":cert,"market_direction_may_not_substitute":True})
 ready=sum(x["reasoning_input_ready"] for x in rows)
 status="READY_FOR_INDEPENDENT_DIRECTION_REASONING" if ready else "HOLD_INDEPENDENT_RESEARCH_DIRECTION_UNAVAILABLE"
 return {"schema_version":"OIAR-083","gate_status":status,"market_count":len(rows),"reasoning_input_ready_markets":ready,"markets":rows,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=certify_directional_reasoning_input(root);return {"gate_status":x["gate_status"],"markets":x["market_count"],"reasoning_input_ready_markets":x["reasoning_input_ready_markets"],"probability_enabled":False,"execution_authority":False}
