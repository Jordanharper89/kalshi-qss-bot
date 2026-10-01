import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState,contract
class T(unittest.TestCase):
 def test_core(self):
  with tempfile.TemporaryDirectory() as td:
   s=RuntimeState(td);a=s.boot();b=s.running(cycle_count=1,prospective_cases=11)
   self.assertEqual(a["status"],"STARTING");self.assertEqual(b["status"],"RUNNING");self.assertEqual(b["cycle_count"],1);self.assertFalse(b["execution_authority"])
   self.assertTrue((Path(td)/contract()["state_path"]).exists())
  print("[STATE]",json.dumps(contract(),sort_keys=True));print("[PASS] SSR-001 standalone Solana profitability runtime core")
if __name__=="__main__":unittest.main()
