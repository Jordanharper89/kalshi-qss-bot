\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_343_solana_verified_recurring_program_identity_expansion import identify_expanded_program
from .oad_348_solana_verified_economic_program_expansion import identify_verified_economic_program
from .oad_349_solana_economic_protocol_attribution_v2 import attribute_economic_protocols_v2
from .oad_350_solana_verified_economic_flow_behavior_decoder import decode_verified_economic_flow_behaviors
from .oad_351_solana_remaining_unknown_priority_ranker import rank_remaining_unknown_programs

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaSameUniverseCoverageReport:
    blocks:int
    transactions:int
    program_invocations:int
    old_known:int
    new_known:int
    old_unknown:int
    new_unknown:int
    old_known_ratio:float
    new_known_ratio:float
    known_ratio_delta:float
    old_economic_known:int
    new_economic_known:int
    old_economic_resolution_ratio:float
    new_economic_resolution_ratio:float
    economic_resolution_delta:float
    wallet_flows:int
    decoded_behaviors:int
    behavior_counts:tuple
    remaining_unknowns:tuple
    state:str
    execution_authority:bool=False

def measure_same_universe_coverage(block_limit=2,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    env=canonical_transaction_envelopes(batch)
    attrs=attribute_economic_protocols_v2(env)
    flows=build_wallet_token_flows(env)
    behaviors=decode_verified_economic_flow_behaviors(env,attrs,flows)
    priorities=rank_remaining_unknown_programs(attrs,flows)

    ids=[]
    for a in attrs:
        ids.extend(tuple(a.top_level_program_ids)+tuple(a.inner_program_ids))

    old_known=old_econ=0
    new_known=new_econ=0
    for pid in ids:
        o=identify_expanded_program(pid)
        n=identify_verified_economic_program(pid)
        if o.known:
            old_known+=1
            if o.market_relevant: old_econ+=1
        if n.known:
            new_known+=1
            if n.market_relevant: new_econ+=1

    total=len(ids)
    old_unknown=total-old_known; new_unknown=total-new_known
    old_ratio=(old_known/total) if total else 1.0
    new_ratio=(new_known/total) if total else 1.0
    old_econ_den=old_econ+old_unknown
    new_econ_den=new_econ+new_unknown
    old_econ_ratio=(old_econ/old_econ_den) if old_econ_den else 1.0
    new_econ_ratio=(new_econ/new_econ_den) if new_econ_den else 1.0
    bc=Counter(b.behavior for b in behaviors)

    return SolanaSameUniverseCoverageReport(
        len(batch.blocks),len(env),total,
        old_known,new_known,old_unknown,new_unknown,
        old_ratio,new_ratio,new_ratio-old_ratio,
        old_econ,new_econ,old_econ_ratio,new_econ_ratio,new_econ_ratio-old_econ_ratio,
        len(flows),len(behaviors),tuple(bc.most_common()),
        tuple((p.program_id,p.invocations,p.flow_transactions,p.bidirectional_flow_transactions,p.priority_score,p.priority_class) for p in priorities[:20]),
        "SAME_UNIVERSE_COVERAGE_MEASURED" if env and ids else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY",
        False
    )

