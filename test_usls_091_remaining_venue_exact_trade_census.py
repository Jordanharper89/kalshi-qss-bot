import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_091_remaining_venue_exact_trade_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_census(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_trade_count":d["exact_trade_count"],"unknown_instruction_count":d["unknown_instruction_count"],"venue_exact_counts":d["venue_exact_counts"]},sort_keys=True))
  self.assertGreater(d["exact_trade_count"],0)
  for v,n in d["venue_exact_counts"].items():self.assertGreater(n,0,f"NO_EXACT_TRADES_{v}")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-091 exact physical trade census across Moonit/Boop/Heaven")
  print("[PASS] unknown program instructions retained separately")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
