import unittest
from qseries_v2.oracle_adapters.independent.oad_391_solana_production_learner_admission_contract import build_production_learner_admission_contract
class T(unittest.TestCase):
    def test_contract(self):
        x,batch=build_production_learner_admission_contract()
        print("[ADMISSION CONTRACT] runtime_inputs=",x.runtime_inputs)
        print("[ADMISSION CONTRACT] runner=",x.runner_path)
        print("[ADMISSION CONTRACT] callables=",x.runner_callables)
        print("[ADMISSION CONTRACT] durable_counter_count=",x.durable_counter_count)
        print("[ADMISSION CONTRACT] ready=",x.ready)
        self.assertTrue(x.ready)
        self.assertEqual(x.runtime_inputs,3)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-391 production learner admission contract ready")
