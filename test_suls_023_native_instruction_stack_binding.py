import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_023_native_instruction_stack_binding import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_bind(self):
  p,d=write(ROOT);print("[BOUND_BIRTH_COUNT]",d["bound_birth_count"])
  for x in d["rows"]:
   for e in x["birth_instruction_events"]:print("[BIRTH_INSTRUCTION]",json.dumps(e,sort_keys=True))
  if d["bound_birth_count"]==0:self.fail("NO_BIRTH_INSTRUCTION_BOUND_TO_EXACT_PROGRAM")
  print("[PASS] SULS-023 native instruction-stack binding")
if __name__=="__main__":unittest.main()
