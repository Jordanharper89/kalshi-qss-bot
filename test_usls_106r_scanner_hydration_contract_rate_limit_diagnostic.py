import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106r_scanner_hydration_contract_rate_limit_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT,max_samples=3)
  print("[STATE]",json.dumps({"raw_record_count":d["raw_record_count"],"probe_count":d["probe_count"],
   "finding":d["finding"],"rate_limit_probe_count":d["rate_limit_probe_count"]},sort_keys=True))
  for x in d["probes"]:print("[PROBE]",json.dumps(x,sort_keys=True))
  print("[HYDRATE_SOURCE]")
  for x in d["hydrate_source_excerpt"]:print(x)
  print("[RPC_SOURCE]")
  for x in d["rpc_source_excerpt"]:print(x)
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(d["probe_count"],0,"NO_SIGNATURES_FOR_DIAGNOSTIC")
  self.assertGreater(len(d["hydrate_source_excerpt"]),0,"HYDRATE_SOURCE_NOT_FOUND")
  self.assertGreater(len(d["rpc_source_excerpt"]),0,"RPC_SOURCE_NOT_FOUND")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106R hydration contract/rate-limit diagnostic")
  print("[PASS] no hydration certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
