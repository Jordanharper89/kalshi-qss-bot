import unittest
from qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import (
    canonical_sport_subdomain,disambiguate_semantic_domain
)

class T(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(canonical_sport_subdomain("MLB"),"baseball")
        self.assertEqual(canonical_sport_subdomain("NHL"),"hockey")
        self.assertEqual(canonical_sport_subdomain("SOCCER"),"soccer")
        self.assertEqual(canonical_sport_subdomain("UNKNOWN"),"UNKNOWN")
    def test_upstream_mlb(self):
        r=disambiguate_semantic_domain("Chicago C","sports","UNKNOWN","MLB")
        self.assertEqual((r.semantic_domain,r.semantic_subdomain),("sports","baseball"))
    def test_upstream_soccer(self):
        r=disambiguate_semantic_domain("Manchester City","sports","UNKNOWN","SOCCER")
        self.assertEqual((r.semantic_domain,r.semantic_subdomain),("sports","soccer"))
    def test_financial(self):
        r=disambiguate_semantic_domain("Target Price: $80,000","financial_markets","UNKNOWN","financial_price")
        self.assertEqual((r.semantic_domain,r.semantic_subdomain),("financial_markets","financial_price"))

if __name__=="__main__":
    print("="*100)
    print(" OAD-104 SPORT VOCABULARY CANONICALIZATION TEST")
    print("="*100)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] MLB -> baseball")
    print("[PASS] NHL -> hockey")
    print("[PASS] SOCCER -> soccer")
    print("[PASS] UNKNOWN remains UNKNOWN")
    print("[PASS] financial_markets:financial_price preserved")
    print("[DONE] OAD-104 SPORT VOCABULARY REBUILD CERTIFIED")
