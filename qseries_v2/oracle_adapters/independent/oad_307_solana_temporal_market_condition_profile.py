from __future__ import annotations
from dataclasses import dataclass

from .oad_267_solana_pool_liquidity_historical_state import read_solana_proven_history
from .oad_270_solana_price_volume_liquidity_acceleration_conditions import build_solana_acceleration_conditions

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

DISCOVERY_SOURCE_ID="source.dex.solana.token_discovery.latest"

@dataclass(frozen=True,slots=True)
class TemporalMarketConditionProfile:
    token_address:str
    queried_rows:int
    pair_conditions:tuple
    ready_pairs:int
    evidence_state:str
    queried_sources:tuple
    durable_read_only:bool=True
    probability:None=None
    direction:None=None
    execution_authority:bool=False

def _latest_discovered_token(root=None,per_source_limit=64):
    history=read_solana_proven_history(
        root=root,
        source_ids=(DISCOVERY_SOURCE_ID,),
        per_source_limit=per_source_limit,
        refresh=False,
    )
    if not history.records:
        raise RuntimeError(
            "No durable Solana discovery history found. "
            "OAD-307 will not force a new production write merely to read history."
        )

    # OAD-267 returns exact bounded history for this source. Select the latest
    # observation by persisted observed_at/sequence identity without acquiring
    # or writing anything new.
    rows=sorted(
        history.records,
        key=lambda r: (
            str(r.observed_at),
            -1 if r.sequence_number is None else int(r.sequence_number),
            str(r.observation_id),
        ),
        reverse=True,
    )
    for row in rows:
        tokens=tuple(row.payload.get("tokens") or ())
        if not tokens:
            continue
        first=tokens[0]
        if isinstance(first,dict):
            token=str(first.get("token_address") or "").strip()
            if token:
                return token,history
    raise RuntimeError("Durable Solana discovery history contains no token identity")

def build_current_temporal_market_condition_profile(
    root=None,
    per_source_limit=64,
):
    token,discovery_history=_latest_discovered_token(
        root=root,
        per_source_limit=per_source_limit,
    )

    source_ids=(
        DISCOVERY_SOURCE_ID,
        "source.dex.solana.token_pools."+token,
        "source.onchain.solana.mint."+token,
    )
    history=read_solana_proven_history(
        root=root,
        source_ids=source_ids,
        per_source_limit=per_source_limit,
        refresh=False,
    )

    # Acceleration conditions consume the exact durable pool-history records.
    # Discovery/mint records may coexist in the readback but are ignored by
    # the underlying pool delta/pressure builders when not applicable.
    conditions=build_solana_acceleration_conditions(history.records)
    ready=sum(1 for x in conditions if x.state=="COMPOSITE_READY")
    state=(
        "TEMPORAL_READY"
        if conditions and ready
        else "TEMPORAL_PARTIAL"
        if conditions
        else "DURABLE_HISTORY_INSUFFICIENT_FOR_TEMPORAL_PAIR"
    )
    return TemporalMarketConditionProfile(
        token_address=token,
        queried_rows=history.queried_rows,
        pair_conditions=conditions,
        ready_pairs=ready,
        evidence_state=state,
        queried_sources=history.queried_sources,
        durable_read_only=True,
        probability=None,
        direction=None,
        execution_authority=False,
    )
