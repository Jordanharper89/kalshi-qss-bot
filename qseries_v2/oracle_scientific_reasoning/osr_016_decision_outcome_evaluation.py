from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_016_BUILD_ID="OSR-016"
OSR_016_REVISION="OSR_016_DECISION_THEORETIC_OUTCOME_EVALUATION_V1"

@dataclass(frozen=True)
class OutcomeState:
    outcome_id:str
    probability:float
    utility:float
    downside:float

@dataclass(frozen=True)
class DecisionTheoreticEvaluation:
    expected_utility:float
    expected_downside:float
    risk_adjusted_value:float
    outcome_count:int
    abstain:bool

def evaluate_outcomes(outcomes,risk_aversion=.5,minimum_absolute_value=.05):
    rows=tuple(outcomes)
    if not rows:
        raise ValueError("outcomes required")
    if not 0<=risk_aversion<=1:
        raise ValueError("risk_aversion must be normalized")
    total_p=sum(x.probability for x in rows)
    if abs(total_p-1.0)>1e-9:
        raise ValueError("outcome probabilities must sum to one")
    for x in rows:
        if not 0<=x.probability<=1 or x.downside<0:
            raise ValueError("invalid outcome")
    eu=sum(x.probability*x.utility for x in rows)
    ed=sum(x.probability*x.downside for x in rows)
    rav=eu-risk_aversion*ed
    abstain=abs(rav)<minimum_absolute_value
    return DecisionTheoreticEvaluation(eu,ed,rav,len(rows),abstain)

def build_osr_016_certification_manifest():
    return MappingProxyType({"build_id":OSR_016_BUILD_ID,"revision":OSR_016_REVISION,"role":"outcome_evaluation_only","action_authority":False,"execution":False})

def verify_osr_016_decision_theoretic_outcome_evaluation():
    rows=(OutcomeState("up",.6,1,.1),OutcomeState("down",.4,-.5,.8))
    x=evaluate_outcomes(rows,.5)
    return x.outcome_count==2 and isinstance(x.risk_adjusted_value,float)
