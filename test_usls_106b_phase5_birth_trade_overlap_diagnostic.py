import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106b_phase5_birth_trade_overlap_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"pair_count":d["pair_count"]},sort_keys=True))
  for x in d["pairs"][:30]:print("[PAIR]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["pair_count"],0,"NO_BIRTH_TRADE_OVERLAP_AT_ANY_IDENTITY_LEVEL")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106B birth↔trade overlap diagnostic")
  print("[PASS] no lifecycle certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
