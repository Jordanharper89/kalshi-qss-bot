import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_079_event_driven_birth_hydration_worker import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=run(ROOT)
  print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="births"},sort_keys=True))
  if not d["connected"] or d["ack_count"]<2:self.fail("EVENT_DRIVEN_SUBSCRIPTIONS_NOT_READY")
  if d["notifications_examined"]<1:self.fail("NO_EVENT_DRIVEN_NOTIFICATIONS")
  print("[PASS] SULS-079 event-driven birth hydration worker")
  print("[SCOPE] Zero births is valid until exact birth logs are physically observed")
if __name__=="__main__":unittest.main()
