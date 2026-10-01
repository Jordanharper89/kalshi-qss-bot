import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_049_faster_native_trigger_foundation_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);print("[CANDIDATE_COUNT]",d["candidate_count"])
  for x in d["candidates"][:50]:
   print("[CANDIDATE]",x["path"],json.dumps(x["hits"],sort_keys=True))
   if x.get("excerpt"):print("[EXCERPT]");print(x["excerpt"][:3000])
  print("[PASS] SULS-049 faster native trigger foundation audit")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
