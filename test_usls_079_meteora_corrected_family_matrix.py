import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_079_meteora_corrected_family_matrix import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_matrix(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"phase4_status":d["phase4_status"],
   "damm_v1_program_id_repaired":d["damm_v1_program_id_repaired"],"next_boundary":d["next_boundary"]},sort_keys=True))
  for v,x in d["matrix"].items():print("[VENUE]",v,json.dumps(x,sort_keys=True))
  self.assertTrue(d["damm_v1_program_id_repaired"])
  self.assertEqual(d["matrix"]["METEORA_DYN"]["status"],"EXACT_DAMM_V1_INSTRUCTION_ECONOMICS_CERTIFIED")
  self.assertEqual(d["phase4_status"],"IN_PROGRESS");self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-079 corrected Meteora family matrix")
  print("[NEXT] DBC_SOURCE_ROLE_CERTIFICATION_PLUS_MULTI_VENUE_UNIVERSAL_NORMALIZATION")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
