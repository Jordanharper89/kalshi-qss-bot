import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_127_phase7_physical_friction_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["phase"],7)
  self.assertGreater(d["onchain_family_probe_count"],0)
  self.assertGreater(d["source_native_evidence_rows"],0)
  self.assertEqual(d["phase7_status"],"IN_PROGRESS")
  self.assertFalse(d["phase7_physically_certified"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-127 Phase 7 physical-friction checkpoint")
  print("[PASS] physical friction evidence measured without premature executable-profit claims")
  print("[NEXT]",d["remaining_required_capability"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
