import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_029_physical_solana_gmgn_endpoint_resolver import resolve,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=resolve(ROOT);p=write(ROOT)
  self.assertTrue(p.is_file());self.assertGreater(len(d["native_modules"]),0);self.assertFalse(d["execution_authority"])
  print("[ENDPOINTS]",p);print("[NATIVE_FILES]",d["native_file_count"]);print("[GMGN_FILES]",d["gmgn_file_count"])
  if d["physical_native_files"]:print("[TOP_NATIVE]",d["physical_native_files"][0])
  if d["physical_gmgn_files"]:print("[TOP_GMGN]",d["physical_gmgn_files"][0])
  print("[PASS] OSI-029 physical Solana/GMGN endpoint resolver")
  print("[TRADER] Maps certified source modules to the physical runtime files they already produce")
  print("[SCOPE] Read-only; no duplicate acquisition")
if __name__=="__main__":unittest.main()
