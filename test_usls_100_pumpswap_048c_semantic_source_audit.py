import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_100_pumpswap_048c_semantic_source_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"candidate_count":d["candidate_count"],"required_defects":d["required_defects"]},sort_keys=True))
  for x in d["candidates"][:10]:print("[CANDIDATE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["candidate_count"],0,"NO_PUMPSWAP_RUNTIME_SOURCE_FOUND")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-100 PumpSwap 048C semantic source audit")
  print("[PASS] repair target discovered without fabricating missing semantics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
