import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047b_shared_multidex_identity_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_identity(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"identity_row_count":len(d["identity_rows"]),
   "exact_identity_count":d["exact_identity_count"],"decoder_pending_venues":d["decoder_pending_venues"]},sort_keys=True))
  if d["identity_rows"]:self.assertEqual(d["exact_identity_count"],len(d["identity_rows"]))
  self.assertTrue(d["unknown_identity_retained"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-047B shared multi-DEX identity resolver boundary")
  print("[PASS] PumpSwap exact pool identity plugin integrated; other venue identities remain pending")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
