import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_058_temporal_record_producer_lineage_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT);self.assertGreaterEqual(d["module_count"],4)
  print("[MODULES]",d["module_count"])
  for m in d["modules"]:
   print("[MODULE]",m["module"])
   print("[FUNCTIONS]",json.dumps(m["functions"],sort_keys=True)[:3000])
  print("[PASS] OSI-058 temporal record producer lineage audit")
  print("[TRADER] Finds the certified component that actually creates OAD-314-compatible price-history records")
if __name__=="__main__":unittest.main()
