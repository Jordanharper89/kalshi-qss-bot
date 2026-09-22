import unittest
from qseries_v2.oracle_pre_settlement_coverage import opc_026_full_page_coverage_admission as m
class T(unittest.TestCase):
 def test_contract(self):self.assertTrue(m.verify_opc_026_full_page_coverage_admission())
if __name__=="__main__":unittest.main(verbosity=2)
