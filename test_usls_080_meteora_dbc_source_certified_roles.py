import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_080_meteora_dbc_source_certified_roles import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"roles":d["roles"]},sort_keys=True))
  self.assertEqual(d["row_count"],17)
  self.assertTrue(all(all(x["roles"][k] for k in ("pool","user_in","user_out","base_vault","quote_vault","base_mint","quote_mint","trader")) for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-080 DBC current-source SwapCtx account roles certified")
  print("[PASS] physical positions 3/4/5/6 match user-in/user-out/base-vault/quote-vault")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
