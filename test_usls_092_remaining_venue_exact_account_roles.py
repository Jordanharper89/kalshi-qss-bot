import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_092_remaining_venue_exact_account_roles import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_role_count":d["exact_role_count"],"venue_exact_role_counts":d["venue_exact_role_counts"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["exact_role_count"],d["row_count"],"SOURCE_ACCOUNT_LAYOUT_INCOMPLETE")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-092 exact source-backed account roles")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
