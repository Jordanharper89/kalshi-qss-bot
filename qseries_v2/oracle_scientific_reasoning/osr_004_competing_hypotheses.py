from __future__ import annotations
from dataclasses import dataclass
from math import log
from types import MappingProxyType
from .osr_002_hypothesis_formation import ScientificHypothesis
from .osr_003_evidence_evaluation import HypothesisEvidenceEvaluation

OSR_004_BUILD_ID="OSR-004"
OSR_004_REVISION="OSR_004_COMPETING_HYPOTHESIS_ANALYSIS_V1"

@dataclass(frozen=True)
class CompetingHypothesisScore:
    hypothesis_id:str
    prior_probability:float
    evidence_score:float
    posterior_weight:float

@dataclass(frozen=True)
class CompetingHypothesisAnalysis:
    scores:tuple[CompetingHypothesisScore,...]
    leading_hypothesis_id:str|None
    normalized_leader_probability:float
    abstain:bool

def analyze_competing_hypotheses(hypotheses,evaluations,minimum_leader_probability=.6):
    hs=tuple(hypotheses); ev={x.hypothesis_id:x for x in evaluations}
    if len(hs)<2: raise ValueError("at least two competing hypotheses required")
    if len({h.hypothesis_id for h in hs})!=len(hs): raise ValueError("duplicate hypothesis")
    raw=[]
    for h in hs:
        if not isinstance(h,ScientificHypothesis) or h.hypothesis_id not in ev:
            raise ValueError("complete hypothesis evaluations required")
        e=ev[h.hypothesis_id]
        likelihood=max(.001,min(.999,(e.net_evidence+1)/2))
        weight=h.prior_probability*likelihood
        raw.append((h,e.net_evidence,weight))
    total=sum(x[2] for x in raw)
    scores=tuple(sorted((CompetingHypothesisScore(h.hypothesis_id,h.prior_probability,e,w/total if total else 0.0) for h,e,w in raw),key=lambda x:(-x.posterior_weight,x.hypothesis_id)))
    leader=scores[0]
    abstain=leader.posterior_weight<float(minimum_leader_probability)
    return CompetingHypothesisAnalysis(scores,None if abstain else leader.hypothesis_id,leader.posterior_weight,abstain)

def build_osr_004_certification_manifest():
    return MappingProxyType({"build_id":OSR_004_BUILD_ID,"revision":OSR_004_REVISION,"competing_hypotheses":True,"abstention":True,"execution":False})

def verify_osr_004_competing_hypothesis_analysis():
    from .osr_001_foundation import build_scientific_reasoning_input
    from .osr_002_hypothesis_formation import form_hypothesis
    from .osr_003_evidence_evaluation import HypothesisEvidenceEvaluation
    i=build_scientific_reasoning_input("a"*64,"q")
    h1=form_hypothesis(i,"h1","s1","m1","f1",.5);h2=form_hypothesis(i,"h2","s2","m2","f2",.5)
    e1=HypothesisEvidenceEvaluation("h1",1,0,.8,2,1,"supported")
    e2=HypothesisEvidenceEvaluation("h2",0,1,-.8,2,1,"contradicted")
    a=analyze_competing_hypotheses((h1,h2),(e1,e2))
    return not a.abstain and a.leading_hypothesis_id=="h1"
