import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_140_phase7_pool_vault_prepost_state_reconstructor import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  changed=sum(v["with_token_changes"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"rows_with_token_changes":changed,
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(changed,0,"NO_PRE_POST_TOKEN_ACCOUNT_CHANGES_RECOVERED")
  self.assertIn("NOT_GUESSED",d["liquidity_semantics"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-140 pool/vault pre-post state reconstructor")
  print("[PASS] token-account reserve state recovered without guessing pool-vault identity")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
