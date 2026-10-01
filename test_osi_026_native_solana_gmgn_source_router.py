import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_026_native_solana_gmgn_source_router import build_registry,write_registry
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_router(self):
  d=build_registry(ROOT);p=write_registry(ROOT)
  self.assertGreater(len(d["primary"]["native_solana"]),0);self.assertFalse(d["policy"]["coinbase_can_create_opportunity"]);self.assertFalse(d["execution_authority"])
  print("[REGISTRY]",p);print("[NATIVE_MODULES]",len(d["primary"]["native_solana"]));print("[GMGN_MODULES]",len(d["primary"]["gmgn"]))
  print("[COINBASE_CONTEXT_MODULES]",len(d["context_only"]["coinbase"]))
  print("[PASS] OSI-026 native Solana + GMGN source router")
  print("[TRADER] Native Solana creates opportunities; GMGN enriches; Coinbase only describes broader SOL regime")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
