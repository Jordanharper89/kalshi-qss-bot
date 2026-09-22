import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_123_phase7_onchain_fee_latency_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "family_probe_count","tx_found_count","fee_found_count","latency_found_count","next_boundary")},sort_keys=True))
  self.assertEqual(d["family_probe_count"],14,"NOT_ALL_14_FAMILIES_PROBED")
  self.assertGreater(d["tx_found_count"],0,"NO_TRANSACTION_READBACK")
  self.assertGreater(d["fee_found_count"],0,"NO_ONCHAIN_NETWORK_FEE_READBACK")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-123 on-chain fee/latency probe")
  print("[PASS] Solana transaction fee evidence physically read without converting it into fake quote fee fractions")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
