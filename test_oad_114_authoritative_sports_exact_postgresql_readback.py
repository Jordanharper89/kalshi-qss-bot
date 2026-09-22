import unittest
from unittest.mock import patch
from types import SimpleNamespace

import qseries_v2.oracle_adapters.independent.oad_114_authoritative_sports_exact_postgresql_readback as m

class T(unittest.TestCase):
    def test_exact_reader_reuses_oad068(self):
        row=SimpleNamespace(observation_id="obs-1")
        with patch.object(m,"_existing_backend",return_value=object()) as b, \
             patch.object(m,"_existing_query_one",return_value=row) as q:
            got=m.find_authoritative_sports_observation("obs-1",root=".")
        print("[OBSERVATION_ID]",got.observation_id)
        b.assert_called_once()
        q.assert_called_once()
        self.assertEqual(got.observation_id,"obs-1")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-114 exact PostgreSQL readback reuse certified")
