import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_007_empirical_play_ranker import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_ranker(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"ranked_play_count":d["ranked_play_count"]},sort_keys=True))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  for i,x in enumerate(d["plays"],1):self.assertEqual(x["rank"],i)
  print("[PASS] SSR-007 empirical live-play ranker")
if __name__=="__main__":unittest.main()
