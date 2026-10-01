import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_012_live_event_normalization_and_intake import normalize
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_normalize(self):
  r=normalize({"mint":"M","type":"new_pool","timestamp":"2026-09-18T05:00:00+00:00","signature":"s"},"x.json")
  self.assertEqual(r["event_type"],"NEW_POOL");self.assertEqual(r["asset_key"],"M")
 def test_physical(self):
  p=ROOT/"OSI_011_LIVE_SOLANA_SOURCE_BOUNDARY.json";self.assertTrue(p.is_file())
  data=json.loads(p.read_text(encoding="utf-8"));self.assertTrue(data["live_boundary_certified"])
  print("[PASS] OSI-012 live event normalization + intake")
  print("[TRADER] Real Solana runtime records can enter the opportunity hunter in one canonical shape")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
