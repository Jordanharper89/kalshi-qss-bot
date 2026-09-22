import unittest
from qseries_v2.oracle_adapters.independent.oad_306_solana_launch_security_single_writer_persistence import *
class T(unittest.TestCase):
    def test_physical(self):
        r=persist_current_solana_launch_security()
        print("[PHYSICAL] token=",r.token_address); print("[PHYSICAL] already_present=",r.already_present); print("[PHYSICAL] committed_new=",r.committed_new); print("[PHYSICAL] exact_readback=",r.exact_readback); print("[PHYSICAL] observation_ids=",r.observation_ids)
        self.assertEqual(r.raw_observations,2); self.assertEqual(r.canonical_observations,2); self.assertEqual(r.already_present+r.committed_new,2); self.assertEqual(r.exact_readback,2); self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-306 launch/security evidence persisted through universal single writer")
    print("[PASS] exact 2/2 observation-ID PostgreSQL readback certified")
