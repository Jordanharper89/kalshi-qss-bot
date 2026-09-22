import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_109_pump_exact_trade_economic_path_materializer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"input_trade_count":d["input_trade_count"],"priced_trade_count":d["priced_trade_count"]},sort_keys=True))
  self.assertGreater(d["input_trade_count"],0,"NO_107E_EXACT_PUMP_TRADES")
  self.assertGreater(d["priced_trade_count"],0,"NO_PUMP_TRADE_PRICE_RECONSTRUCTED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-109 Pump exact-trade economic path materializer")
  print("[PASS] observed effective-price path reconstructed from exact trade transactions")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
