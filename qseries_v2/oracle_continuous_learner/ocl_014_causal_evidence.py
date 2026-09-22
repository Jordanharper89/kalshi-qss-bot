from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
OCL_014_BUILD_ID="OCL-014";OCL_014_REVISION="OCL_014_CAUSAL_EVIDENCE_LEARNING_V1"
@dataclass(frozen=True)
class CausalEvidenceState:
 cause_id:str; effect_id:str; supporting_weight:float; contradicting_weight:float; independent_sources:int; causal_evidence_score:float; status:str
def learn_causal_evidence(cause_id,effect_id,supporting_weights,contradicting_weights,independent_sources):
 if cause_id==effect_id or independent_sources<1:raise ValueError("valid cause/effect and independent evidence required")
 sup=sum(max(0.0,float(x)) for x in supporting_weights);con=sum(max(0.0,float(x)) for x in contradicting_weights)
 total=sup+con;score=0.0 if total==0 else (sup-con)/total
 status="supported" if score>=.5 and independent_sources>=2 else ("contradicted" if score<=-.5 else "uncertain")
 return CausalEvidenceState(cause_id,effect_id,sup,con,independent_sources,score,status)
def build_ocl_014_certification_manifest():return MappingProxyType({"build_id":OCL_014_BUILD_ID,"revision":OCL_014_REVISION,"supports_counterevidence":True,"correlation_is_not_causation":True,"execution":False})
def verify_ocl_014_causal_evidence_learning():
 a=learn_causal_evidence("x","y",(1,.8),(.1,),2);b=learn_causal_evidence("x","y",(.1,),(1,.8),2)
 return a.status=="supported" and b.status=="contradicted"
