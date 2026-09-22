import unittest
from qseries_v2.oracle_adapters.independent.oad_067_independent_physical_single_writer_persistence import *
class T(unittest.TestCase):
    def test_physical(self):
        r=persist_fresh_independent_batch(timeout_seconds=120.0)
        print("[PHYSICAL] requested=",r.requested);print("[PHYSICAL] committed=",r.committed);print("[PHYSICAL] request_id=",r.request_id)
        print("[PHYSICAL] observation_ids=",r.observation_ids)
        self.assertGreater(r.requested,0);self.assertEqual(r.requested,r.committed)
if __name__=="__main__":
    print("="*88);print(" OAD-067 PHYSICAL CERTIFICATION TEST");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        print("[NOTE] Physical gate requires OPH-021 canonical writer RUNNING, normally via Oracle Live Runtime.")
        raise SystemExit(1)
    print("[PASS] Real independent observations committed through OPH single-writer path");print("[DONE] OAD-067 CERTIFIED")
