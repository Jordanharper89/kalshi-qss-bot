from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_learner.ocl_016_entity_learning import build_entity_learning_observation,verify_entity_learning_observation
from qseries_v2.oracle_continuous_learner.ocl_017_entity_relationship import learn_entity_relationship,verify_entity_relationship_state
from .oad_218_existing_ocl_state_hash_envelope import envelope
from .oad_227_crypto_learned_case_asof_snapshot_boundary import capture_crypto_learned_case_snapshot

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class PhysicalEntityRelationshipMaterialization:
    as_of_sequence:int
    entity_observations:int
    relationships:tuple
    entity_relationship_state_hash:str|None
    state:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def materialize_entity_relationship_state(root=None,per_asset_limit=512):
    snap=capture_crypto_learned_case_snapshot(root,per_asset_limit)
    observations=[];association={}
    for seq,oid,source,observed,praw in snap.rows:
        p=praw if isinstance(praw,dict) else dict(praw or ())
        asset=str(p.get("asset") or "").upper()
        evh=str(p.get("evidence_hash") or "");outh=str(p.get("outcome_hash") or "")
        rv=p.get("return_fraction")
        if not asset or len(evh)!=64 or len(outh)!=64 or rv is None:continue
        ts=observed.isoformat() if hasattr(observed,"isoformat") else str(observed)
        eo=build_entity_learning_observation(f"asset:{asset.lower()}","crypto_asset","realized_return",float(rv),ts,evh,outh)
        if not verify_entity_learning_observation(eo):raise RuntimeError("OCL-016 entity observation failed verification")
        observations.append(eo)
        for row in tuple(p.get("condition_vector") or ()):
            if not isinstance(row,(list,tuple)) or not row:continue
            family=str(row[0]).strip().lower()
            if not family:continue
            key=(f"source_family:{family}",f"asset:{asset.lower()}","observed_condition_association")
            association.setdefault(key,[]).append(True)
    relationships=[]
    for (src,tgt,typ),evidence in sorted(association.items()):
        rel=learn_entity_relationship(src,tgt,typ,tuple(evidence))
        if not verify_entity_relationship_state(rel):raise RuntimeError("OCL-017 relationship failed verification")
        relationships.append(rel)
    rels=tuple(relationships)
    h=envelope("entity_relationship",rels).state_hash if rels else None
    return PhysicalEntityRelationshipMaterialization(snap.as_of_sequence,len(observations),rels,h,"MATERIALIZED_NON_CAUSAL_ASSOCIATIONS" if rels else "HOLD_ENTITY_RELATIONSHIP_EVIDENCE_REQUIRED")
