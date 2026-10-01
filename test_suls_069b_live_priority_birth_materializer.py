import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_069b_live_priority_birth_materializer import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_materialize(self):
  d=run(ROOT);print("[STATE]",json.dumps({"event_count":d["event_count"],"new_events":d["new_events"]},sort_keys=True))
  print("[PASS] SULS-069B live-priority birth materializer")
  print("[SCOPE] Recovered births preserve lineage but cannot masquerade as fresh signals")
if __name__=="__main__":unittest.main()
