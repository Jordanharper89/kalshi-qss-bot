import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_105_phase5_physical_birth_trade_source_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_census(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"candidate_count":d["candidate_count"],"birth_candidates":d["birth_candidates"],"trade_candidates":d["trade_candidates"]},sort_keys=True))
  for x in d["candidates"][:40]:print("[SOURCE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["birth_candidates"],0,"NO_BIRTH_SOURCES_FOUND")
  self.assertGreater(d["trade_candidates"],0,"NO_TRADE_SOURCES_FOUND")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-105 Phase 5 physical birth/trade source census")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
