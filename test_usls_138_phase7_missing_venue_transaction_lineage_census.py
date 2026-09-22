import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_138_phase7_missing_venue_transaction_lineage_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"families_with_raw_tx":d["families_with_raw_tx"],
   "families_with_vault_or_role_evidence":d["families_with_vault_or_role_evidence"],
   "family_lineage":d["family_lineage"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(len(d["family_lineage"]),13)
  self.assertGreater(d["families_with_vault_or_role_evidence"],0,
                     "NO_POOL_OR_ACCOUNT_ROLE_LINEAGE_FOUND")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-138 missing-venue transaction lineage census")
  print("[PASS] pool/account/vault lineage measured before friction reconstruction")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
