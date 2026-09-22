from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
from .oad_190_crypto_comparable_condition_outcome_statistics import build_comparable_condition_outcome_statistics
from .oad_192_crypto_comparable_case_sample_sufficiency import assess_comparable_case_sufficiency
from .oad_193_crypto_recency_weighted_outcome_statistics import build_recency_weighted_outcome_statistics
from .oad_194_crypto_regime_relevance_weighting import build_latest_regime_profiles
from .oad_195_crypto_historical_outcome_contradiction_uncertainty import build_historical_outcome_uncertainty

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class WeightedHistoricalLearningCertification:
    historical_learned_cases:int
    raw_statistics_groups:int
    sufficiency_profiles:int
    recency_profiles:int
    regime_profiles:int
    uncertainty_profiles:int
    insufficient_groups:int
    mature_descriptive_groups:int
    assets:tuple
    physical_ready:bool
    certified_at:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def run_crypto_weighted_historical_learning_physical_certification(
    root=None,
    per_asset_limit:int=512,
    half_life_seconds:int=7*24*60*60,
):
    history=read_crypto_learned_case_history(root=root,per_asset_limit=per_asset_limit)
    if not history: raise RuntimeError("no verified crypto learned-case history available")
    now=datetime.now(timezone.utc)
    raw=build_comparable_condition_outcome_statistics(history)
    suff=assess_comparable_case_sufficiency(raw)
    recency=build_recency_weighted_outcome_statistics(history,reference_time=now,half_life_seconds=half_life_seconds)
    regime=build_latest_regime_profiles(history,reference_time=now,half_life_seconds=half_life_seconds)
    uncertainty=build_historical_outcome_uncertainty(recency)
    assets=tuple(sorted({x.asset for x in history}))
    ready=bool(
        raw and len(suff)==len(raw) and len(recency)==len(raw) and regime and
        len(uncertainty)==len(recency) and assets
    )
    if not ready:
        raise RuntimeError("weighted historical-learning certification failed")
    return WeightedHistoricalLearningCertification(
        len(history),len(raw),len(suff),len(recency),len(regime),len(uncertainty),
        sum(x.sufficiency_state=="INSUFFICIENT" for x in suff),
        sum(x.sufficiency_state=="MATURE_DESCRIPTIVE" for x in suff),
        assets,True,datetime.now(timezone.utc).isoformat(),False,False,False
    )
