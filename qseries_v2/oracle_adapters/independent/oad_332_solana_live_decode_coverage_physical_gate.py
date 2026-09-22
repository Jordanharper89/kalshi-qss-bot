\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_320_solana_program_instruction_registry import classify_transaction_instructions
from .oad_328_solana_live_dex_pool_identity_registry import build_live_solana_dex_pool_registry
from .oad_329_solana_dex_transaction_attribution import attribute_transactions_to_live_dex_pools
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_331_solana_dex_market_behavior_inference import infer_solana_market_behavior
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaDecodeCoverageReport:
 blocks:int;transactions:int;instructions:int;unknown_instructions:int;known_instruction_ratio:float
 dex_registry_pools:int;dex_registry_ids:tuple;dex_attributed_transactions:int;wallet_flows:int
 decoded_behaviors:int;behavior_counts:tuple;unknown_program_counts:tuple;state:str;execution_authority:bool=False
def measure_live_solana_decode_coverage(block_limit=1,dex_query="SOL/USDC",dex_limit=100,timeout_seconds=25.0):
    b=acquire_finalized_block_batch(None,block_limit,timeout_seconds);env=canonical_transaction_envelopes(b)
    cls=classify_transaction_instructions(env);reg=build_live_solana_dex_pool_registry(dex_query,dex_limit,timeout_seconds)
    attr=attribute_transactions_to_live_dex_pools(env,reg);flows=build_wallet_token_flows(env);beh=infer_solana_market_behavior(env,attr,flows)
    unknown=[c.program_id for c in cls if c.program_class=="UNKNOWN_PROGRAM"]
    known_ratio=(len(cls)-len(unknown))/len(cls) if cls else 1.0
    bc=Counter(x.behavior for x in beh);uc=Counter(unknown)
    state="LIVE_DECODE_COVERAGE_MEASURED" if env and cls else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY"
    return SolanaDecodeCoverageReport(len(b.blocks),len(env),len(cls),len(unknown),known_ratio,reg.pools,reg.dexes,sum(x.attributed for x in attr),len(flows),len(beh),tuple(sorted(bc.items())),tuple(uc.most_common(20)),state,False)

