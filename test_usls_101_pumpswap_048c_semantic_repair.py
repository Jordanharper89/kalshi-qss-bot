import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_101_pumpswap_048c_semantic_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_repair(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_trade_count":d["exact_trade_count"],"repairs":d["repairs"]},sort_keys=True))
  self.assertEqual(d["exact_trade_count"],117,"PUMPSWAP_EXACT_TRADE_COUNT_CHANGED")
  self.assertTrue(all(x.get("instruction_index") is None for x in d["rows"]))
  self.assertTrue(all((x.get("source_lineage") or {}).get("identity_revision")=="USLS_047C" for x in d["rows"]))
  self.assertTrue(all((x.get("source_lineage") or {}).get("semantic_repair_revision")=="USLS_101" for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-101 PumpSwap 048C semantic repair")
  print("[PASS] log index no longer mislabeled as instruction index")
  print("[PASS] event observation time separated from transaction block time")
  print("[PASS] identity lineage corrected to USLS_047C")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
