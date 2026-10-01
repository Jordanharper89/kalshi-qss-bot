from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_046_finalized_head_latency_probe.py"
TEST=ROOT/"test_suls_046_finalized_head_latency_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch

def probe():
 now=time.time();b=acquire_finalized_block_batch(limit=1)
 blocks=list(getattr(b,"blocks",()) or ())
 if not blocks:return {"revision":"SULS_046","ok":False,"error":"NO_FINALIZED_BLOCK","execution_authority":False}
 slot,blk=blocks[-1];bt=blk.get("blockTime")
 age=None if bt is None else max(0.0,now-float(bt))
 return {"revision":"SULS_046","ok":bt is not None,"head_slot":getattr(b,"head_slot",None),
  "sample_slot":slot,"block_time":bt,"observed_unix":now,"finalized_head_age_seconds":age,
  "launch_window_5s_possible":bool(age is not None and age<=5.0),
  "execution_authority":False,"read_only":True}

def write(root):
 d=probe();p=root/"runtime_state/solana_opportunities/launch_surveillance/finalized_head_latency_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_046_finalized_head_latency_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d.get("ok"):self.fail("FINALIZED_HEAD_LATENCY_PROBE_FAILED")
  print("[PASS] SULS-046 finalized-head latency probe")
  print("[TRADER] <=5s means finalized can serve launch entry timing; >5s means finalized is confirmation-only")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")