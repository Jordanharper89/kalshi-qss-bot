from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .oad_267_solana_pool_liquidity_historical_state import read_solana_proven_history
from .oad_307_solana_temporal_market_condition_profile import build_current_temporal_market_condition_profile

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class WalletTraderConditionProfile:
    token_address:str
    holder_rows:int
    trader_rows:int
    holder_observations:int
    trader_observations:int
    conditions:tuple
    evidence_state:str
    queried_sources:tuple
    provider_claim_only:bool=True
    durable_read_only:bool=True
    probability:None=None
    direction:None=None
    execution_authority:bool=False

def _latest(records, observation_type):
    rows=tuple(r for r in records if r.observation_type==observation_type)
    if not rows:
        return None
    return sorted(
        rows,
        key=lambda r:(
            -1 if r.sequence_number is None else int(r.sequence_number),
            str(r.observed_at),
            str(r.observation_id),
        ),
    )[-1]

def _count(row):
    if row is None:
        return 0
    try:
        return max(0,int(row.payload.get("row_count") or 0))
    except (TypeError,ValueError):
        return 0

def build_current_wallet_trader_condition_profile(root=None,per_source_limit=64):
    # Current token identity comes only from already-durable Solana evidence.
    temporal=build_current_temporal_market_condition_profile(
        root=root,
        per_source_limit=per_source_limit,
    )
    token=temporal.token_address
    source_ids=(
        "source.gmgn.solana.token."+token+".holders",
        "source.gmgn.solana.token."+token+".traders",
    )
    h=read_solana_proven_history(
        root=root,
        source_ids=source_ids,
        per_source_limit=per_source_limit,
        refresh=False,
    )
    holder=_latest(h.records,"gmgn_solana_holders")
    trader=_latest(h.records,"gmgn_solana_traders")
    holder_rows=_count(holder)
    trader_rows=_count(trader)

    if holder is not None and trader is not None:
        state="DURABLE_WALLET_TRADER_EVIDENCE_READY"
    elif holder is not None or trader is not None:
        state="DURABLE_WALLET_TRADER_EVIDENCE_PARTIAL"
    else:
        state="DURABLE_WALLET_TRADER_EVIDENCE_UNAVAILABLE"

    conditions=(
        ("holder_rows",holder_rows),
        ("trader_rows",trader_rows),
        ("holder_evidence_present",holder is not None),
        ("trader_evidence_present",trader is not None),
    )
    return WalletTraderConditionProfile(
        token_address=token,
        holder_rows=holder_rows,
        trader_rows=trader_rows,
        holder_observations=sum(1 for r in h.records if r.observation_type=="gmgn_solana_holders"),
        trader_observations=sum(1 for r in h.records if r.observation_type=="gmgn_solana_traders"),
        conditions=conditions,
        evidence_state=state,
        queried_sources=h.queried_sources,
        provider_claim_only=True,
        durable_read_only=True,
        probability=None,
        direction=None,
        execution_authority=False,
    )
