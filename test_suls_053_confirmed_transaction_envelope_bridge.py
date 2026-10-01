import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_053_confirmed_transaction_envelope_bridge import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_bridge(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if d["block_count"]==0 or d["transaction_count"]==0:self.fail("CONFIRMED_TRANSACTION_ENVELOPE_BRIDGE_FAILED")
  print("[PASS] SULS-053 confirmed transaction envelope bridge")
if __name__=="__main__":unittest.main()
