import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_022_exact_candidate_transaction_recovery import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_recover(self):
  p,d=write(ROOT);print("[TARGET_COUNT]",d["target_count"]);print("[RECOVERED_COUNT]",d["recovered_count"])
  for x in d["transactions"]:print("[TX_RECOVERY]",x["signature"],x["recovered"],json.dumps(x["envelope_fields"]))
  if d["target_count"]==0 or d["recovered_count"]!=d["target_count"]:self.fail("EXACT_CANDIDATE_TRANSACTION_NOT_RECOVERED")
  print("[PASS] SULS-022 exact candidate transaction recovery")
if __name__=="__main__":unittest.main()
