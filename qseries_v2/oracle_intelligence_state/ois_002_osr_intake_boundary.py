from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OIS_002_BUILD_ID="OIS-002"
OIS_002_REVISION="OIS_002_CERTIFIED_OSR_STATE_INTAKE_BOUNDARY_V1"

@dataclass(frozen=True)
class OSRStateIntake:
    subject_id:str
    reasoning_state:str
    support:float
    confidence:float
    contradiction:float
    abstain:bool
    osr_state_hash:str
    read_only:bool=True

def build_osr_state_intake(subject_id,reasoning_state,support,confidence,contradiction,abstain,osr_state_hash):
    if not subject_id or len(osr_state_hash)!=64:
        raise ValueError("subject and certified OSR state hash required")
    vals=(float(support),float(confidence),float(contradiction))
    if any(not 0<=v<=1 for v in vals):
        raise ValueError("normalized OSR state values required")
    return OSRStateIntake(subject_id,reasoning_state,*vals,bool(abstain),osr_state_hash,True)

def build_ois_002_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_002_BUILD_ID,
        "revision":OIS_002_REVISION,
        "upstream":"OSR-030 frozen boundary",
        "osr_mutation":False,
        "read_only":True,
        "execution":False,
    })

def verify_ois_002_certified_osr_state_intake_boundary():
    x=build_osr_state_intake("btc","supported",.8,.9,.1,False,"a"*64)
    return x.read_only and x.confidence==.9 and not build_ois_002_certification_manifest()["osr_mutation"]
