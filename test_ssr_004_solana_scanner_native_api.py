import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_004_native_api import contract,payload
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_api(self):
  c=contract();h=payload(ROOT,"/health");p=payload(ROOT,"/plays")
  print("[STATE]",json.dumps(c,sort_keys=True))
  self.assertEqual(len(c["endpoints"]),6);self.assertFalse(h["execution_authority"]);self.assertFalse(p["execution_authority"])
  print("[PASS] SSR-004 standalone Solana Scanner native API")
if __name__=="__main__":unittest.main()
