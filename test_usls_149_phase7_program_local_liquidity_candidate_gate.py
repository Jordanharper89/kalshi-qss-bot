import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_149_phase7_program_local_liquidity_candidate_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  n=sum(v["with_candidate"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"candidate_rows":n,
   "family_support":d["family_support"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(n,0,"NO_PROGRAM_LOCAL_OPPOSING_FLOW_CANDIDATES")
  self.assertEqual(d["pool_vault_certification"],"NOT_CLAIMED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-149 program-local liquidity candidate gate")
  print("[PASS] opposing token-flow pairs retained as candidates, not mislabeled as certified vaults")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
