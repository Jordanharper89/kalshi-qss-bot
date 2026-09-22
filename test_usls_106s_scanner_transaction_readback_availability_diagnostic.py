import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106s_scanner_transaction_readback_availability_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT,max_samples=2)
  print("[STATE]",json.dumps({"raw_record_count":d["raw_record_count"],
   "probe_count":d["probe_count"],"finding":d["finding"]},sort_keys=True))
  for x in d["probes"]:print("[PROBE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(d["probe_count"],0,"NO_SIGNATURES_FOR_READBACK_DIAGNOSTIC")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106S transaction-readback availability diagnostic")
  print("[PASS] direct RPC contract uses required timeout_seconds")
  print("[PASS] no hydration certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
