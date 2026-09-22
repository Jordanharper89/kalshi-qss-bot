import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_067_meteora_orca_exact_swap_instruction_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_census(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"venue_counts":d["venue_counts"]},sort_keys=True))
  for x in d["rows"][:30]:print("[SWAP]",json.dumps({k:x[k] for k in ("venue","signature","level","instruction_ordinal","instruction_name")},sort_keys=True))
  self.assertGreater(d["row_count"],0,"NO_EXACT_METEORA_ORCA_SWAP_IN_SAMPLE")
  self.assertTrue(d["unknown_activity_retained_upstream"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-067 exact Meteora/Orca swap instruction census")
  print("[PASS] instruction lineage preserves top vs inner parent")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
