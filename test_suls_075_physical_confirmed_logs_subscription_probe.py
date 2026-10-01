import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_075_physical_confirmed_logs_subscription_probe import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=run(ROOT);print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="notifications"},sort_keys=True))
  for n in d["notifications"][:6]:
   print("[NOTIFICATION]",json.dumps({"slot":n["slot"],"signature":n["signature"],"err":n["err"],"log_count":len(n["logs"])},sort_keys=True))
  if not d["connected"] or d["ack_count"]<2:self.fail("CONFIRMED_LOGS_SUBSCRIPTION_NOT_ACKNOWLEDGED")
  if d["notification_count"]<1:self.fail("NO_PHYSICAL_LOGS_NOTIFICATION")
  print("[PASS] SULS-075 physical confirmed logsSubscribe probe")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
