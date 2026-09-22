import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106x_verified_exact_birth_dispatch_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_per_family=20)
  print("[STATE]",json.dumps({
   "raw_record_count":d["raw_record_count"],
   "eligible_successful_candidates":d["eligible_successful_candidates"],
   "dispatch_probe_count":d["dispatch_probe_count"],
   "successful_dispatch_count":d["successful_dispatch_count"],
   "rpc_error_count":d["rpc_error_count"],
   "exact_birth_count":d["exact_birth_count"]},sort_keys=True))
  for x in d["probes"]:
   print("[PROBE]",json.dumps({k:x[k] for k in ("family","signature","slot","rpc_error","tx_found","meta_err","dispatch")},sort_keys=True))
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(sum(d["eligible_successful_candidates"].values()),0,"NO_SUCCESSFUL_TARGET_FAMILY_CANDIDATES")
  self.assertGreater(d["dispatch_probe_count"],0,"NO_EXACT_DECODER_DISPATCH_ATTEMPTED")
  self.assertGreater(d["successful_dispatch_count"],0,"NO_VERIFIED_DECODER_EXECUTED")
  self.assertEqual(d["non_target_policy"],"RETAIN_RAW_UNRESOLVED_NO_INVENTED_DECODER")
  self.assertFalse(d["identity_materialization_certified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106X verified exact-birth dispatch gate")
  if d["exact_birth_count"]:
   print("[READY] exact prospective birth semantics detected; identity materialization is next")
  else:
   print("[WAIT] verified decoders executed; no exact birth in retained bounded cohort")
  print("[PASS] non-target families retained unresolved; no decoder invented")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
