import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_013_exact_maturity_contract import certify
class T(unittest.TestCase):
 def test_contract(self):
  r=certify()
  self.assertEqual(r["exact_horizon"],60)
  self.assertEqual(r["friction_bps"],200)
  self.assertFalse(r["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
