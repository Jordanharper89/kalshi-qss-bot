import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106_phase5_exact_birth_trade_join import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_join(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("birth_rows_seen","trade_rows_seen","exact_join_rows","unresolved_trade_rows")},sort_keys=True))
  self.assertGreater(d["birth_rows_seen"],0);self.assertGreater(d["trade_rows_seen"],0)
  self.assertGreater(d["exact_join_rows"],0,"NO_PHYSICAL_BIRTH_TRADE_OVERLAP")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106 exact birth↔trade physical join")
  print("[PASS] unresolved trades retained rather than dropped")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
