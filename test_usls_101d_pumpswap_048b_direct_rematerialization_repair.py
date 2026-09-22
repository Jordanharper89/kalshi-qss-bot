import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_101d_pumpswap_048b_direct_rematerialization_repair import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_repair(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "source_revision":d["source_revision"],
   "source_exact_list_key":d["source_exact_list_key"],
   "exact_trade_count":d["exact_trade_count"],
   "source_pending_raw_count":d["source_pending_raw_count"],
   "repairs":d["repairs"]},sort_keys=True))
  self.assertEqual(d["source_revision"],"USLS_048B")
  self.assertEqual(d["exact_trade_count"],117,"PUMPSWAP_048B_EXACT_COUNT_NOT_117")
  self.assertTrue(all(x.get("instruction_index") is None for x in d["rows"]))
  self.assertTrue(all((x.get("source_lineage") or {}).get("identity_revision")=="USLS_047C" for x in d["rows"]))
  self.assertTrue(all((x.get("source_lineage") or {}).get("semantic_repair_revision")=="USLS_101D" for x in d["rows"]))
  self.assertTrue(all(x.get("block_time") is None for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-101D direct USLS-048B rematerialization recovered 117 exact PumpSwap trades")
  print("[PASS] 048C semantic defects repaired without reconstructing from raw 046B population")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
