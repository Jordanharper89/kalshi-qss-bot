from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_017_BUILD_ID="OCL-017"
OCL_017_REVISION="OCL_017_ENTITY_RELATIONSHIP_LEARNING_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class EntityRelationshipState:
    source_entity_id:str
    target_entity_id:str
    relationship_type:str
    supporting_count:int
    contradicting_count:int
    relationship_score:float
    relationship_hash:str

def learn_entity_relationship(source_entity_id,target_entity_id,relationship_type,evidence):
    if source_entity_id==target_entity_id:
        raise ValueError("distinct entities required")
    rows=tuple(bool(x) for x in evidence)
    if not rows:
        raise ValueError("relationship evidence required")
    sup=sum(rows); con=len(rows)-sup
    score=(sup-con)/len(rows)
    raw={
        "source_entity_id":source_entity_id,
        "target_entity_id":target_entity_id,
        "relationship_type":relationship_type,
        "supporting_count":sup,
        "contradicting_count":con,
        "relationship_score":score,
    }
    return EntityRelationshipState(source_entity_id,target_entity_id,relationship_type,sup,con,score,_h(raw))

def verify_entity_relationship_state(x):
    raw={
        "source_entity_id":x.source_entity_id,
        "target_entity_id":x.target_entity_id,
        "relationship_type":x.relationship_type,
        "supporting_count":x.supporting_count,
        "contradicting_count":x.contradicting_count,
        "relationship_score":x.relationship_score,
    }
    return x.source_entity_id!=x.target_entity_id and -1<=x.relationship_score<=1 and x.relationship_hash==_h(raw)

def build_ocl_017_certification_manifest():
    return MappingProxyType({"build_id":OCL_017_BUILD_ID,"revision":OCL_017_REVISION,"association_is_not_causation":True,"execution":False})

def verify_ocl_017_entity_relationship_learning():
    x=learn_entity_relationship("e1","e2","influence", (1,1,0))
    return verify_entity_relationship_state(x)
