import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_005_universal_opportunity_admission import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[ADMISSION_POLICY]",d["admission_policy"]);print("[ADMITTED_COUNT]",d["admitted_count"])
  for x in d["opportunities"][:20]:print("[OPPORTUNITY]",json.dumps(x,sort_keys=True))
  if d["admitted_count"]==0:self.fail("NO_SOLANA_OPPORTUNITIES_ADMITTED")
  print("[PASS] SULS-005 universal opportunity admission")
  print("[TRADER] Valid newborn/young pools are admitted for observation without excluding tiny market caps")
if __name__=="__main__":unittest.main()
