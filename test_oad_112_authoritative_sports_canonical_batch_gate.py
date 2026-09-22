import unittest
from qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation
from qseries_v2.oracle_adapters.independent.oad_112_authoritative_sports_canonical_batch_gate import build_authoritative_sports_canonical_batch

class T(unittest.TestCase):
    def test_batch(self):
        o=build_observation(
            source_id="mlb:game:1",provider="statsapi.mlb.com",sport_family="baseball",
            observation_type="official_game_schedule_state",subject="Houston Astros at New York Mets",
            observed_at="2026-08-28T12:00:00+00:00",
            source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
            payload={"gamePk":1},
        )
        r=build_authoritative_sports_canonical_batch((o,),"oad112-test")
        print("[CANONICAL]",len(r.canonical_observations))
        print("[PROVENANCE_VALIDATED]",r.provenance_validated)
        self.assertTrue(r.ready_for_existing_single_writer)
        self.assertEqual(r.provenance_validated,1)
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-112 authoritative sports canonical batch gate certified")
