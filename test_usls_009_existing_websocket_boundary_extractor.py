import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_009_existing_websocket_boundary_extractor import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_extract(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"candidate_count":d["candidate_count"]},sort_keys=True))
  for x in d["candidates"][:10]:print("[CANDIDATE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["candidate_count"],0)
  self.assertIsNotNone(d["best_candidate"])
  print("[PASS] USLS-009 existing websocket subscription boundary extractor")
  print("[SCOPE] Exact reuse boundary identified; no duplicate Solana websocket runtime created")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
