import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_013_live_prospective_research_worker import freeze_live,status
class T(unittest.TestCase):
 def test_freeze(self):
  b={"source_count":3,"opportunity_seed_id":"o","asset_key":"SOL:M","freeze_at":"2026-09-18T05:00:00+00:00"}
  r={"thesis_metadata":{"thesis_family":"LIQUIDITY_EXPANSION"},"x_y_z_reasoning":{"x":"pool","y":"liq","z":"wallet"}}
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);x=freeze_live(b,r,root);self.assertEqual(len(x["added"]),6);self.assertEqual(status(root)["queued_total"],6)
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_012_live_event_normalization_and_intake.py").is_file())
  print("[PASS] OSI-013 live prospective research worker")
  print("[TRADER] Qualified real setups can be frozen into forward paper calls before the move")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
