import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_004_universal_birth_event_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_normalizer(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "event_count","identity_resolved_count","unresolved_birth_count","dropped_candidate_count")},sort_keys=True))
  self.assertGreater(d["event_count"],0)
  self.assertEqual(d["dropped_candidate_count"],0)
  self.assertGreater(d["identity_resolved_count"],0)
  for r in d["events"]:
   self.assertIn(r["canonical_state"],("IDENTITY_RESOLVED","UNRESOLVED_BIRTH"))
   self.assertFalse(r["execution_authority"])
  print("[PASS] USLS-004 universal birth event normalizer")
  print("[PASS] resolved and unresolved launches share one downstream contract")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
