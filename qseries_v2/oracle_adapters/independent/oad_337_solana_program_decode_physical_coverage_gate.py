\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_320_solana_program_instruction_registry import classify_transaction_instructions
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_333_solana_authoritative_program_identity_registry import identify_solana_program
from .oad_334_solana_transaction_protocol_attribution import attribute_transaction_protocols
from .oad_335_solana_jupiter_route_reconstruction import reconstruct_routed_swaps
from .oad_336_solana_pump_meteora_market_behavior_decoder import decode_protocol_market_behaviors

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
BASELINE_KNOWN_RATIO=0.5804145818441744

@dataclass(frozen=True,slots=True)
class SolanaProgramDecodePhysicalReport:
    blocks:int
    transactions:int
    instructions:int
    baseline_known_ratio:float
    prior_registry_known:int
    authoritative_known:int
    infrastructure_instructions:int
    economic_known_instructions:int
    unknown_instructions:int
    authoritative_known_ratio:float
    economic_resolution_ratio:float
    wallet_flows:int
    routed_swaps:int
    protocol_behaviors:int
    protocol_counts:tuple
    top_unknown_programs:tuple
    materially_improved:bool
    state:str
    execution_authority:bool=False

def measure_solana_program_decode_physical(block_limit=1,timeout_seconds=25.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    env=canonical_transaction_envelopes(batch)
    legacy=classify_transaction_instructions(env)
    attr=attribute_transaction_protocols(env)
    flows=build_wallet_token_flows(env)
    routes=reconstruct_routed_swaps(env,attr,flows)
    behaviors=decode_protocol_market_behaviors(env,attr,flows)

    # Count exact top-level + CPI program invocations from the attribution layer.
    ids=[]
    for a in attr:
        ids.extend(a.top_level_program_ids)
        ids.extend(a.inner_program_ids)
    infra=econ=unknown=0
    pc=Counter(); uc=Counter()
    for pid in ids:
        x=identify_solana_program(pid)
        if not x.known:
            unknown+=1;uc[pid]+=1
        elif x.category=="INFRASTRUCTURE":
            infra+=1;pc[x.name]+=1
        else:
            econ+=1;pc[x.name]+=1
    total=len(ids)
    known=infra+econ
    ratio=known/total if total else 1.0
    econ_denom=econ+unknown
    economic_ratio=econ/econ_denom if econ_denom else 1.0
    prior_known=sum(1 for x in legacy if x.program_class!="UNKNOWN_PROGRAM")
    improved=ratio>BASELINE_KNOWN_RATIO
    state="PROGRAM_DECODE_COVERAGE_MEASURED" if env and total else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY"
    return SolanaProgramDecodePhysicalReport(
        len(batch.blocks),len(env),total,BASELINE_KNOWN_RATIO,prior_known,known,infra,econ,unknown,
        ratio,economic_ratio,len(flows),len(routes),len(behaviors),
        tuple(pc.most_common()),tuple(uc.most_common(20)),improved,state,False
    )

