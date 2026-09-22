from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_075_meteora_damm_v1_program_correction.py"
TEST=ROOT/"test_usls_075_meteora_damm_v1_program_correction.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,json
from pathlib import Path

CORRECT_PROGRAM="Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"
RETIRED_BAD_PROGRAM="Eo7WjKq67jJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"
SWAP_DISC=hashlib.sha256(b"global:swap").digest()[:8]

def write(root):
 d={"revision":"USLS_075","venue":"METEORA_DAMM_V1","program_id":CORRECT_PROGRAM,
  "retired_bad_program_id":RETIRED_BAD_PROGRAM,"swap_discriminator_hex":SWAP_DISC.hex(),
  "supersedes_registry_revision":"USLS_065_FOR_DAMM_V1_PROGRAM_ID_ONLY",
  "execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_damm_v1_program_correction.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_075_meteora_damm_v1_program_correction import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertNotEqual(CORRECT_PROGRAM,RETIRED_BAD_PROGRAM)
  self.assertEqual(CORRECT_PROGRAM,"Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB")
  self.assertEqual(SWAP_DISC.hex(),"f8c69e91e17587c8")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-075 Meteora DAMM v1 program-ID correction")
  print("[PASS] retired bad ...67jJ... address; official ...67rjJ... address frozen")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")