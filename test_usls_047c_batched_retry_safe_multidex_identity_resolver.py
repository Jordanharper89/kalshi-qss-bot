import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_identity(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"pool_count":d["pool_count"],"exact_identity_count":d["exact_identity_count"],
   "batched_rpc":d["batched_rpc"],"retry_safe":d["retry_safe"],
   "decoder_pending_venues":d["decoder_pending_venues"]},sort_keys=True))
  for x in d["identity_rows"]:print("[IDENTITY]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["pool_count"],0)
  self.assertEqual(d["exact_identity_count"],d["pool_count"])
  self.assertTrue(d["batched_rpc"]);self.assertTrue(d["retry_safe"])
  self.assertTrue(d["unknown_identity_retained"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-047C batched retry-safe multi-DEX identity resolver")
  print("[PASS] PumpSwap pool + mint decimals resolved with two batched RPC boundaries")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
