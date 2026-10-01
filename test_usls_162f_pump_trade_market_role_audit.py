import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162f_pump_trade_market_role_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["matched_trade_instructions"],0,"NO_KNOWN_CURVE_PUMP_TRADE_INSTRUCTIONS")
  self.assertTrue(d["all_observed_trade_types_certified"],"PUMP_MARKET_ACCOUNT_ROLE_NOT_STABLE_ENOUGH")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162F Pump trade market-role audit")
  print("[NEXT]",d["next_boundary"])
if __name__=="__main__":unittest.main()
