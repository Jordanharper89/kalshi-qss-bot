import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_021_decoder_readiness_truth_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_truth(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"ready_count":d["ready_count"],"certified_count":d["certified_count"]},sort_keys=True))
  for x in d["rows"]:print("[FAMILY]",json.dumps(x,sort_keys=True))
  self.assertTrue(all(not x["heuristic_birth_evidence_admissible"] for x in d["rows"]))
  self.assertTrue(any(x["family"]=="METEORA_DAMM" and x["exact_pool_identity_certified"] for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-021 decoder readiness truth repair")
  print("[PASS] USLS-019 heuristic PUMP_FUN selection is retired unless exact create_v2 is physically seen")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
