from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_163_crypto_live_multi_source_cohort import build_crypto_live_multi_source_cohort
from .oad_167_crypto_structured_condition_metric_extraction import extract_crypto_condition_metrics
from .oad_168_crypto_condition_state_normalization import normalize_crypto_condition_states
from .oad_169_crypto_temporal_condition_change_evaluator import evaluate_crypto_temporal_condition_changes
from .oad_170_crypto_cross_source_consistency_profile import build_crypto_cross_source_consistency_profiles

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoConditionIntelligencePhysicalCertification:
    state:str
    available_sources:tuple
    unavailable_sources:tuple
    raw_observations:int
    structured_metrics:int
    condition_states:int
    temporal_changes:int
    comparable_temporal_metrics:int
    cross_source_assets:tuple
    profiles:tuple
    runtime_ready:bool
    certified_at:str
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def run_crypto_condition_intelligence_physical_runtime_certification(
    timeout_seconds=20.0,
    previous_states=(),
):
    cohort=build_crypto_live_multi_source_cohort(timeout_seconds)
    metrics=extract_crypto_condition_metrics(cohort)
    states=normalize_crypto_condition_states(metrics)
    changes=evaluate_crypto_temporal_condition_changes(states,previous_states)
    profiles=build_crypto_cross_source_consistency_profiles(states,changes)
    cross=tuple(x.asset for x in profiles if x.evidence_state=="CROSS_SOURCE_PRESENT")
    comparable=sum(1 for x in changes if x.comparable_history_present)
    runtime_ready=bool(metrics and states and cross)
    if not runtime_ready:
        raise RuntimeError(
            "crypto condition intelligence not ready; "
            f"sources={tuple((x.source_family,x.state,x.observation_count,x.error_type) for x in cohort.source_states)!r}; "
            f"metrics={len(metrics)}; cross_source_assets={cross!r}"
        )
    return CryptoConditionIntelligencePhysicalCertification(
        cohort.state,cohort.available_sources,cohort.unavailable_sources,
        len(cohort.observations),len(metrics),len(states),len(changes),comparable,
        cross,profiles,True,datetime.now(timezone.utc).isoformat(),
        True,False,False,False
    )
