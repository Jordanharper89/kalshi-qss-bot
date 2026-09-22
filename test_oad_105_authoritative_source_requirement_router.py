import unittest
from qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import assign_source_requirement

class T(unittest.TestCase):
    def test_mlb_alias(self):
        r=assign_source_requirement("sports","MLB","UPSTREAM_SPORTS_PRESERVED")
        self.assertEqual(r.subdomain,"baseball"); self.assertTrue(r.authoritative_source_families)
    def test_soccer_alias(self):
        r=assign_source_requirement("sports","SOCCER","UPSTREAM_SPORTS_PRESERVED")
        self.assertEqual(r.subdomain,"soccer"); self.assertTrue(r.authoritative_source_families)
    def test_nhl_alias(self):
        r=assign_source_requirement("sports","NHL","UPSTREAM_SPORTS_PRESERVED")
        self.assertEqual(r.subdomain,"hockey"); self.assertTrue(r.authoritative_source_families)
    def test_financial(self):
        r=assign_source_requirement("financial_markets","financial_price","UPSTREAM_FINANCIAL_PRESERVED")
        self.assertTrue(r.authoritative_source_families)

if __name__=="__main__":
    print("="*100)
    print(" OAD-105 SPORT VOCABULARY SOURCE ROUTER TEST")
    print("="*100)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] MLB/SOCCER/NHL vocabulary canonicalized")
    print("[PASS] Every canonical sport family maps to an authoritative source requirement")
    print("[PASS] financial_markets source contract preserved")
    print("[DONE] OAD-105 SPORT VOCABULARY REBUILD CERTIFIED")
