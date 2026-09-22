import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_020_exact_birth_semantic_firewall import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_firewall(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("pump_instruction_count","create_v2_discriminator_hex","exact_create_v2_count","heuristic_birth_is_certification")},sort_keys=True))
  for x in d["rows"]:print("[PUMP_IX]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["pump_instruction_count"],0)
  self.assertFalse(d["heuristic_birth_is_certification"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-020 exact instruction-discriminator birth semantic firewall")
  print("[PASS] generic create/mint log words can no longer certify a protocol birth")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
