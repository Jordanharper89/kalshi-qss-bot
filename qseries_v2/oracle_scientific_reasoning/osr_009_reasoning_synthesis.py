from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .osr_006_bayesian_update import BayesianEvidenceUpdate
from .osr_007_causal_relationship import CausalRelationshipEvaluation
from .osr_008_temporal_sequence import TemporalSequenceAnalysis

OSR_009_BUILD_ID="OSR-009"
OSR_009_REVISION="OSR_009_BAYESIAN_CAUSAL_TEMPORAL_SYNTHESIS_V1"

@dataclass(frozen=True)
class ScientificSynthesis:
    posterior_probability:float
    causal_status:str
    temporal_precedence:bool
    confidence:float
    conclusion_state:str
    abstain:bool

def synthesize_bayesian_causal_temporal(bayesian,causal,temporal,cause_event_id,effect_event_id,minimum_confidence=.6):
    if not isinstance(bayesian,BayesianEvidenceUpdate) or not isinstance(causal,CausalRelationshipEvaluation) or not isinstance(temporal,TemporalSequenceAnalysis):
        raise ValueError("certified reasoning components required")
    temporal_ok=(cause_event_id,effect_event_id) in temporal.causal_precedence_pairs
    causal_factor=1.0 if causal.status=="supported" else (.5 if causal.status=="uncertain" else 0.0)
    temporal_factor=1.0 if temporal_ok else 0.25
    confidence=bayesian.posterior_probability*causal_factor*temporal_factor
    abstain=confidence<float(minimum_confidence)
    state="supported" if not abstain and causal.status=="supported" and temporal_ok else ("contradicted" if causal.status=="contradicted" else "uncertain")
    return ScientificSynthesis(bayesian.posterior_probability,causal.status,temporal_ok,confidence,state,abstain)

def build_osr_009_certification_manifest():
    return MappingProxyType({"build_id":OSR_009_BUILD_ID,"revision":OSR_009_REVISION,"synthesis":"Bayesian+causal+temporal","abstention":True,"execution":False})

def verify_osr_009_bayesian_causal_temporal_synthesis():
    from .osr_006_bayesian_update import bayesian_update
    from .osr_007_causal_relationship import CausalCriterion,evaluate_causal_relationship
    from .osr_008_temporal_sequence import TemporalEvent,analyze_temporal_sequence
    b=bayesian_update(.5,9)
    c=evaluate_causal_relationship("cause","effect",(CausalCriterion("temporal_precedence",True,1),CausalCriterion("mechanism",True,1)))
    t=analyze_temporal_sequence((TemporalEvent("cause",1,"a"*64),TemporalEvent("effect",2,"b"*64)))
    s=synthesize_bayesian_causal_temporal(b,c,t,"cause","effect")
    return not s.abstain and s.conclusion_state=="supported"
