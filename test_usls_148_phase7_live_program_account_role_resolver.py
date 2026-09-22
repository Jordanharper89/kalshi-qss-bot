import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_148_phase7_live_program_account_role_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  matched=sum(v["with_changed_program_accounts"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"matched_rows":matched,
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(matched,0,"NO_CHANGED_TOKEN_ACCOUNTS_INTERSECT_TARGET_PROGRAM_INSTRUCTIONS")
  self.assertFalse(d["vault_role_claimed"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-148 live program-account role resolver")
  print("[PASS] exact target-program instruction accounts intersected with physical token deltas")
  print("[PASS] no pool-vault role claimed yet")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
