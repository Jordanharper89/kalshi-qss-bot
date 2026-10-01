from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_020_native_birth_decoder_truth_gate.py"
TEST=ROOT/"test_suls_020_native_birth_decoder_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
def gate(root):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 r=json.loads((base/"native_birth_candidate_physical_gate.json").read_text(encoding="utf-8"))
 observed=bool(r.get("physical_candidate_observed"))
 return {"revision":"SULS_020","native_candidate_observed":observed,
  "candidate_count":r.get("candidate_count",0),"transactions_examined":r.get("transactions_examined",0),
  "verified_pool_birth_decoder_ready":False,
  "next_required_boundary":"SULS_021_EXACT_PROGRAM_INSTRUCTION_POOL_BIRTH_VERIFICATION" if observed else "SULS_021_NATIVE_BIRTH_CAPTURE_WINDOW_EXPANSION",
  "execution_authority":False,"read_only":True,
  "scope":"Candidate observation is not yet exact instruction-level pool-birth verification"}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_decoder_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_020_native_birth_decoder_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertFalse(d["verified_pool_birth_decoder_ready"])
  print("[PASS] SULS-020 native birth decoder truth gate")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-020 NATIVE BIRTH DECODER TRUTH GATE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()