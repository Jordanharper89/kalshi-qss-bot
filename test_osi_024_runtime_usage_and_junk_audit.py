import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_024_runtime_usage_and_junk_audit import audit,write_report
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write_report(ROOT)
  self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[REPORT]",p);print("[FILE_COUNT]",d["file_count"]);print("[TOTAL_BYTES]",d["total_bytes"])
  print("[OVER_1GB]",len(d["over_1gb"]));print("[OVER_100MB]",len(d["over_100mb"]))
  if d["largest_files"]:print("[LARGEST]",json.dumps(d["largest_files"][0],sort_keys=True))
  print("[PASS] OSI-024 runtime usage and junk audit")
  print("[TRADER] Measures what is actually consuming disk/runtime attention before cleanup")
  print("[SCOPE] Read-only inventory; nothing deleted")
if __name__=="__main__":unittest.main()
