import unittest
from qseries_v2.oracle_adapters.independent.oad_289_gmgn_clean_single_writer_persistence import *
class T(unittest.TestCase):
 def test_physical(self):
  r=persist_current_gmgn();print("[PHYSICAL] token=",r.token_address);print("[PHYSICAL] already_present=",r.already_present);print("[PHYSICAL] committed_new=",r.committed_new);print("[PHYSICAL] exact_readback=",r.exact_readback);self.assertEqual(r.already_present+r.committed_new,3);self.assertEqual(r.exact_readback,3)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));raise SystemExit(0 if r.wasSuccessful() else 1)
