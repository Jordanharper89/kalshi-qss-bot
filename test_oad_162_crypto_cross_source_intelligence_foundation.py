import unittest
from qseries_v2.oracle_adapters.independent.oad_162_crypto_cross_source_intelligence_foundation import verify_crypto_source_contracts
class T(unittest.TestCase):
    def test_contracts(self):
        c=verify_crypto_source_contracts()
        print("[SOURCES]",tuple(x.source_family for x in c))
        print("[MARKET_NATIVE_INDEPENDENT]",c[0].independent_evidence)
        print("[CHAIN_INDEPENDENT]",tuple(x.independent_evidence for x in c[1:]))
        self.assertEqual(len(c),4)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-162 crypto cross-source intelligence foundation certified")
