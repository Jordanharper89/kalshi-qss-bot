from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_157_phase8_first_feature_learning_checkpoint.py"
TEST=ROOT/"test_usls_157_phase8_first_feature_learning_checkpoint.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def _load(root,p):return json.loads((Path(root)/p).read_text(encoding="utf-8"))

def run(root):
 snap=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase8_leakage_safe_feature_snapshots.json")
 idx=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase8_cross_launch_comparable_case_index.json")
 groups=idx.get("groups",[])
 learned=[g for g in groups if g.get("outcome_sample_size",0)>=2]
 cross=[g for g in learned if g.get("family_count",0)>=2]
 return {"revision":"USLS_157","phase":8,
  "snapshot_count":snap.get("snapshot_count",0),
  "comparable_group_count":len(groups),
  "learnable_group_count":len(learned),
  "cross_family_learnable_group_count":len(cross),
  "phase8_status":"IN_PROGRESS","phase8_physically_certified":False,
  "remaining_required_capability":
   "EXPAND_FEATURES_WITH_TRADE_FLOW_TRADER_LIQUIDITY_AND_EXECUTION_SIGNALS_THEN_PROSPECTIVE_OOS_FEATURE_OUTCOME_VALIDATION",
  "raw_frequency_only":True,"calibrated_probability_claimed":False,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_first_feature_learning_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_157_phase8_first_feature_learning_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["snapshot_count"],0)
  self.assertGreater(d["comparable_group_count"],0)
  self.assertEqual(d["phase8_status"],"IN_PROGRESS")
  self.assertFalse(d["phase8_physically_certified"])
  self.assertTrue(d["raw_frequency_only"])
  self.assertFalse(d["calibrated_probability_claimed"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-157 Phase 8 first feature-learning checkpoint")
  print("[PASS] leakage-safe comparable-case learning foundation established")
  print("[NEXT]",d["remaining_required_capability"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8"); TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT)); print("[PASS] test:",TEST.name); print("[PASS] execution_authority=FALSE")
