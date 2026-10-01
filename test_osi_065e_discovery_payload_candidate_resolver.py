import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_065_discovery_payload_candidate_resolver import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[DISCOVERY_RETURN_TYPE]",d["discovery_return_type"])
  print("[DECLARED_TOKEN_COUNT]",d["declared_token_count"])
  print("[TOKENS_CONTAINER_TYPE]",d["tokens_container_type"])
  print("[TOKEN_ENTRY_SHAPES]",json.dumps(d["token_entry_shapes"],sort_keys=True))
  print("[CANDIDATE_COUNT]",d["candidate_count"])
  for x in d["results"]:
   print("[CANDIDATE]",json.dumps(x,sort_keys=True))
  print("[VIABLE_COUNT]",d["viable_count"])
  print("[FIRST_VIABLE]",json.dumps(d["first_viable"],sort_keys=True))
  if d["candidate_count"]==0:self.fail("DISCOVERY_PAYLOAD_CONTAINED_NO_SOLANA_ADDRESSES")
  print("[PASS] OSI-065E discovery-payload candidate resolver")
  print("[TRADER] Reads the real discovered-token collection and separates currently expandable pools from stale candidates")
  print("[SCOPE] Read-only; no prospective anchor mutation")

if __name__=="__main__":
 unittest.main()
