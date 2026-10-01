import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_065_live_token_candidate_viability_audit import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[DISCOVERY_SHAPE]",json.dumps(d["discovery_shape"],sort_keys=True))
  print("[SELECTED_TOKEN]",d["selected_token"])
  print("[CANDIDATE_COUNT]",d["candidate_count"])
  for x in d["results"]:
   print("[CANDIDATE]",json.dumps(x,sort_keys=True))
  print("[VIABLE_COUNT]",d["viable_count"])
  if d["candidate_count"]==0:self.fail("NO_DISCOVERED_SOLANA_TOKEN_CANDIDATES")
  print("[PASS] OSI-065D live token candidate viability audit")
  print("[TRADER] Separates token discovery from actually expandable live pools before atomic anchoring")
  print("[SCOPE] Read-only audit; no persistence and no prospective anchor mutation")

if __name__=="__main__":
 unittest.main()
