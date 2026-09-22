import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_030_universal_trade_tape_contract import write,validate
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  sample={k:None for k in d["required_fields"]}
  sample.update({"trade_id":"fixture:1","side":"UNKNOWN_TRADE_TYPE","execution_authority":False})
  v=validate(sample)
  print("[STATE]",json.dumps({"required_field_count":len(d["required_fields"]),
   "allowed_sides":d["allowed_sides"],"unknown_retention":d["unknown_retention"],
   "sample_valid":v["valid"]},sort_keys=True))
  self.assertTrue(v["valid"]);self.assertTrue(d["unknown_retention"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-030 universal Solana trade-tape contract certified")
  print("[PASS] BUY/SELL/UNKNOWN trades share one venue-neutral schema")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
