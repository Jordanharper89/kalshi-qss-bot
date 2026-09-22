from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .ocl_023_meta_learning_performance import MetaLearningPerformance

OCL_024_BUILD_ID="OCL-024"
OCL_024_REVISION="OCL_024_ADAPTIVE_LEARNING_WEIGHT_MODEL_V1"

@dataclass(frozen=True)
class AdaptiveLearningWeight:
    mechanism_id:str
    base_weight:float
    performance_score:float
    maturity_score:float
    adjusted_weight:float

def build_adaptive_learning_weight(performance,base_weight,maturity_score):
    if not isinstance(performance,MetaLearningPerformance):
        raise ValueError("certified performance object required")
    if not 0<=base_weight<=1 or not 0<=maturity_score<=1:
        raise ValueError("normalized weights required")
    performance_factor=max(0.0,min(1.0,(performance.usefulness_score+1)/2))
    adjusted=float(base_weight)*(0.25+0.75*performance_factor)*float(maturity_score)
    return AdaptiveLearningWeight(performance.mechanism_id,float(base_weight),performance.usefulness_score,float(maturity_score),adjusted)

def build_ocl_024_certification_manifest():
    return MappingProxyType({"build_id":OCL_024_BUILD_ID,"revision":OCL_024_REVISION,"adaptation":"bounded_weight_only","code_rewrite":False,"execution":False,"publication":False})

def verify_ocl_024_adaptive_learning_weight_model():
    from .ocl_023_meta_learning_performance import evaluate_meta_learning_performance
    good=evaluate_meta_learning_performance("g",(.5,.4,.3))
    bad=evaluate_meta_learning_performance("b",(-.5,-.4,-.3))
    return build_adaptive_learning_weight(good,1,.9).adjusted_weight>build_adaptive_learning_weight(bad,1,.9).adjusted_weight
