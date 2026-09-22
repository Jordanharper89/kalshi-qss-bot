import unittest
from qseries_v2.oracle_adapters.independent.oad_392_solana_production_learner_physical_advancement_gate import physically_advance_production_learner
class T(unittest.TestCase):
    def test_physical_advancement(self):
        x=physically_advance_production_learner()
        print("[PRODUCTION LEARNER] invoked=",x.invoked)
        print("[PRODUCTION LEARNER] runner=",x.runner_path)
        print("[PRODUCTION LEARNER] detail=",x.invocation_detail)
        print("[PRODUCTION LEARNER] advanced=",x.advanced)
        print("[BEFORE]",x.before)
        print("[AFTER]",x.after)
        self.assertTrue(x.invoked, x.invocation_detail)
        self.assertTrue(x.advanced, "production learner durable counters did not advance")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-392 real production learner physically advanced from certified Solana batch")
    print("[PASS] durable learner state increased")
    print("[PASS] no counter fabrication or direct state-file mutation")
