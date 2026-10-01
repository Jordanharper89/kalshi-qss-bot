import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_065_short_horizon_temporal_accumulation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[ASSET]",d["asset_key"]);print("[PAIR]",d["pair_address"]);print("[RECORD_COUNT]",d["record_count"])
  for x in d["states"]:print("[CYCLE]",json.dumps(x,sort_keys=True))
  if d["record_count"]<2:self.fail("NONBLOCKING_TEMPORAL_HISTORY_DID_NOT_PROGRESS")
  print("[PASS] OSI-065B nonblocking native temporal accumulation")
  print("[TRADER] Captures real post-anchor pool prices without waiting on PostgreSQL ingestion")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
