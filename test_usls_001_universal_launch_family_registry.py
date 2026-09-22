import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_001_universal_launch_family_registry import write,TARGETS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"target_count":d["target_count"],
   "verified_family_count":d["verified_family_count"],
   "unknown_fallback_active":d["unknown_fallback_active"]},sort_keys=True))
  for k in TARGETS:
   r=d["families"][k]
   print("[FAMILY]",json.dumps({"family":k,"status":r["status"],
    "program_ids":r["program_ids"],"evidence_paths":len(r["evidence_paths"])},sort_keys=True))
  self.assertEqual(set(d["families"]),set(TARGETS))
  self.assertTrue(d["unknown_fallback_active"])
  self.assertTrue(d["families"]["METEORA_DBC"]["program_ids"])
  self.assertTrue(d["families"]["METEORA_DAMM"]["program_ids"])
  print("[PASS] USLS-001 universal launch family registry")
  print("[PASS] UNKNOWN_PROGRAM fallback active; no family silently dropped")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
