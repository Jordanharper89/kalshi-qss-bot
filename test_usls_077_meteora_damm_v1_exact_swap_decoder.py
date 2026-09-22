import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_077_meteora_damm_v1_exact_swap_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_decode(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_swap_count":d["exact_swap_count"]},sort_keys=True))
  for x in d["rows"][:20]:print("[SWAP]",json.dumps({k:x[k] for k in ("signature","level","instruction_ordinal","pool","trader")},sort_keys=True))
  self.assertGreater(d["exact_swap_count"],0,"NO_EXACT_DAMM_V1_SWAP_FOUND")
  self.assertTrue(all(x["pool"] and x["user_source"] and x["user_destination"] and x["trader"] for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-077 DAMM v1 exact swap + source-certified account roles")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
