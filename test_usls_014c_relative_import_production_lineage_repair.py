import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_014c_relative_import_production_lineage_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("subscription_program_count","missing_program_ids",
   "contract_expanded","production_lineage_proven","visited_edge_count")},sort_keys=True))
  print("[LINEAGE]"," -> ".join(d["dependency_lineage"]) if d["dependency_lineage"] else "NONE")
  for x in d["sample_edges"]:print("[EDGE]",json.dumps(x))
  self.assertEqual(d["subscription_program_count"],14)
  self.assertEqual(d["missing_program_ids"],[])
  self.assertTrue(d["contract_expanded"])
  self.assertTrue(d["production_lineage_proven"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-014C relative-import production lineage certified")
  print("[PASS] 24/7 runtime reaches expanded universal subscription contract")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
