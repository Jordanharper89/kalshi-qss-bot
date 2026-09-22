import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_144_phase7_live_token_account_delta_reconstruction import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  changed=sum(v["with_changes"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"rows_with_changes":changed,
   "family_support":d["family_support"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(changed,0,"NO_LIVE_TOKEN_ACCOUNT_DELTAS")
  self.assertIn("REQUIRES_CERTIFIED_MATCH",d["role_policy"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-144 live token-account delta reconstruction")
  print("[PASS] pre/post token balances reconstructed without inventing vault roles")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
