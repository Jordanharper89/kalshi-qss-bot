import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_014_program_registry_exact_readback import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_readback(self):
  p,d=write(ROOT);print("[ADDRESS_COUNT]",d["address_count"])
  for a in d["addresses"]:print("[PROGRAM_ID]",a,json.dumps(d["context_labels"].get(a,[])))
  if d["address_count"]==0:self.fail("NO_PROGRAM_IDS_FOUND")
  print("[PASS] SULS-014 exact program-registry readback")
if __name__=="__main__":unittest.main()
