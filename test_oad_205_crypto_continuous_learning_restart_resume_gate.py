import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_205_crypto_continuous_learning_restart_resume_gate as m
class T(unittest.TestCase):
    def test_resume(self):
        before=SimpleNamespace(cycle_sequence=7,state_hash="a"*64,parent_state_hash="b"*64)
        after=SimpleNamespace(cycle_sequence=8,state_hash="c"*64,parent_state_hash="a"*64)
        cycle=SimpleNamespace(checkpoint_after=8,physical_ready=True)
        with patch.object(m,"read_checkpoint",side_effect=[before,after]), \
             patch.object(m,"verify_checkpoint",return_value=True), \
             patch.object(m,"run_crypto_continuous_learning_worker_cycle",return_value=cycle):
            r=m.verify_crypto_learning_restart_resume()
        print("[RESUME]",r.checkpoint_before_restart,"->",r.checkpoint_after_resume)
        print("[CHAIN]",r.hash_chain_resume)
        self.assertTrue(r.physical_ready)
        self.assertTrue(r.monotonic_resume)
        self.assertTrue(r.hash_chain_resume)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-205 durable restart/resume checkpoint gate certified")
