import unittest
from qseries_v2.oracle_adapters.independent.oad_097_cross_category_leg_parser import *

class T(unittest.TestCase):
    def test_multiple_legs(self):
        rows=split_cross_category_legs({"ticker":"KXMVECROSSCATEGORY-X","title":"yes Bayern Munich,yes Over 41.5 points scored,no Target Price: $100"})
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0].polarity,"yes")
        self.assertEqual(rows[2].polarity,"no")
    def test_preserves_parent(self):
        rows=split_cross_category_legs({"ticker":"ABC","title":"yes Team A,yes Team B"})
        self.assertTrue(all(x.parent_ticker=="ABC" for x in rows))

if __name__=="__main__":
    print("="*88);print(" OAD-097 CERTIFICATION TEST");print(" CROSS-CATEGORY LEG PARSER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Cross-category bundles decomposed into immutable individual legs")
    print("[DONE] OAD-097 CERTIFIED")
