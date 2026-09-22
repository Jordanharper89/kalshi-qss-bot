import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_123_authoritative_sports_market_evidence_envelope import build_sports_market_evidence_envelopes

class T(unittest.TestCase):
    def test_envelope(self):
        d=SimpleNamespace(
            observation_id="o1",source_id="source.independent.mlb:game:1",sport_family="baseball",
            subject="Houston Astros at New York Mets",away_team="Houston Astros",home_team="New York Mets",
            evidence_type="official_game_schedule_state",independent_evidence=True)
        a=SimpleNamespace(observation_id="o1",market_id="KXTEST",association_strength="EXACT_TWO_TEAM_PAIR",candidate_only=True)
        r=build_sports_market_evidence_envelopes(SimpleNamespace(descriptors=(d,),associations=(a,)))
        print("[EVIDENCE_ENVELOPES]",len(r))
        print("[MARKET_ID]",r[0].market_id)
        print("[SOURCE_ID]",r[0].source_id)
        self.assertEqual(len(r),1)
        self.assertTrue(r[0].independent_evidence)
        self.assertIsNone(r[0].direction)
        self.assertIsNone(r[0].probability)
        self.assertFalse(r[0].execution_authority)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-123 authoritative sports market evidence envelope certified")
