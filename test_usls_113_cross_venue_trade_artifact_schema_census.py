import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_113_cross_venue_trade_artifact_schema_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  covered=sum(v>0 for v in d["family_artifact_counts"].values())
  print("[STATE]",json.dumps({"artifact_count":d["artifact_count"],
   "covered_families":covered,"family_artifact_counts":d["family_artifact_counts"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  for x in d["artifacts"][:40]:print("[ARTIFACT]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["artifact_count"],0,"NO_CROSS_VENUE_TRADE_ARTIFACTS_DISCOVERED")
  self.assertGreaterEqual(covered,4,"INSUFFICIENT_CROSS_VENUE_ARTIFACT_COVERAGE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-113 cross-venue trade artifact schema census")
  print("[PASS] physical schemas inventoried before adapter wiring")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
