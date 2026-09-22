import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_095b_moonit_sell_lamport_lineage_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"sell_rows":d["sell_rows"]},sort_keys=True))
  for x in d["rows"]:print("[SELL]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["sell_rows"],0);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-095B Moonit sell lamport lineage diagnostic")
  print("[PASS] no economics certification claimed")
if __name__=="__main__":unittest.main()
