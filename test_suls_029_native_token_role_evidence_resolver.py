import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_029_native_token_role_evidence_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_evidence(self):
  p,d=write(ROOT)
  for r in d["rows"]:
   print("[TARGET_ACCOUNTS]",len(r["target_accounts"]));print("[DISTINCT_MINTS]",json.dumps(r["distinct_mints"]))
   for x in r["target_token_balance_overlap"]:print("[TOKEN_ROLE_EVIDENCE]",json.dumps(x,sort_keys=True))
  if not any(r["target_token_balance_overlap"] for r in d["rows"]):self.fail("NO_TOKEN_BALANCE_ROLE_EVIDENCE")
  print("[PASS] SULS-029 native token-role evidence resolver")
if __name__=="__main__":unittest.main()
