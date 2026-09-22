import unittest
from qseries_v2.oracle_adapters.independent.oad_417_source_to_market_coverage_matrix import *
class T(unittest.TestCase):
 def test_matrix(self):
  x=build_source_to_market_coverage_matrix([{'ticker':'WX','title':'Will temperature exceed 100 F?'},{'ticker':'BTC','title':'Will Bitcoin exceed 100000?'}],'.'); self.assertEqual(len(x),2); self.assertEqual(x[0].state,'COVERED'); self.assertIn(x[1].state,('PARTIAL','COVERED'))
if __name__=='__main__':unittest.main(verbosity=2)
