from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OCL_023_BUILD_ID="OCL-023"
OCL_023_REVISION="OCL_023_META_LEARNING_PERFORMANCE_EVALUATION_V1"

@dataclass(frozen=True)
class MetaLearningPerformance:
    mechanism_id:str
    evaluation_count:int
    improvement_count:int
    degradation_count:int
    mean_delta:float
    usefulness_score:float
    status:str

def evaluate_meta_learning_performance(mechanism_id,deltas):
    rows=tuple(float(x) for x in deltas)
    if not mechanism_id or not rows: raise ValueError("mechanism evaluations required")
    improve=sum(1 for x in rows if x>0); degrade=sum(1 for x in rows if x<0)
    mean=sum(rows)/len(rows)
    directional=(improve-degrade)/len(rows)
    magnitude=min(1.0,abs(mean))
    score=directional*magnitude
    status="beneficial" if score>.05 else ("harmful" if score<-.05 else "uncertain")
    return MetaLearningPerformance(mechanism_id,len(rows),improve,degrade,mean,score,status)

def build_ocl_023_certification_manifest():
    return MappingProxyType({"build_id":OCL_023_BUILD_ID,"revision":OCL_023_REVISION,"evaluates":"historical_learning_mechanism_performance","self_modifying_code":False,"execution":False})

def verify_ocl_023_meta_learning_performance_evaluation():
    good=evaluate_meta_learning_performance("m",(0.2,0.1,0.3))
    bad=evaluate_meta_learning_performance("n",(-0.2,-0.1,-0.3))
    return good.status=="beneficial" and bad.status=="harmful"
