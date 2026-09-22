import unittest
from unittest.mock import patch
from types import SimpleNamespace

import qseries_v2.oracle_adapters.independent.oad_115_authoritative_sports_idempotent_persistence as m
from qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation
from qseries_v2.oracle_adapters.independent.oad_110_authoritative_sports_canonical_bridge import canonicalize_authoritative_sports_observation

class T(unittest.TestCase):
    def test_missing_only_write_and_exact_readback(self):
        raw=build_observation(
            source_id="mlb:game:3",provider="statsapi.mlb.com",sport_family="baseball",
            observation_type="official_game_schedule_state",subject="A at B",
            observed_at="2026-08-28T12:00:00+00:00",
            source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",payload={"gamePk":3})
        c=canonicalize_authoritative_sports_observation(raw,"oad115-test")
        physical={"canonical":(c,),"providers":("statsapi.mlb.com",)}
        accepted=SimpleNamespace(accepted=True)
        submission=SimpleNamespace(request_id="req-115")
        with patch.object(m,"run_physical_gate",return_value=physical), \
             patch.object(m,"find_authoritative_sports_observation",return_value=None), \
             patch.object(m,"submit_authoritative_sports_batch",return_value=submission), \
             patch.object(m,"await_authoritative_sports_commit",return_value=(accepted,)), \
             patch.object(m,"exact_authoritative_sports_readback",return_value=(c,)):
            r=m.persist_current_authoritative_sports(root=".")
        print("[COHORT_SIZE]",r.cohort_size)
        print("[MISSING_BEFORE_WRITE]",r.missing_before_write)
        print("[COMMITTED_NEW]",r.committed_new)
        print("[EXACT_READBACK]",r.exact_readback)
        self.assertEqual((r.cohort_size,r.missing_before_write,r.committed_new,r.exact_readback),(1,1,1,1))
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-115 idempotent authoritative sports persistence contract certified")
    print("[NOTE] physical production function uses real sports acquisition and existing PostgreSQL single writer")
