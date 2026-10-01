import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_047_native_commitment_capability_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  for x in d["modules"]:print("[MODULE]",json.dumps({k:v for k,v in x.items() if k!="source_excerpt"},sort_keys=True))
  if not d["modules"]:self.fail("NO_NATIVE_COMMITMENT_MODULES")
  print("[PASS] SULS-047 native commitment capability audit")
if __name__=="__main__":unittest.main()
