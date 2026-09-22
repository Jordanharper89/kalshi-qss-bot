from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .osr_016_decision_outcome_evaluation import DecisionTheoreticEvaluation
from .osr_017_scenario_branching import ScenarioTree
from .osr_018_counterfactual_reasoning import CounterfactualComparison

OSR_019_BUILD_ID="OSR-019"
OSR_019_REVISION="OSR_019_DECISION_SCENARIO_COUNTERFACTUAL_SYNTHESIS_V1"

@dataclass(frozen=True)
class DecisionScenarioCounterfactualSynthesis:
    risk_adjusted_value:float
    scenario_mass:float
    counterfactual_effect:float
    confidence:float
    state:str
    abstain:bool

def synthesize_decision_scenario_counterfactual(decision,scenario,counterfactual,minimum_confidence=.55):
    if not isinstance(decision,DecisionTheoreticEvaluation) or not isinstance(scenario,ScenarioTree) or not isinstance(counterfactual,CounterfactualComparison):
        raise ValueError("certified reasoning components required")
    mass_quality=max(0.0,1-abs(1-scenario.total_leaf_probability))
    identifiability=1.0 if counterfactual.identifiable else .25
    decisiveness=min(1.0,abs(decision.risk_adjusted_value))
    confidence=mass_quality*identifiability*(.5+.5*decisiveness)
    abstain=decision.abstain or confidence<minimum_confidence
    state="supported" if not abstain else "uncertain"
    return DecisionScenarioCounterfactualSynthesis(decision.risk_adjusted_value,scenario.total_leaf_probability,counterfactual.treatment_effect,confidence,state,abstain)

def build_osr_019_certification_manifest():
    return MappingProxyType({"build_id":OSR_019_BUILD_ID,"revision":OSR_019_REVISION,"synthesis":"decision+scenario+counterfactual","abstention":True,"execution":False})

def verify_osr_019_decision_scenario_counterfactual_synthesis():
    from .osr_016_decision_outcome_evaluation import OutcomeState,evaluate_outcomes
    from .osr_017_scenario_branching import make_branch,build_scenario_tree
    from .osr_018_counterfactual_reasoning import evaluate_counterfactual
    d=evaluate_outcomes((OutcomeState("a",1,1,0),),0)
    t=build_scenario_tree((make_branch("r",None,1,"r"),make_branch("a","r",1,"a")))
    c=evaluate_counterfactual(1,0,True)
    s=synthesize_decision_scenario_counterfactual(d,t,c)
    return not s.abstain and s.state=="supported"
