import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_014b_production_runtime_universal_subscription_lineage_gate_repair import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["subscription_program_count"],14)
  self.assertEqual(d["missing_program_ids"],[])
  self.assertTrue(d["contract_expanded"])
  self.assertTrue(d["production_lineage_proven"])
  self.assertGreaterEqual(len(d["dependency_lineage"]),2)
  self.assertFalse(d["execution_authority"])
  print("[LINEAGE]"," -> ".join(d["dependency_lineage"]))
  print("[PASS] USLS-014B production runtime universal subscription lineage certified")
  print("[PASS] 24/7 runtime reaches the expanded 14-program subscription contract")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
