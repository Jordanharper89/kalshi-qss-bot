from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_011_BUILD_ID="OSR-011"
OSR_011_REVISION="OSR_011_UNCERTAINTY_DECOMPOSITION_ENGINE_V1"

@dataclass(frozen=True)
class UncertaintyComponents:
    missing_evidence:float
    contradiction:float
    source_reliability:float
    model_ambiguity:float
    hypothesis_competition:float
    total_uncertainty:float
    dominant_component:str

def decompose_uncertainty(missing_evidence,contradiction,source_reliability,model_ambiguity,hypothesis_competition):
    vals={
        "missing_evidence":float(missing_evidence),
        "contradiction":float(contradiction),
        "source_reliability":float(source_reliability),
        "model_ambiguity":float(model_ambiguity),
        "hypothesis_competition":float(hypothesis_competition),
    }
    if any(not 0<=x<=1 for x in vals.values()):
        raise ValueError("uncertainty components must be normalized")
    total=sum(vals.values())/len(vals)
    dominant=sorted(vals.items(), key=lambda x:(-x[1],x[0]))[0][0]
    return UncertaintyComponents(vals["missing_evidence"],vals["contradiction"],vals["source_reliability"],vals["model_ambiguity"],vals["hypothesis_competition"],total,dominant)

def build_osr_011_certification_manifest():
    return MappingProxyType({"build_id":OSR_011_BUILD_ID,"revision":OSR_011_REVISION,"decomposition":"five_component","execution":False,"publication":False})

def verify_osr_011_uncertainty_decomposition_engine():
    x=decompose_uncertainty(.8,.2,.3,.4,.5)
    return x.dominant_component=="missing_evidence" and 0<=x.total_uncertainty<=1
