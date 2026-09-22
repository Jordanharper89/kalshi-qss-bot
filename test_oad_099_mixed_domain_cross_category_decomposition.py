import unittest
from qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import *

class T(unittest.TestCase):
    def test_mixed(self):
        rows=decompose_mixed_market({"ticker":"KXMVECROSSCATEGORY-X","title":"yes Novak Djokovic,no Target Price: $100"})
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0].domain,"sports")
        self.assertEqual(rows[1].domain,"financial_markets")
    def test_no_sports_none(self):
        rows=decompose_mixed_market({"ticker":"X","title":"yes Novak Djokovic"})
        self.assertFalse(any(x.domain=="sports" and x.subdomain=="NONE" for x in rows))

if __name__=="__main__":
    print("="*88);print(" OAD-099 CERTIFICATION TEST");print(" MIXED-DOMAIN CROSS-CATEGORY DECOMPOSITION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Mixed bundles preserve independent leg domains")
    print("[DONE] OAD-099 CERTIFIED")
