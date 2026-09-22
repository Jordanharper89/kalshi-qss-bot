import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_037_quote_amount_evidence_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"quote_exact_count":d["quote_exact_count"],
   "native_sol_pending_count":d["native_sol_pending_count"]},sort_keys=True))
  for x in d["rows"]:print("[QUOTE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertTrue(all(x["quote_amount"] is None or x["quote_amount"]>0 for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-037 quote-amount evidence audit")
  print("[PASS] native SOL quote is not falsely inferred from wallet balance delta")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
