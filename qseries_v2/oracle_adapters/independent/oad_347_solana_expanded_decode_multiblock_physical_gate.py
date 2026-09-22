\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_343_solana_verified_recurring_program_identity_expansion import identify_expanded_program
from .oad_344_solana_expanded_protocol_attribution import attribute_expanded_protocols
from .oad_345_solana_orderbook_dex_behavior_decoder import decode_orderbook_dex_behaviors
from .oad_346_solana_unresolved_economic_evidence_profiler import profile_unresolved_economic_evidence

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

OAD342_KNOWN_RATIO=0.9130739572379951
OAD342_ECONOMIC_RESOLUTION_RATIO=0.8226037195994278

@dataclass(frozen=True,slots=True)
class SolanaExpandedDecodePhysicalReport:
    blocks:int
    transactions:int
    program_invocations:int
    known:int
    infrastructure:int
    economic_known:int
    unknown:int
    known_ratio:float
    economic_resolution_ratio:float
    wallet_flows:int
    orderbook_behaviors:int
    behavior_counts:tuple
    top_unknown_programs:tuple
    top_unresolved_economic_evidence:tuple
    state:str
    execution_authority:bool=False

def measure_expanded_decode_physical(block_limit=2,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    env=canonical_transaction_envelopes(batch)
    attrs=attribute_expanded_protocols(env)
    flows=build_wallet_token_flows(env)
    behaviors=decode_orderbook_dex_behaviors(env,attrs,flows)
    evidence=profile_unresolved_economic_evidence(env,attrs,flows)

    ids=[]
    for a in attrs:
        ids.extend(tuple(a.top_level_program_ids)+tuple(a.inner_program_ids))

    known=infra=econ=0
    unknown_counter=Counter()
    for pid in ids:
        x=identify_expanded_program(pid)
        if x.known:
            known+=1
            if x.market_relevant:
                econ+=1
            else:
                infra+=1
        else:
            unknown_counter[pid]+=1

    unknown=sum(unknown_counter.values())
    known_ratio=(known/len(ids)) if ids else 1.0
    economic_den=econ+unknown
    economic_ratio=(econ/economic_den) if economic_den else 1.0
    bc=Counter(b.behavior for b in behaviors)

    evidence_rows=tuple(
        (
            e.program_id,e.invocations,e.transactions,
            e.transactions_with_token_flows,e.bidirectional_flow_transactions,
            e.evidence_class
        )
        for e in evidence[:20]
    )

    return SolanaExpandedDecodePhysicalReport(
        len(batch.blocks),len(env),len(ids),known,infra,econ,unknown,
        known_ratio,economic_ratio,len(flows),len(behaviors),
        tuple(bc.most_common()),
        tuple(unknown_counter.most_common(20)),
        evidence_rows,
        "EXPANDED_PROGRAM_DECODE_COVERAGE_MEASURED" if env and ids else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY",
        False
    )

