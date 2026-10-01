import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_061_oad314_pending_case_factory import build,HORIZONS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=build(ROOT);self.assertEqual(d["case_count"],len(HORIZONS));self.assertFalse(d["execution_authority"])
  print("[ASSET]",d["asset_key"]);print("[PAIR]",d["pair_address"]);print("[ANCHOR_OBSERVATION]",d["anchor_observation_id"])
  for c in d["cases"]:print("[CASE]",c.experience_id,c.horizon_seconds,c.snapshot_at)
  print("[PASS] OSI-061 OAD-314 pending-case factory")
  print("[TRADER] Builds real 5s/15s/30s/60s/5m/15m outcome-pending cases from the resolved live token")
if __name__=="__main__":unittest.main()
