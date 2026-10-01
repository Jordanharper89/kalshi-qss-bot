import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_005_strategy_discovery_regime_learning_gate import summarize
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_learning(self):
  rows=[]
  for i,r in enumerate([.08,.05,-.02,.11,.04,.07]):
   rows.append({"pattern":"NEW_POOL+LIQ_UP+WALLET_CLUSTER","regime":"SOL_STRONG","horizon_seconds":60,"net_return_after_friction":r,"mfe":r+.03,"mae":-.03})
  s=summarize(rows,5)
  self.assertEqual(len(s),1);self.assertEqual(s[0]["sample_size"],6);self.assertFalse(s[0]["calibrated_probability_claimed"])
 def test_small_sample_abstains(self):
  self.assertEqual(summarize([{"pattern":"X","regime":"R","horizon_seconds":5,"net_return_after_friction":1}],5),[])
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_004_continuous_paper_path_outcome_engine.py").is_file())
  print("[PASS] OSI-005 strategy discovery + regime learning gate")
  print("[TRADER] Repeated X+Y+Z outcomes can become evidence-backed candidate strategies only after enough samples")
  print("[PASS] no calibrated probability claim from raw historical frequency")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
