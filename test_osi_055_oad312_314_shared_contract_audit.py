import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_055_oad312_314_shared_contract_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  print("[SHARED_KEY_COUNT]",d["shared_key_count"]);print("[SHARED_KEYS]",json.dumps(d["shared_keys"]))
  if d["shared_key_count"]==0:self.fail("NO_OAD312_OAD314_SHARED_DATA_CONTRACT")
  print("[PASS] OSI-055 OAD-312/OAD-314 shared contract audit")
  print("[TRADER] Confirms the temporal history and outcome grader speak a common data language")
if __name__=="__main__":unittest.main()
