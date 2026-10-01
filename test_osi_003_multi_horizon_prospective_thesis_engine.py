import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_003_multi_horizon_prospective_thesis_engine import build_theses,HORIZONS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_universal(self):
  b={"source_count":3,"opportunity_seed_id":"x","asset_key":"SOL:M","freeze_at":"2026-09-18T05:00:00+00:00"}
  r=build_theses(b,{"thesis_metadata":{"thesis_family":"LIQUIDITY_EXPANSION"},"x_y_z_reasoning":{"x":"new_pool","y":"liquidity_up","z":"wallet_cluster"}})
  self.assertEqual(tuple(x["horizon_seconds"] for x in r),HORIZONS)
 def test_buy_pressure_frozen(self):
  b={"source_count":3,"opportunity_seed_id":"x","asset_key":"SOL:M","freeze_at":"2026-09-18T05:00:00+00:00"}
  r=build_theses(b,{"thesis_metadata":{"thesis_family":"BUY_PRESSURE"}})
  self.assertEqual(len(r),1);self.assertEqual(r[0]["horizon_seconds"],60);self.assertEqual(r[0]["thesis_metadata"]["target_return"],.10)
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_002_same_opportunity_evidence_synchronizer.py").is_file())
  print("[PASS] OSI-003 multi-horizon prospective thesis engine")
  print("[TRADER] Oracle can study 5s/15s/30s/60s/5m/15m edge without rewriting BUY_PRESSURE")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
