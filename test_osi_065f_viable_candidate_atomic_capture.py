import unittest,json
from datetime import datetime
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_065_short_horizon_temporal_accumulation import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[CANDIDATE_COUNT]",d["candidate_count"])
  print("[VIABLE_COUNT]",d["viable_count"])
  print("[ASSET]",d["asset_key"])
  print("[PAIR]",d["pair_address"])
  print("[ANCHOR_OBSERVATION]",d["anchor_observation_id"])
  print("[ANCHOR_AT]",d["anchor_at"])
  print("[RECORD_COUNT]",d["record_count"])
  anchor=datetime.fromisoformat(d["anchor_at"].replace("Z","+00:00"))
  for r in d["records"][1:]:
   t=datetime.fromisoformat(r["observed_at"].replace("Z","+00:00"))
   print("[RECORD]",json.dumps({
    "age_seconds":round((t-anchor).total_seconds(),3),
    "observed_at":r["observed_at"],
    "price_usd":r["payload"]["pools"][0]["price_usd"],
   },sort_keys=True))
  if d["viable_count"]<1:self.fail("NO_VIABLE_DISCOVERED_SOLANA_POOL")
  if d["record_count"]<5:self.fail("ATOMIC_TEMPORAL_CAPTURE_INSUFFICIENT_RECORDS")
  print("[PASS] OSI-065F viable-candidate atomic anchor + temporal capture")
  print("[TRADER] Chooses an actually expandable live pool, freezes it, and follows the same pair every 5 seconds")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
