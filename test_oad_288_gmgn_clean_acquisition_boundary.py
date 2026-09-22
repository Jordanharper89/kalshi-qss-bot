import unittest
from qseries_v2.oracle_adapters.independent.oad_288_gmgn_clean_acquisition_boundary import *
class T(unittest.TestCase):
 def test_physical(self):
  x=acquire_current_gmgn_token();print("[GMGN] token=",x.token_address);print("[GMGN] sections=",tuple(x.payload));self.assertTrue(x.token_address);self.assertFalse(x.execution_authority)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));raise SystemExit(0 if r.wasSuccessful() else 1)
