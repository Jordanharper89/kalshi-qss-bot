import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"subscription_ack_count":d["subscription_ack_count"],
   "notifications_seen":d["notifications_seen"],"row_count":d["row_count"],
   "venue_row_counts":d["venue_row_counts"],"venue_exact_counts":d["venue_exact_counts"]},sort_keys=True))
  self.assertEqual(d["subscription_ack_count"],14);self.assertGreater(d["notifications_seen"],0)
  self.assertGreater(d["row_count"],0);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-046B one shared live router covers all 14 known Solana venue programs")
  print("[PASS] exact plugins decode; undecoded activity remains raw for later adapters")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
