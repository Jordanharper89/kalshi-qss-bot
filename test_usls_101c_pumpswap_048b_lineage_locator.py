import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_101c_pumpswap_048b_lineage_locator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_locator(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"source_hits":len(d["source_hits"]),"json_candidates":len(d["json_candidates"])},sort_keys=True))
  for x in d["source_hits"][:15]:print("[SOURCE]",json.dumps(x,sort_keys=True))
  for x in d["json_candidates"][:20]:print("[JSON]",json.dumps(x,sort_keys=True))
  self.assertTrue(d["source_hits"] or d["json_candidates"],"NO_PUMPSWAP_048B_LINEAGE_FOUND")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-101C PumpSwap 048B lineage locator")
  print("[PASS] no semantic certification claimed")
if __name__=="__main__":unittest.main()
