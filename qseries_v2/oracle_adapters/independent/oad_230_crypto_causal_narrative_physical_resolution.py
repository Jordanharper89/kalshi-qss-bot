from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_learner.ocl_014_causal_evidence import verify_ocl_014_causal_evidence_learning
from qseries_v2.oracle_continuous_learner.ocl_018_narrative_learning import verify_ocl_018_narrative_learning_engine
from qseries_v2.oracle_continuous_learner.ocl_019_narrative_market_relationship import verify_ocl_019_narrative_market_relationship_learning
from .oad_227_crypto_learned_case_asof_snapshot_boundary import capture_crypto_learned_case_snapshot

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CausalNarrativePhysicalResolution:
    as_of_sequence:int
    explicit_causal_rows:int
    explicit_narrative_rows:int
    causal_state_hash:str|None
    narrative_state_hash:str|None
    causal_state:str
    narrative_state:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def resolve_causal_narrative_physical_state(root=None,per_asset_limit=512):
    if not verify_ocl_014_causal_evidence_learning():raise RuntimeError("OCL-014 verifier failed")
    if not verify_ocl_018_narrative_learning_engine():raise RuntimeError("OCL-018 verifier failed")
    if not verify_ocl_019_narrative_market_relationship_learning():raise RuntimeError("OCL-019 verifier failed")
    snap=capture_crypto_learned_case_snapshot(root,per_asset_limit)
    causal=[];narrative=[]
    for row in snap.rows:
        p=row[4] if isinstance(row[4],dict) else dict(row[4] or ())
        if p.get("causal_evidence") is not None:causal.append(p["causal_evidence"])
        if p.get("narrative_observations") is not None or p.get("narrative_reactions") is not None:narrative.append(p)
    # Current crypto learned-case schema contains condition vectors and outcomes,
    # not explicit causal evidence or narrative observations/reactions.
    return CausalNarrativePhysicalResolution(
        snap.as_of_sequence,len(causal),len(narrative),None,None,
        "HOLD_EXPLICIT_CAUSAL_EVIDENCE_REQUIRED" if not causal else "HOLD_CAUSAL_PROVENANCE_VALIDATION_REQUIRED",
        "HOLD_EXPLICIT_NARRATIVE_EVIDENCE_REQUIRED" if not narrative else "HOLD_NARRATIVE_PROVENANCE_VALIDATION_REQUIRED",
    )
