import unittest
from unittest.mock import patch
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_118_persisted_authoritative_sports_cohort as m

class T(unittest.TestCase):
    def test_exact_persisted_cohort(self):
        rows=(SimpleNamespace(observation_id="o1"),SimpleNamespace(observation_id="o2"))
        p=SimpleNamespace(observation_ids=("o1","o2"),providers=("statsapi.mlb.com",),committed_new=2)
        with patch.object(m,"persist_current_authoritative_sports",return_value=p), \
             patch.object(m,"exact_authoritative_sports_readback",return_value=rows):
            r=m.load_persisted_authoritative_sports_cohort(root=".")
        print("[COHORT_SIZE]",r.cohort_size)
        print("[OBSERVATION_IDS]",r.observation_ids)
        self.assertEqual(r.cohort_size,2)
        self.assertEqual(r.observation_ids,("o1","o2"))
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-118 exact persisted authoritative sports cohort certified")
