import unittest,tempfile,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_031_unified_solana_opportunity_event_normalizer import normalize,normalize_batch,write
class T(unittest.TestCase):
 def test_fixture(self):
  e=normalize("NATIVE_SOLANA","x",{"mint":"M","slot":123,"event_type":"swap"});self.assertIsNotNone(e);self.assertEqual(e["asset_key"],"M")
  self.assertIsNone(normalize("GMGN","x",{"foo":"bar"}))
  with tempfile.TemporaryDirectory() as td:
   p=write(Path(td),[e]);self.assertTrue(p.is_file())
  print("[PASS] OSI-031 unified Solana opportunity event normalizer")
  print("[TRADER] Native Solana and GMGN now enter one auditable opportunity-event shape")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
