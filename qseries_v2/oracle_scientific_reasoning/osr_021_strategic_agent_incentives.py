from dataclasses import dataclass
from types import MappingProxyType
OSR_021_BUILD_ID="OSR-021"; OSR_021_REVISION="OSR_021_STRATEGIC_AGENT_INCENTIVE_REASONING_V1"
@dataclass(frozen=True)
class StrategicAgent:
    agent_id:str; objectives:tuple[str,...]; constraints:tuple[str,...]; available_actions:tuple[str,...]
@dataclass(frozen=True)
class IncentiveAssessment:
    agent_id:str; action_id:str; benefit:float; cost:float; constraint_penalty:float; incentive_score:float
def assess_incentive(agent,action_id,benefit,cost,constraint_penalty=0):
    if action_id not in agent.available_actions: raise ValueError("action unavailable to agent")
    vals=tuple(float(x) for x in (benefit,cost,constraint_penalty))
    if any(x<0 for x in vals): raise ValueError("nonnegative values required")
    return IncentiveAssessment(agent.agent_id,action_id,*vals,vals[0]-vals[1]-vals[2])
def rank_agent_actions(agent,assessments):
    rows=tuple(assessments)
    if not rows or any(x.agent_id!=agent.agent_id for x in rows): raise ValueError("matching assessments required")
    return tuple(sorted(rows,key=lambda x:(-x.incentive_score,x.action_id)))
def build_osr_021_certification_manifest(): return MappingProxyType({"build_id":OSR_021_BUILD_ID,"revision":OSR_021_REVISION,"execution":False})
def verify_osr_021_strategic_agent_incentive_reasoning():
    a=StrategicAgent("a",("profit",),(),("hold","act"))
    return rank_agent_actions(a,(assess_incentive(a,"hold",1,1),assess_incentive(a,"act",3,1)))[0].action_id=="act"
