import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_199_crypto_continuous_verified_learned_case_formation as m

class T(unittest.TestCase):
    def test_idempotent_binding(self):
        outcome=SimpleNamespace(experience_id="e1",asset="BTC")
        maturity=SimpleNamespace(outcomes=(outcome,))
        exp=SimpleNamespace(experience_id="e1",asset="BTC")
        rb=SimpleNamespace(records=(exp,))
        persisted=SimpleNamespace(already_present=1,committed_new=0,exact_readback=1)
        with patch.object(m,"mature_continuous_crypto_outcomes",return_value=maturity), \
             patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \
             patch.object(m,"persist_verified_learned_cases",return_value=persisted):
            r=m.form_continuous_verified_learned_cases()
        print("[MATCHES]",r.candidate_matches); print("[ALREADY_PRESENT]",r.already_present); print("[READBACK]",r.exact_readback)
        self.assertTrue(r.physical_ready)
        self.assertEqual(r.committed_new,0)
        self.assertEqual(r.already_present,1)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-199 continuous verified learned-case formation + idempotency certified")
