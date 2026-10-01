import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_050_native_commitment_latency_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  for x in d["rows"]:print("[COMMITMENT]",json.dumps(x,sort_keys=True))
  print("[PROCESSED_MINUS_FINALIZED_SLOTS]",d["processed_minus_finalized_slots"])
  print("[CONFIRMED_MINUS_FINALIZED_SLOTS]",d["confirmed_minus_finalized_slots"])
  print("[PROCESSED_5S_POSSIBLE]",d["processed_5s_possible"])
  print("[CONFIRMED_5S_POSSIBLE]",d["confirmed_5s_possible"])
  if not any(x.get("ok") for x in d["rows"]):self.fail("NO_NATIVE_COMMITMENT_PROBE_SUCCEEDED")
  print("[PASS] SULS-050 native commitment latency probe")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
