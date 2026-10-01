import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_002_profit_hunt_worker import cycle,contract
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  d=cycle(ROOT,dry_run=True);c=contract();print("[STATE]",json.dumps(c,sort_keys=True))
  self.assertEqual(len(c["pipeline"]),4);self.assertTrue(c["continuous"]);self.assertTrue(d["dry_run"]);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-002 continuous profit-hunt worker dry-run contract")
if __name__=="__main__":unittest.main()
