import unittest
from qseries_v2.oracle_adapters.independent.oad_389_solana_production_learning_runner_resolution import resolve_production_learning_runner
class T(unittest.TestCase):
    def test_resolution(self):
        x=resolve_production_learning_runner()
        print("[PRODUCTION RUNNER] resolved=",x.resolved,"path=",x.runner_path)
        print("[CALLABLES]",x.callable_names)
        print("[SIGNATURES]",x.signatures)
        self.assertTrue(x.resolved)
        self.assertTrue(x.runner_path)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-389 production learning runner resolved")
