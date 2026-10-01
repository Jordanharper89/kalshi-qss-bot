import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_002_pool_birth_event_contract import write_fixture,verify
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,x=write_fixture(ROOT);self.assertTrue(verify(x));self.assertFalse(x.execution_authority)
  print("[PASS] SULS-002 canonical pool-birth event contract")
  print("[SCOPE] Contract certification only; fixture does not claim live observation")
if __name__=="__main__":unittest.main()
