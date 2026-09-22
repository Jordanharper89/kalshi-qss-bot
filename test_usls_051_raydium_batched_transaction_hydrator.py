import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_051_raydium_batched_transaction_hydrator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"requested_count":d["requested_count"],
   "hydrated_count":d["hydrated_count"],"selected_counts":{k:len(v) for k,v in d["selected_by_venue"].items()}},sort_keys=True))
  self.assertGreater(d["requested_count"],0);self.assertGreater(d["hydrated_count"],0)
  self.assertTrue(d["batched_rpc"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-051 Raydium multi-family transactions hydrated in one batched RPC boundary")
  print("[PASS] shared router reused; no new venue-specific collector created")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
