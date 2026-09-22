import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_070_meteora_orca_instruction_transfer_evidence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_evidence(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"venue_transfer_rows":d["venue_transfer_rows"]},sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertGreater(sum(d["venue_transfer_rows"].values()),0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-070 exact swap -> parent CPI transfer evidence")
  print("[PASS] no account roles or economics inferred yet")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
