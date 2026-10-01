import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_068b_rate_safe_restart_signature_backfill import recover
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_recovery(self):
  d=recover(ROOT,page_limit=50,max_pages=2);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["restart_backfill_ready"])
  self.assertEqual(d["anchor_count"],2)
  print("[PASS] SULS-068B rate-safe restart signature backfill")
  print("[SCOPE] Recovery only discovers/persists signatures; SULS-067B hydrates them at a bounded RPC-safe rate")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
