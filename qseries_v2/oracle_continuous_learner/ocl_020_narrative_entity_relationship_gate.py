from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_016_entity_learning import verify_ocl_016_entity_learning_model
from .ocl_017_entity_relationship import verify_ocl_017_entity_relationship_learning
from .ocl_018_narrative_learning import verify_ocl_018_narrative_learning_engine
from .ocl_019_narrative_market_relationship import verify_ocl_019_narrative_market_relationship_learning

OCL_020_BUILD_ID="OCL-020"
OCL_020_REVISION="OCL_020_NARRATIVE_ENTITY_RELATIONSHIP_CERTIFICATION_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class NarrativeEntityRelationshipCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_ocl_016_through_020():
    checks=(
        verify_ocl_016_entity_learning_model(),
        verify_ocl_017_entity_relationship_learning(),
        verify_ocl_018_narrative_learning_engine(),
        verify_ocl_019_narrative_market_relationship_learning(),
    )
    if not all(checks):
        raise RuntimeError("capability certification failed")
    builds=tuple("OCL-%03d"%i for i in range(16,21))
    raw={
        "builds":builds,
        "capability":"narrative_entity_and_relationship_learning",
        "next_capability":"learner_state_aggregation_and_meta_learning",
        "certified":True,
    }
    return NarrativeEntityRelationshipCertification(builds,raw["capability"],raw["next_capability"],_h(raw))

def build_ocl_020_certification_manifest():
    c=certify_ocl_016_through_020()
    return MappingProxyType({
        "build_id":OCL_020_BUILD_ID,
        "revision":OCL_020_REVISION,
        "capability":c.capability,
        "next_capability":c.next_capability,
        "certified":True,
        "execution":False,
        "publication":False,
    })

def verify_ocl_020_narrative_entity_relationship_certification_gate():
    c=certify_ocl_016_through_020()
    return c.certified and len(c.builds)==5 and c.next_capability=="learner_state_aggregation_and_meta_learning"
