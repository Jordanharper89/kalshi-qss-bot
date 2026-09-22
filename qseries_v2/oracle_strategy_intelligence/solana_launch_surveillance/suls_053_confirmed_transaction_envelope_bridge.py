from __future__ import annotations
import json
from dataclasses import dataclass
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_052_confirmed_native_block_capture import acquire_confirmed_block_batch
from qseries_v2.oracle_adapters.independent.oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes

@dataclass(frozen=True,slots=True)
class BridgeBatch:
 head_slot:int
 blocks:tuple

def run():
 b=acquire_confirmed_block_batch(3)
 bridge=BridgeBatch(b.head_slot,b.blocks)
 envs=canonical_transaction_envelopes(bridge)
 return {"revision":"SULS_053","head_slot":b.head_slot,"block_count":len(b.blocks),
  "transaction_count":len(envs),
  "sample":[{"slot":getattr(e,"slot",None),"signature":getattr(e,"signature",None),
   "success":getattr(e,"success",None),"block_time":getattr(e,"block_time",None)}
   for e in envs[:20]],"execution_authority":False,"read_only":True}

def write(root):
 d=run();p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_transaction_envelope_bridge.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
