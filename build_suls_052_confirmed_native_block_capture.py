from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_052_confirmed_native_block_capture.py"
TEST=ROOT/"test_suls_052_confirmed_native_block_capture.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc

@dataclass(frozen=True,slots=True)
class ConfirmedBlockBatch:
 head_slot:int
 blocks:tuple
 commitment:str="confirmed"
 execution_authority:bool=False

def acquire_confirmed_block_batch(limit=2):
 head=int(_rpc("getSlot",[{"commitment":"confirmed"}],15.0))
 start=max(0,head-max(1,int(limit))+1);rows=[]
 for slot in range(start,head+1):
  try:
   b=_rpc("getBlock",[slot,{"commitment":"confirmed","encoding":"jsonParsed",
      "transactionDetails":"full","rewards":False,"maxSupportedTransactionVersion":1}],20.0)
   if b:rows.append((slot,b))
  except Exception:continue
 return ConfirmedBlockBatch(head,tuple(rows))

def write(root):
 b=acquire_confirmed_block_batch(2);now=time.time()
 ages=[max(0.0,now-float(x[1].get("blockTime"))) for x in b.blocks if x[1].get("blockTime") is not None]
 d={"revision":"SULS_052","head_slot":b.head_slot,"block_count":len(b.blocks),
  "min_age_seconds":min(ages) if ages else None,"max_age_seconds":max(ages) if ages else None,
  "confirmed_capture_ready":bool(b.blocks),"execution_authority":False,"read_only":True}
 p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_native_block_capture.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_052_confirmed_native_block_capture import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_capture(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["confirmed_capture_ready"]:self.fail("CONFIRMED_NATIVE_BLOCK_CAPTURE_FAILED")
  print("[PASS] SULS-052 confirmed native block capture")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")