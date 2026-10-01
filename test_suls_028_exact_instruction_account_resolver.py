import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_028_exact_instruction_account_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_resolve(self):
  p,d=write(ROOT);print("[TARGET_INSTRUCTION_COUNT]",d["target_instruction_count"])
  for r in d["rows"]:
   for x in r["target_instructions"]:print("[TARGET_INSTRUCTION]",json.dumps(x,sort_keys=True))
  if d["target_instruction_count"]==0:self.fail("NO_METEORA_TARGET_INSTRUCTIONS_RESOLVED")
  print("[PASS] SULS-028 exact instruction account resolver")
if __name__=="__main__":unittest.main()
