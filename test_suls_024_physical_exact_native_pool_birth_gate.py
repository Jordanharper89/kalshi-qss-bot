import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_024_physical_exact_native_pool_birth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[VERIFIED_BIRTH_COUNT]",d["verified_birth_count"])
  for x in d["births"]:print("[NATIVE_BIRTH]",json.dumps(x,sort_keys=True))
  print("[SCOPE]",d["scope"])
  if d["verified_birth_count"]==0:self.fail("NO_EXACT_NATIVE_POOL_BIRTH_VERIFIED")
  print("[PASS] SULS-024 physical exact native pool-birth gate")
if __name__=="__main__":unittest.main()
