import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_017_token_pool_role_evidence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("row_count","token_candidate_rows","quote_resolved_rows")},sort_keys=True))
  for r in d["rows"]:print("[ROLE]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(d["token_candidate_rows"],0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-017 token/quote role evidence extracted from live transactions")
  print("[SCOPE] candidate token roles only; pool identity is not guessed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
