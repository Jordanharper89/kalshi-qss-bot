import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_020_live_throughput_observation_gate import observe
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_component_contract(self):
  self.assertTrue((ROOT/"run_osi_solana_intelligence_live.py").is_file())
  r=observe(ROOT,seconds=0,interval=.01);self.assertFalse(r["execution_authority"]);self.assertTrue(r["read_only"])
  print("[PASS] OSI-020B live throughput observation gate installed")
  print("[TRADER] This is the speedometer for the Solana hunter after Oracle restart")
  print("[SCOPE] Component certification only; live progression still requires physical observation")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
