from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .osr_011_uncertainty_decomposition import UncertaintyComponents
from .osr_013_adversarial_challenge import AdversarialChallengeResult

OSR_014_BUILD_ID="OSR-014"
OSR_014_REVISION="OSR_014_CONTRADICTION_ALTERNATIVE_EXPLANATION_SYNTHESIS_V1"

@dataclass(frozen=True)
class AlternativeExplanation:
    explanation_id:str
    support:float
    contradiction:float
    plausibility:float

@dataclass(frozen=True)
class ContradictionAlternativeSynthesis:
    leading_explanation_id:str|None
    leading_score:float
    uncertainty:float
    adversarial_vulnerability:float
    abstain:bool
    synthesis_state:str

def synthesize_alternatives(uncertainty,adversarial_result,alternatives,minimum_score=.55):
    if not isinstance(uncertainty,UncertaintyComponents) or not isinstance(adversarial_result,AdversarialChallengeResult):
        raise ValueError("certified uncertainty and adversarial results required")
    rows=tuple(alternatives)
    if not rows: raise ValueError("alternative explanations required")
    scored=[]
    for x in rows:
        if not 0<=x.support<=1 or not 0<=x.contradiction<=1 or not 0<=x.plausibility<=1:
            raise ValueError("normalized alternative explanation values required")
        base=x.support*(1-x.contradiction)*x.plausibility
        penalty=(1-uncertainty.total_uncertainty)*(1-adversarial_result.vulnerability_score)
        score=base*(.5+.5*penalty)
        scored.append((score,x.explanation_id))
    scored=sorted(scored,key=lambda x:(-x[0],x[1]))
    leader=scored[0]
    abstain=leader[0]<minimum_score
    state="resolved" if not abstain else ("contested" if uncertainty.total_uncertainty>=.5 or adversarial_result.vulnerability_score>=.5 else "uncertain")
    return ContradictionAlternativeSynthesis(None if abstain else leader[1],leader[0],uncertainty.total_uncertainty,adversarial_result.vulnerability_score,abstain,state)

def build_osr_014_certification_manifest():
    return MappingProxyType({"build_id":OSR_014_BUILD_ID,"revision":OSR_014_REVISION,"combines":"uncertainty+contradiction+adversarial+alternatives","abstention":True,"execution":False})

def verify_osr_014_contradiction_alternative_explanation_synthesis():
    from .osr_011_uncertainty_decomposition import decompose_uncertainty
    from .osr_013_adversarial_challenge import HypothesisChallenge,challenge_hypothesis
    u=decompose_uncertainty(.1,.1,.1,.1,.1)
    a=challenge_hypothesis("h",(HypothesisChallenge("c","a",.1,.1,.1),))
    s=synthesize_alternatives(u,a,(AlternativeExplanation("x",1,0,1),AlternativeExplanation("y",.2,.5,.5)))
    return not s.abstain and s.leading_explanation_id=="x"
