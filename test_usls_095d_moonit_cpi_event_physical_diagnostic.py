import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_095d_moonit_cpi_event_physical_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"candidate_count":d["candidate_count"],"top_prefixes":d["top_prefixes"],"top_programs":d["top_programs"]},sort_keys=True))
  for x in d["candidate_rows"][:100]:print("[CANDIDATE]",json.dumps(x,sort_keys=True))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-095D Moonit CPI-event physical diagnostic")
  print("[PASS] no economics certification claimed")
if __name__=="__main__":unittest.main()
