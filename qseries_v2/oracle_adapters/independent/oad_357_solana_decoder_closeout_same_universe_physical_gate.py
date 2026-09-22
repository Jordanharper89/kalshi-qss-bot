\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_348_solana_verified_economic_program_expansion import identify_verified_economic_program
from .oad_353_solana_final_verified_economic_program_expansion import identify_final_verified_program
from .oad_354_solana_economic_protocol_attribution_v3 import attribute_economic_protocols_v3
from .oad_355_solana_final_economic_behavior_decoder import decode_final_economic_behaviors
from .oad_356_solana_decoder_closeout_unknown_registry import rank_decoder_closeout_unknowns

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaDecoderCloseoutPhysicalReport:
    blocks:int
    transactions:int
    program_invocations:int
    previous_known:int
    final_known:int
    previous_unknown:int
    final_unknown:int
    previous_known_ratio:float
    final_known_ratio:float
    known_ratio_delta:float
    previous_economic_known:int
    final_economic_known:int
    previous_economic_resolution_ratio:float
    final_economic_resolution_ratio:float
    economic_resolution_delta:float
    wallet_flows:int
    decoded_behaviors:int
    behavior_counts:tuple
    remaining_unknowns:tuple
    state:str
    execution_authority:bool=False

def measure_decoder_closeout_physical(block_limit=2,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    env=canonical_transaction_envelopes(batch)
    attrs=attribute_economic_protocols_v3(env)
    flows=build_wallet_token_flows(env)
    behaviors=decode_final_economic_behaviors(env,attrs,flows)
    unknowns=rank_decoder_closeout_unknowns(attrs,flows)

    ids=[]
    for a in attrs: ids.extend(tuple(a.top_level_program_ids)+tuple(a.inner_program_ids))
    pk=pe=fk=fe=0
    for pid in ids:
        p=identify_verified_economic_program(pid)
        f=identify_final_verified_program(pid)
        if p.known:
            pk+=1
            if p.market_relevant: pe+=1
        if f.known:
            fk+=1
            if f.market_relevant: fe+=1
    total=len(ids); pu=total-pk; fu=total-fk
    pr=pk/total if total else 1.0; fr=fk/total if total else 1.0
    pden=pe+pu; fden=fe+fu
    per=pe/pden if pden else 1.0; fer=fe/fden if fden else 1.0
    bc=Counter(b.behavior for b in behaviors)

    return SolanaDecoderCloseoutPhysicalReport(
        len(batch.blocks),len(env),total,pk,fk,pu,fu,pr,fr,fr-pr,pe,fe,per,fer,fer-per,
        len(flows),len(behaviors),tuple(bc.most_common()),
        tuple((u.program_id,u.invocations,u.flow_transactions,u.bidirectional_flow_transactions,u.priority_score,u.disposition) for u in unknowns[:20]),
        "DECODER_CLOSEOUT_PHYSICAL_MEASURED" if env and ids else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY",False
    )

