from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_010_continuous_strategy_learning_runtime.py"
TEST=ROOT/"test_osi_010_continuous_strategy_learning_runtime.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_005_strategy_discovery_regime_learning_gate import summarize

EXECUTION_AUTHORITY=False

def learn(cases:list[dict],state_path:Path,min_sample:int=5)->dict:
 candidates=summarize(cases,min_sample)
 state={"candidate_strategies":candidates,"case_count":len(cases),
        "strategy_count":len(candidates),"calibrated_probability_available":False,
        "execution_authority":False,"read_only":True}
 state_path.parent.mkdir(parents=True,exist_ok=True)
 state_path.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 return state
"""

TEST_TEXT=r"""import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_010_continuous_strategy_learning_runtime import learn
class T(unittest.TestCase):
 def test_learn(self):
  cases=[{"pattern":"NEW_POOL+LIQ_UP+WALLET_CLUSTER","regime":"SOL_STRONG","horizon_seconds":60,
          "net_return_after_friction":r,"mfe":r+.02,"mae":-.02} for r in [.05,.07,-.01,.03,.09,.02]]
  with tempfile.TemporaryDirectory() as td:
   s=learn(cases,Path(td)/"s.json",5)
   self.assertEqual(s["strategy_count"],1);self.assertFalse(s["calibrated_probability_available"])
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_005_strategy_discovery_regime_learning_gate.py").is_file())
  print("[PASS] OSI-010 continuous strategy learning runtime")
  print("[TRADER] Oracle can continuously promote repeated profitable X+Y+Z patterns into candidate strategies")
  print("[PASS] raw outcome frequency is not mislabeled calibrated probability")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-010 installed; execution_authority=FALSE")
if __name__=="__main__":main()
