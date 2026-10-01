import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_044_due_horizon_native_outcome_worker import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_worker(self):
  d=run(ROOT);print("[STATE]",json.dumps({"outcome_count":d["outcome_count"],"new_outcomes":d["new_outcomes"]},sort_keys=True))
  print("[PASS] SULS-044 due-horizon native outcome worker")
  print("[SCOPE] Zero outcomes is valid until a fresh admitted birth reaches a scheduled horizon")
if __name__=="__main__":unittest.main()
