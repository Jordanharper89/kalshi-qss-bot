import unittest
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import *

class T(unittest.TestCase):
    def batch(self,n):
        return assemble_runtime_batch((build_runtime_input(n,"x","r"+str(n),"a"*64,{"n":n}),))
    def test_verifier(self): self.assertTrue(verify_ocl_027_incremental_learner_state_update_runtime())
    def test_chain(self):
        g=genesis_incremental_state();s=apply_runtime_batch(g,self.batch(1));self.assertEqual(s.parent_state_hash,g.state_hash)
    def test_replay_rejected(self):
        g=genesis_incremental_state();b=self.batch(1);s=apply_runtime_batch(g,b)
        with self.assertRaises(ValueError): apply_runtime_batch(s,b)

if __name__=="__main__":
    print("="*72);print(" OCL-027 CERTIFICATION TEST");print(" INCREMENTAL LEARNER STATE UPDATE RUNTIME");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Incremental hash-chained learner-state updates certified")
    print("[DONE] OCL-027 CERTIFIED")
