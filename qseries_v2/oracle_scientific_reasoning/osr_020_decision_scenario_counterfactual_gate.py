from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_016_decision_outcome_evaluation import verify_osr_016_decision_theoretic_outcome_evaluation
from .osr_017_scenario_branching import verify_osr_017_scenario_construction_branch_reasoning
from .osr_018_counterfactual_reasoning import verify_osr_018_counterfactual_reasoning_engine
from .osr_019_decision_scenario_counterfactual_synthesis import verify_osr_019_decision_scenario_counterfactual_synthesis

OSR_020_BUILD_ID="OSR-020"
OSR_020_REVISION="OSR_020_DECISION_SCENARIO_COUNTERFACTUAL_CERTIFICATION_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class DecisionScenarioCounterfactualCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_osr_016_through_020():
    checks=(
        verify_osr_016_decision_theoretic_outcome_evaluation(),
        verify_osr_017_scenario_construction_branch_reasoning(),
        verify_osr_018_counterfactual_reasoning_engine(),
        verify_osr_019_decision_scenario_counterfactual_synthesis(),
    )
    if not all(checks):
        raise RuntimeError("decision/scenario/counterfactual capability certification failed")
    builds=tuple("OSR-%03d"%i for i in range(16,21))
    raw={
        "builds":builds,
        "capability":"decision_theory_scenario_and_counterfactual_reasoning",
        "next_capability":"game_theory_complex_systems_and_signal_reasoning",
        "certified":True,
    }
    return DecisionScenarioCounterfactualCertification(builds,raw["capability"],raw["next_capability"],_h(raw))

def build_osr_020_certification_manifest():
    c=certify_osr_016_through_020()
    return MappingProxyType({
        "build_id":OSR_020_BUILD_ID,
        "revision":OSR_020_REVISION,
        "capability":c.capability,
        "next_capability":c.next_capability,
        "certified":True,
        "execution":False,
        "publication":False,
    })

def verify_osr_020_decision_scenario_counterfactual_certification_gate():
    c=certify_osr_016_through_020()
    return c.certified and len(c.builds)==5 and c.next_capability=="game_theory_complex_systems_and_signal_reasoning"
