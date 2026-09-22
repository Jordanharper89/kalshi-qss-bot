import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_120_current_market_sports_team_pair_index import candidate_markets_for_sports_descriptor

class T(unittest.TestCase):
    def test_exact_two_team_pair_only(self):
        d=SimpleNamespace(observation_id="o1",away_team="Houston Astros",home_team="New York Mets")
        markets=(
            {"ticker":"GOOD","title":"Houston Astros at New York Mets"},
            {"ticker":"ONE","title":"Will the Houston Astros win?"},
            {"ticker":"NOISE","title":"New York weather"},
        )
        r=candidate_markets_for_sports_descriptor(d,markets)
        print("[CANDIDATES]",[(x.market_id,x.association_strength) for x in r])
        self.assertEqual(tuple(x.market_id for x in r),("GOOD",))
        self.assertTrue(all(x.candidate_only for x in r))

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-120 exact two-team market candidate index certified")
