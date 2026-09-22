from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_153_phase8_cross_launch_feature_contract.py"
TEST=ROOT/"test_usls_153_phase8_cross_launch_feature_contract.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def build():
 return {
  "revision":"USLS_153","phase":8,"capability":"CROSS_LAUNCH_FEATURE_LEARNING",
  "feature_families":[
   "trade_velocity","quote_volume_velocity","buy_sell_imbalance",
   "unique_trader_growth","repeat_trader_fraction","concentration",
   "price_path_momentum","mfe_mae","liquidity_change",
   "execution_deviation","latency","fee_load"],
  "horizons_seconds":[1,5,15,30,60,300,900],
  "learning_rules":{
   "future_leakage":"FORBIDDEN",
   "features_must_exist_at_or_before_prediction_time":True,
   "outcomes_must_be_strictly_after_prediction_time":True,
   "missing_feature":"RETAIN_NULL",
   "raw_frequency_is_not_calibrated_probability":True,
   "cross_venue_orientation":"DIRECTED_ASSET_PAIR_PRESERVED",
   "profitability_claim":"FORBIDDEN_WITHOUT_PROSPECTIVE_OOS_NET_EVIDENCE"},
  "phase7_dependency_state":"PARTIAL_EXECUTABLE_SUPPORT_ALLOWED_ONLY_AS_EXPLICIT_FEATURE_AVAILABILITY",
  "read_only":True,"execution_authority":False}

def write(root):
 d=build()
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_cross_launch_feature_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_153_phase8_cross_launch_feature_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertEqual(d["phase"],8)
  self.assertEqual(d["capability"],"CROSS_LAUNCH_FEATURE_LEARNING")
  self.assertEqual(d["learning_rules"]["future_leakage"],"FORBIDDEN")
  self.assertTrue(d["learning_rules"]["raw_frequency_is_not_calibrated_probability"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-153 Phase 8 cross-launch feature contract")
  print("[PASS] leakage-safe feature/outcome semantics frozen")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8"); TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT)); print("[PASS] test:",TEST.name); print("[PASS] execution_authority=FALSE")
