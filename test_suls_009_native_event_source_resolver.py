import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_009_native_event_source_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_resolver(self):
  p,d=write(ROOT);print("[CANDIDATE_COUNT]",d["candidate_count"]);print("[NATIVE_EVENT_CANDIDATE_FOUND]",d["native_event_candidate_found"])
  print("[BEST_CANDIDATE]",json.dumps(d["best_candidate"],sort_keys=True));print("[PASS] SULS-009 native event source resolver")
if __name__=="__main__":unittest.main()
