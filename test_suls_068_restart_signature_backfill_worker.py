import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_068_restart_signature_backfill_worker import recover
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_recovery(self):
  d=recover(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["restart_backfill_ready"]);self.assertEqual(d["anchor_count"],2)
  print("[PASS] SULS-068 restart signature backfill worker")
  print("[SCOPE] Zero recovered births is valid when no certified-family birth occurred across the gap")
if __name__=="__main__":unittest.main()
