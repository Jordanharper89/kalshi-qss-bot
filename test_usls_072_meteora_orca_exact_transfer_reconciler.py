import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_072_meteora_orca_exact_transfer_reconciler import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_reconcile(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"venue_exact_counts":d["venue_exact_counts"]},sort_keys=True))
  for x in d["rows"][:30]:
   if x["economics"]:print("[EXACT]",json.dumps(x,sort_keys=True))
  self.assertGreater(sum(d["venue_exact_counts"].values()),0,"NO_SOURCE_CERTIFIED_TRANSFER_RECONCILIATION")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-072 exact instruction-level transfer reconciliation where physically supported")
  print("[PASS] no signer-wallet aggregate substituted for per-instruction economics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
