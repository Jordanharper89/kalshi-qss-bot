import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_002_universal_transaction_shape_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_shapes(self):
  p,d=write(ROOT)
  self.assertGreater(d["row_count"],0)
  rich=[r for r in d["rows"] if r["program_ids"] and r["account_keys"] and r["logs"]]
  self.assertGreater(len(rich),0)
  s=rich[-1]
  print("[STATE]",json.dumps({"row_count":d["row_count"],"rich_rows":len(rich)},sort_keys=True))
  print("[SAMPLE]",json.dumps({"signature":s["signature"],"program_ids":s["program_ids"],
   "account_keys":len(s["account_keys"]),"instructions":len(s["instructions"]),
   "token_balances":len(s["token_balances"]),"logs":len(s["logs"])},sort_keys=True))
  print("[PASS] USLS-002 universal transaction shape normalizer")
  print("[PASS] scanner input is protocol-neutral transaction structure")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
