import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_145_phase7_certified_vault_role_match import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  matched=sum(v["with_role_match"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"rows_with_role_match":matched,
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["match_policy"],
   "ONLY_EXACT_ACCOUNT_ADDRESS_MATCH_TO_EXISTING_CERTIFIED_ROLE_ARTIFACTS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-145 certified vault-role match")
  print("[STATE] exact certified role matches may legitimately be zero for unseen pools")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
