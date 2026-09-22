import unittest
from qseries_v2.oracle_adapters.independent.oad_302_solana_security_evidence_boundary import *
class T(unittest.TestCase):
    def test_physical(self):
        x=acquire_current_solana_security_evidence()
        print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] security_fields=",len(x.gmgn_security))
        self.assertTrue(x.token_address); self.assertIsInstance(x.gmgn_security,dict)
        self.assertTrue(x.provider_claim_only); self.assertFalse(x.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-302 GMGN Solana security evidence physically certified as provider claim")
