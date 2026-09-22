import unittest
from unittest.mock import patch
from types import SimpleNamespace

from qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation
from qseries_v2.oracle_adapters.independent.oad_112_authoritative_sports_canonical_batch_gate import build_authoritative_sports_canonical_batch
from qseries_v2.oracle_adapters.independent.oad_113_authoritative_sports_single_writer_binding import submit_authoritative_sports_batch

class T(unittest.TestCase):
    def test_exact_existing_writer_reuse(self):
        o=build_observation(
            source_id="mlb:game:2",provider="statsapi.mlb.com",sport_family="baseball",
            observation_type="official_game_schedule_state",subject="A at B",
            observed_at="2026-08-28T12:00:00+00:00",
            source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",payload={"gamePk":2})
        batch=build_authoritative_sports_canonical_batch((o,),"oad113-test")
        with patch("qseries_v2.oracle_adapters.independent.oad_113_authoritative_sports_single_writer_binding.submit_independent_canonical_batch",
                   return_value=SimpleNamespace(request_id="req-1",observation_count=1)) as p:
            sub=submit_authoritative_sports_batch(batch)
        print("[REQUEST_ID]",sub.request_id)
        print("[OBSERVATION_COUNT]",sub.observation_count)
        p.assert_called_once()
        self.assertEqual(sub.observation_count,1)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-113 existing PostgreSQL single-writer binding certified")
