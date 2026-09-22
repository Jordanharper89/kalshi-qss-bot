import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_033_universal_trade_tape_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_norm(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("row_count","buy_count","sell_count","amounts_pending_count","profitability_claimed")},sort_keys=True))
  for x in d["rows"][:40]:print("[TAPE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["row_count"],d["buy_count"]+d["sell_count"])
  self.assertEqual(d["amounts_pending_count"],d["row_count"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-033 Pump trades normalized into universal Solana tape schema")
  print("[PASS] side is exact; amounts remain explicitly pending rather than guessed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
