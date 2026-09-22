import unittest
from qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation
from qseries_v2.oracle_adapters.independent.oad_110_authoritative_sports_canonical_bridge import (
    canonicalize_authoritative_sports_observation, bridge_contract_record
)

class T(unittest.TestCase):
    def test_exact_existing_bridge(self):
        o = build_observation(
            source_id="mlb:test:1", provider="statsapi.mlb.com", sport_family="baseball",
            observation_type="official_game_schedule_state", subject="A at B",
            observed_at="2026-08-28T12:00:00+00:00",
            source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
            payload={"gamePk": 1},
        )
        c = canonicalize_authoritative_sports_observation(o, "oad110-test")
        r = bridge_contract_record()
        print("[BRIDGE_MODULE]", r["module"])
        print("[BRIDGE_CALLABLE]", r["callable"])
        print("[CANONICAL_SOURCE_ID]", c.source_id)
        self.assertEqual(r["callable"], "canonicalize_independent_observation")
        self.assertEqual(c.source_id, "source.independent."+o.source_id)
        self.assertFalse(r["execution_authority"])
        self.assertFalse(r["probability_enabled"])

if __name__ == "__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-110 exact repository bridge certified")
