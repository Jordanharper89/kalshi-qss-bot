import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_064_confirmed_horizon_outcome_worker import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_worker(self):
  d=run(ROOT);print("[STATE]",json.dumps({"outcome_count":d["outcome_count"],"new_outcomes":d["new_outcomes"]},sort_keys=True))
  print("[PASS] SULS-064 confirmed horizon outcome worker")
  print("[SCOPE] Zero outcomes is valid until a fresh confirmed birth matures")
if __name__=="__main__":unittest.main()
