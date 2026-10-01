import unittest,json
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
