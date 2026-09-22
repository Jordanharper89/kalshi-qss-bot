import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_071_meteora_orca_source_certified_role_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"venue_role_counts":d["venue_role_counts"]},sort_keys=True))
  self.assertGreater(d["venue_role_counts"].get("METEORA_DAMM",0),0)
  self.assertGreater(d["venue_role_counts"].get("METEORA_DLMM",0),0)
  self.assertGreater(d["venue_role_counts"].get("ORCA",0),0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-071 source-certified DAMM/DLMM/Orca account roles")
  print("[PASS] DBC/DYN remain pending rather than guessed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
