from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_163_crypto_live_multi_source_cohort import build_crypto_live_multi_source_cohort
from .oad_164_crypto_asset_chain_evidence_alignment import align_crypto_asset_chain_evidence
from .oad_165_crypto_cross_source_evidence_comparison_state import build_crypto_evidence_comparison_states

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
DIRECTION_ENABLED=False

@dataclass(frozen=True,slots=True)
class CryptoCrossSourcePhysicalCertification:
    state:str
    available_sources:tuple
    unavailable_sources:tuple
    total_observations:int
    aligned_assets:int
    ready_for_evidence_comparison_assets:int
    ready_assets:tuple
    asset_states:tuple
    runtime_ready:bool
    certified_at:str
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def run_crypto_cross_source_physical_runtime_certification(
    timeout_seconds=20.0,
    max_coinbase_products=25,
    max_alignment_span_seconds=1800.0,
):
    cohort=build_crypto_live_multi_source_cohort(timeout_seconds,max_coinbase_products)
    alignments=align_crypto_asset_chain_evidence(cohort)
    states=build_crypto_evidence_comparison_states(alignments,max_alignment_span_seconds)
    ready=tuple(x.asset for x in states if x.ready_for_evidence_comparison)
    asset_states=tuple((x.asset,x.state,x.market_observation_count,x.chain_observation_count,x.observation_time_span_seconds) for x in states)
    runtime_ready=(
        "coinbase" in cohort.available_sources
        and any(x in cohort.available_sources for x in ("bitcoin","ethereum","solana"))
        and bool(ready)
    )
    if not runtime_ready:
        raise RuntimeError(
            "crypto cross-source runtime has no simultaneous market+chain evidence; "
            f"source_states={tuple((x.source_family,x.state,x.observation_count,x.error_type,x.error_message) for x in cohort.source_states)!r}; "
            f"asset_states={asset_states!r}"
        )
    return CryptoCrossSourcePhysicalCertification(
        cohort.state,cohort.available_sources,cohort.unavailable_sources,len(cohort.observations),
        sum(1 for x in alignments if x.market_source_present or x.chain_source_present),
        len(ready),ready,asset_states,True,datetime.now(timezone.utc).isoformat(),
        True,False,False,False
    )
