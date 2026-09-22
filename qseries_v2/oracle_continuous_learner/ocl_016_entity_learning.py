from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_016_BUILD_ID = "OCL-016"
OCL_016_REVISION = "OCL_016_ENTITY_LEARNING_MODEL_V1"

def _h(v):
    return sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

@dataclass(frozen=True)
class EntityLearningObservation:
    entity_id: str
    entity_type: str
    behavior_name: str
    behavior_value: float
    observed_at: str
    evidence_hash: str
    outcome_hash: str
    observation_hash: str

def build_entity_learning_observation(entity_id, entity_type, behavior_name, behavior_value, observed_at, evidence_hash, outcome_hash):
    if not entity_id or not entity_type or not behavior_name or not observed_at:
        raise ValueError("entity learning identity fields required")
    for x in (evidence_hash, outcome_hash):
        if len(x) != 64:
            raise ValueError("sha256 evidence/outcome required")
    raw = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "behavior_name": behavior_name,
        "behavior_value": float(behavior_value),
        "observed_at": observed_at,
        "evidence_hash": evidence_hash,
        "outcome_hash": outcome_hash,
    }
    return EntityLearningObservation(
        entity_id, entity_type, behavior_name, float(behavior_value), observed_at,
        evidence_hash, outcome_hash, _h(raw)
    )

def verify_entity_learning_observation(o):
    raw = {
        "entity_id": o.entity_id,
        "entity_type": o.entity_type,
        "behavior_name": o.behavior_name,
        "behavior_value": o.behavior_value,
        "observed_at": o.observed_at,
        "evidence_hash": o.evidence_hash,
        "outcome_hash": o.outcome_hash,
    }
    return o.observation_hash == _h(raw)

def build_ocl_016_certification_manifest():
    return MappingProxyType({
        "build_id": OCL_016_BUILD_ID,
        "revision": OCL_016_REVISION,
        "role": "outcome_grounded_entity_learning",
        "identity_mutation": False,
        "execution": False,
    })

def verify_ocl_016_entity_learning_model():
    o = build_entity_learning_observation("entity:fed", "organization", "announcement_lag", 3.0, "t", "a"*64, "b"*64)
    return verify_entity_learning_observation(o)
