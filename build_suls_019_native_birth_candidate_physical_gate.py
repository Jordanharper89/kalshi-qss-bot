from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_019_native_birth_candidate_physical_gate.py"
TEST=ROOT/"test_suls_019_native_birth_candidate_physical_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_017_live_native_transaction_program_scan import write as scan_write
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_018_native_pool_birth_candidate_decoder import write as decode_write

def run(root,attempts=5):
 observed=[];total_tx=0
 for i in range(max(1,int(attempts))):
  _,s=scan_write(root);total_tx+=int(s.get("transaction_count",0))
  _,d=decode_write(root)
  for x in d.get("candidates",[]):
   key=(x.get("slot"),x.get("signature"))
   if key not in {(y.get("slot"),y.get("signature")) for y in observed}:observed.append(x)
  if observed:break
  if i+1<attempts:time.sleep(1.0)
 return {"revision":"SULS_019","attempts":i+1,"transactions_examined":total_tx,
  "candidate_count":len(observed),"candidates":observed,
  "physical_candidate_observed":bool(observed),"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_candidate_physical_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_019_native_birth_candidate_physical_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[ATTEMPTS]",d["attempts"]);print("[TRANSACTIONS_EXAMINED]",d["transactions_examined"])
  print("[CANDIDATE_COUNT]",d["candidate_count"]);print("[PHYSICAL_CANDIDATE_OBSERVED]",d["physical_candidate_observed"])
  for x in d["candidates"][:20]:print("[PHYSICAL_CANDIDATE]",json.dumps(x,sort_keys=True))
  if not d["physical_candidate_observed"]:self.fail("NO_NATIVE_POOL_BIRTH_CANDIDATE_OBSERVED")
  print("[PASS] SULS-019 native birth candidate physical gate")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-019 NATIVE BIRTH CANDIDATE PHYSICAL GATE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()