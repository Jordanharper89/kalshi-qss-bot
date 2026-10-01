import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_003_physical_multi_launcher_discovery import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[CANDIDATE_TOKENS]",d["candidate_tokens"]);print("[EVENT_COUNT]",d["event_count"]);print("[FAMILY_COUNTS]",json.dumps(d["family_counts"],sort_keys=True))
  for x in d["events"][:20]:print("[BIRTH_EVENT]",json.dumps(x,sort_keys=True))
  if d["event_count"]==0:self.fail("NO_PHYSICAL_SOLANA_POOL_EVENTS")
  print("[PASS] SULS-003 physical multi-launcher discovery")
  print("[SCOPE] Observed-family coverage only; universal launcher coverage remains unclaimed")
if __name__=="__main__":unittest.main()
