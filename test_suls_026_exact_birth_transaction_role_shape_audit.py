import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_026_exact_birth_transaction_role_shape_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);self.assertTrue(d["rows"])
  for r in d["rows"]:
   print("[ACCOUNT_KEYS]",len(r["account_keys"]))
   print("[OUTER_INSTRUCTIONS]",len(r["outer_instructions"]))
   print("[INNER_GROUPS]",len(r["inner_instructions"]))
   print("[PRE_TOKEN_BALANCES]",len(r["pre_token_balances"]))
   print("[POST_TOKEN_BALANCES]",len(r["post_token_balances"]))
   print("[ROLE_SHAPE]",json.dumps(r,sort_keys=True)[:12000])
  print("[PASS] SULS-026 exact birth transaction role-shape audit")
if __name__=="__main__":unittest.main()
