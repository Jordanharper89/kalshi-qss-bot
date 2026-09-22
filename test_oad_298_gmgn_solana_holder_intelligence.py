import unittest
from qseries_v2.oracle_adapters.independent.oad_298_gmgn_solana_holder_intelligence import *
class T(unittest.TestCase):
    def test_physical(self):
        x=acquire_current_gmgn_token_holders()
        print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] raw_type=",type(x.raw).__name__)
        self.assertTrue(x.token_address); self.assertIsNotNone(x.raw); self.assertFalse(x.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-298 live GMGN Solana holder intelligence physically certified")
