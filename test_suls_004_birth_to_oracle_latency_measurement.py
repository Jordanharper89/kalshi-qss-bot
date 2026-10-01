import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_004_birth_to_oracle_latency_measurement import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[MEASURED]",d["measured"]);print("[VALID_NONNEGATIVE]",d["valid_nonnegative"])
  print("[MIN_SECONDS]",d["min_seconds"]);print("[MEDIAN_SECONDS]",d["median_seconds"]);print("[MAX_SECONDS]",d["max_seconds"])
  for x in d["rows"][:20]:print("[LATENCY]",json.dumps(x,sort_keys=True))
  if d["valid_nonnegative"]==0:self.fail("NO_VALID_BIRTH_TO_ORACLE_LATENCY")
  print("[PASS] SULS-004 physical birth-to-Oracle latency measurement")
  print("[SCOPE] Measures current discovery latency; does not claim sub-second native birth detection")
if __name__=="__main__":unittest.main()
