import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_073_meteora_dbc_physical_role_discovery import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_discovery(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"dbc_row_count":d["dbc_row_count"],
   "recurrent_transfer_touched_positions":d["recurrent_transfer_touched_positions"][:12],"role_certified":d["role_certified"]},sort_keys=True))
  self.assertGreater(d["dbc_row_count"],0);self.assertGreater(len(d["recurrent_transfer_touched_positions"]),0)
  self.assertFalse(d["role_certified"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-073 DBC physical role discovery evidence")
  print("[PASS] recurrent transfer-linked account positions measured; no guessed certification")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
