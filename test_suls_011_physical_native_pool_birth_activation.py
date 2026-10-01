import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_011_physical_native_pool_birth_activation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_activation(self):
  p,d=write(ROOT)
  print("[CALLABLE_COUNT]",d["callable_count"])
  for r in d["native_candidates"]:print("[NATIVE_CANDIDATE]",json.dumps(r,sort_keys=True))
  print("[PHYSICAL_NATIVE_ACTIVATION_CANDIDATE]",json.dumps(d["physical_native_activation_candidate"],sort_keys=True))
  if d["callable_count"]==0:self.fail("NO_CALLABLE_NATIVE_SOLANA_ACQUISITION")
  print("[PASS] SULS-011 physical native pool-birth activation candidate")
  print("[SCOPE] Callable activation candidate only; pool-birth decode not yet claimed")
if __name__=="__main__":unittest.main()
