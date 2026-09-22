import unittest
from qseries_v2.oracle_adapters.independent.oad_390_solana_production_learner_state_baseline import capture_learner_state_baseline
class T(unittest.TestCase):
    def test_baseline(self):
        x=capture_learner_state_baseline()
        print("[STATE FILES]",x.files)
        print("[COUNTERS]",x.counters)
        self.assertGreater(len(x.files),0)
        self.assertGreater(len(x.counters),0)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-390 production learner durable-state baseline captured read-only")
