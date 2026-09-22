import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106m_scanner_lifecycle_state_materializer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_materializer(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "raw_record_count":d["raw_record_count"],"birth_record_count":d["birth_record_count"],
   "trade_record_count":d["trade_record_count"],"joined_trade_count":d["joined_trade_count"],
   "unresolved_trade_count":d["unresolved_trade_count"],"pending_birth_count":d["pending_birth_count"],
   "accounting_ok":d["accounting_ok"]},sort_keys=True))
  self.assertGreater(d["raw_record_count"],0)
  self.assertGreater(d["trade_record_count"],0)
  self.assertTrue(d["accounting_ok"],"TRADE_ACCOUNTING_LOSS")
  self.assertEqual(d["joined_trade_count"]+d["unresolved_trade_count"],d["trade_record_count"])
  self.assertEqual(d["unknown_retention"],"RETAIN_UNRESOLVED")
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106M scanner lifecycle-state materializer")
  print("[PASS] every persisted trade accounted for; unresolved birth lineage retained")
  print("[PASS] zero-birth tape remains scientifically valid and uncertified")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
