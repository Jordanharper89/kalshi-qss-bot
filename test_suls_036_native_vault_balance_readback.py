import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_036_native_vault_balance_readback import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_readback(self):
  p,d=write(ROOT);print("[SNAPSHOT_COUNT]",d["snapshot_count"])
  for x in d["snapshots"]:print("[VAULT_SNAPSHOT]",json.dumps(x,sort_keys=True))
  if not d["snapshots"]:self.fail("NO_NATIVE_VAULT_SNAPSHOT")
  if not all(x["token"].get("amount") is not None and x["quote"].get("amount") is not None for x in d["snapshots"]):
   self.fail("NATIVE_VAULT_BALANCE_MISSING")
  print("[PASS] SULS-036 native vault balance readback")
if __name__=="__main__":unittest.main()
