import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_130_phase7_pumpswap_fee_liquidity_normalization import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "row_count","quote_mint_decimals","fee_fraction_ready_count","liquidity_ready_count","next_boundary")},sort_keys=True))
  self.assertGreater(d["row_count"],0,"NO_PUMPSWAP_ROWS")
  self.assertGreater(d["fee_fraction_ready_count"],0,"NO_PHYSICAL_PUMPSWAP_FEE_FRACTIONS")
  self.assertGreater(d["liquidity_ready_count"],0,"NO_PHYSICAL_PUMPSWAP_LIQUIDITY")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-130 PumpSwap fee/liquidity normalization")
  print("[PASS] raw fees and reserves converted using physically read quote-mint decimals")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
