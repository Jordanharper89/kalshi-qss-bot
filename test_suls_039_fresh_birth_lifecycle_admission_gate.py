import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_039_fresh_birth_lifecycle_admission_gate import gate,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[PHYSICAL_STATE]",json.dumps(d,sort_keys=True))
  src=ROOT/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
  original=src.read_text(encoding="utf-8")
  try:
   src.write_text(json.dumps({"events":[{"event_id":"x","block_time":100.0}]}),encoding="utf-8")
   f=gate(ROOT,103.0);self.assertEqual(f["fresh_birth_count"],1)
  finally:src.write_text(original,encoding="utf-8")
  print("[PASS] SULS-039 fresh-birth lifecycle admission gate")
  print("[SCOPE] Current historical event may be stale; prospective future births require <=5s admission")
if __name__=="__main__":unittest.main()
