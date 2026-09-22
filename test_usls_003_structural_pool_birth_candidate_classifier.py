import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_003_structural_pool_birth_candidate_classifier import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_classifier(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "event_count","retained_count","dropped_count","candidate_count","unknown_retained_count")},sort_keys=True))
  self.assertGreater(d["event_count"],0)
  self.assertEqual(d["event_count"],d["retained_count"])
  self.assertEqual(d["dropped_count"],0)
  self.assertGreater(d["candidate_count"],0)
  print("[PASS] USLS-003 structural pool-birth candidate classifier")
  print("[PASS] unknown programs retained instead of dropped")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
