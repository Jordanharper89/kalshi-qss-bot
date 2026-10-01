import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_021_exact_program_instruction_pool_birth_verification import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_verify(self):
  p,d=write(ROOT);print("[INSTRUCTION_LEVEL_CANDIDATES]",d["instruction_level_candidates"])
  for x in d["verified_candidates"]:print("[VERIFICATION]",json.dumps(x,sort_keys=True))
  if d["instruction_level_candidates"]==0:self.fail("NO_EXACT_PROGRAM_INSTRUCTION_BIRTH_CANDIDATE")
  print("[PASS] SULS-021 exact program/instruction pool-birth verification")
if __name__=="__main__":unittest.main()
