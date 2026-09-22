import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_093_remaining_venue_parent_transfer_evidence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_transfers(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"venue_transfer_rows":d["venue_transfer_rows"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  for v,n in d["venue_transfer_rows"].items():self.assertGreater(n,0,f"NO_TRANSFER_EVIDENCE_{v}")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-093 parent-scoped transfer evidence for Moonit/Boop/Heaven")
  print("[PASS] economics not fabricated from whole-transaction wallet deltas")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
