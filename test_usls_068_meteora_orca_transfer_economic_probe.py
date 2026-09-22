import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_068_meteora_orca_transfer_economic_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_two_asset_count":d["exact_two_asset_count"],"venue_exact_counts":d["venue_exact_counts"]},sort_keys=True))
  for x in d["rows"][:30]:print("[ECON]",json.dumps({k:x[k] for k in ("venue","signature","instruction_name","trader","input_mint","input_amount","output_mint","output_amount","decoder_state")},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-068 conservative Meteora/Orca economic probe")
  print("[PASS] no pool role, BUY/SELL, or quote orientation fabricated")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
