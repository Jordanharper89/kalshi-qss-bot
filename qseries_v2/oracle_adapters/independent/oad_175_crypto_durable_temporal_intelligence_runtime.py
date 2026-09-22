from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_163_crypto_live_multi_source_cohort import build_crypto_live_multi_source_cohort
from .oad_167_crypto_structured_condition_metric_extraction import extract_crypto_condition_metrics
from .oad_168_crypto_condition_state_normalization import normalize_crypto_condition_states
from .oad_169_crypto_temporal_condition_change_evaluator import evaluate_crypto_temporal_condition_changes
from .oad_170_crypto_cross_source_consistency_profile import build_crypto_cross_source_consistency_profiles
from .oad_172_crypto_condition_snapshot_postgresql_persistence import stamp_crypto_condition_states,persist_crypto_condition_snapshot
from .oad_173_crypto_condition_source_scoped_history_readback import read_crypto_condition_history_for_current_states
from .oad_174_crypto_historical_condition_sequence_and_prior_state import select_latest_prior_comparable_states,build_crypto_condition_sequences

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoDurableTemporalIntelligenceResult:
    snapshot_at:str; cohort_state:str; current_states:int; historical_states:int
    exact_prior_states:int; comparable_temporal_metrics:int; increased:int; decreased:int
    unchanged:int; no_comparable_history:int; sequences:int; cross_source_assets:tuple
    committed_new:int; exact_readback:int; changes:tuple; profiles:tuple
    runtime_ready:bool; execution_authority:bool=False

def run_crypto_durable_temporal_intelligence(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0,per_source_history_limit=512,snapshot_at=None):
    stamp=snapshot_at or datetime.now(timezone.utc)
    if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=timezone.utc)
    stamp=stamp.astimezone(timezone.utc)

    # Acquire/normalize current state first only to know the exact condition source IDs.
    # History is still read before current persistence, preventing self-comparison.
    cohort=build_crypto_live_multi_source_cohort(acquisition_timeout_seconds)
    metrics=extract_crypto_condition_metrics(cohort)
    raw_states=normalize_crypto_condition_states(metrics)
    evidence_times={(x.asset,x.source_family,x.metric_name):x.observed_at for x in raw_states}
    current=stamp_crypto_condition_states(raw_states,stamp)

    history=read_crypto_condition_history_for_current_states(
        current,root=root,per_source_limit=per_source_history_limit
    )
    prior=select_latest_prior_comparable_states(current,history.states)
    changes=evaluate_crypto_temporal_condition_changes(current,prior)
    profiles=build_crypto_cross_source_consistency_profiles(current,changes)
    sequences=build_crypto_condition_sequences(history.states)

    persisted=persist_crypto_condition_snapshot(
        current,root=root,timeout_seconds=timeout_seconds,snapshot_at=stamp,
        evidence_observed_at_by_key=evidence_times,
    )
    cross=tuple(x.asset for x in profiles if x.evidence_state=="CROSS_SOURCE_PRESENT")
    comparable=sum(x.comparable_history_present for x in changes)
    inc=sum(x.temporal_state=="INCREASED" for x in changes)
    dec=sum(x.temporal_state=="DECREASED" for x in changes)
    same=sum(x.temporal_state=="UNCHANGED" for x in changes)
    none=sum(x.temporal_state=="NO_COMPARABLE_HISTORY" for x in changes)
    ready=bool(current and cross and persisted.exact_readback==len(current))
    return CryptoDurableTemporalIntelligenceResult(
        stamp.isoformat(),cohort.state,len(current),len(history.states),len(prior),
        comparable,inc,dec,same,none,len(sequences),cross,persisted.committed_new,
        persisted.exact_readback,changes,profiles,ready,False
    )
