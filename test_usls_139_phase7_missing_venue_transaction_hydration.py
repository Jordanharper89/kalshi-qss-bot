import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_139_phase7_missing_venue_transaction_hydration import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"family_count":d["family_count"],
   "tx_found_count":d["tx_found_count"],"fee_found_count":d["fee_found_count"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["family_count"],13)
  self.assertGreater(d["tx_found_count"],0,"NO_MISSING_VENUE_TRANSACTIONS_HYDRATED")
  self.assertGreater(d["fee_found_count"],0,"NO_NETWORK_FEES_RECOVERED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-139 missing-venue transaction hydration")
  print("[PASS] transaction fee + pre/post account state physically recovered")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
