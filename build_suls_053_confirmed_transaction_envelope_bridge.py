from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_053_confirmed_transaction_envelope_bridge.py"
TEST=ROOT/"test_suls_053_confirmed_transaction_envelope_bridge.py"

MOD_TEXT=r"""from __future__ import annotations
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
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_053_confirmed_transaction_envelope_bridge import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_bridge(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if d["block_count"]==0 or d["transaction_count"]==0:self.fail("CONFIRMED_TRANSACTION_ENVELOPE_BRIDGE_FAILED")
  print("[PASS] SULS-053 confirmed transaction envelope bridge")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")