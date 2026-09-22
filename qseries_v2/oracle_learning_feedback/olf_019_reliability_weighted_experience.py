from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .olf_014_condition_aware_experience import resolve_condition_aware_experience
from .olf_018_pattern_stability import materialize_pattern_stability

OLF_019_BUILD_ID="OLF-019"
OLF_019_REVISION="OLF_019_RELIABILITY_WEIGHTED_EXPERIENCE_RESOLVER_V1"

@dataclass(frozen=True)
class ReliabilityWeightedExperience:
    market_ticker:str
    available:bool
    pattern_id:str
    samples:int
    condition_similarity:float
    historical_relationship_strength:float
    hit_rate:float
    mean_brier_score:float
    calibration_error:float
    reliability_weight:float
    contradiction_score:float
    stable:bool
    reliability_weighted_strength:float
    learner_state_hash:str
    reason:str
    directional_signal_available:bool=False
    execution_authority:bool=False

def resolve_reliability_weighted_experience(root=None,market_ticker="",source_rows=()):
    root=Path(root or Path.cwd()).resolve()
    base=resolve_condition_aware_experience(root,market_ticker,source_rows)
    stability=materialize_pattern_stability(root)
    by={str(x["pattern_id"]):x for x in stability.get("patterns",[])}
    p=by.get(base.pattern_id)
    if not base.available or p is None:
        return ReliabilityWeightedExperience(base.market_ticker,False,base.pattern_id,base.samples,base.condition_similarity,base.relationship_strength,0,1,1,0,1,False,0,base.learner_state_hash,"NO_PERFORMANCE_QUALIFIED_PATTERN",False,False)
    weighted=base.relationship_strength*float(p["reliability_weight"])
    available=bool(p["stable"]) and weighted>=.20
    reason="STABLE_PERFORMANCE_QUALIFIED_PATTERN" if available else "PATTERN_CONTESTED_OR_LOW_RELIABILITY"
    return ReliabilityWeightedExperience(
        base.market_ticker,available,base.pattern_id,int(p["samples"]),base.condition_similarity,
        base.relationship_strength,float(p["hit_rate"]),float(p["mean_brier_score"]),
        float(p["calibration_error"]),float(p["reliability_weight"]),float(p["contradiction_score"]),
        bool(p["stable"]),weighted,base.learner_state_hash,reason,False,False
    )

def verify_olf_019_reliability_weighted_experience_resolver():
    return OLF_019_BUILD_ID=="OLF-019" and callable(resolve_reliability_weighted_experience)
