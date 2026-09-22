import unittest
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_208_crypto_learning_physical_launcher_admission_gate import evaluate_crypto_learning_launcher_admission
class T(unittest.TestCase):
    def test_physical(self):
        r=evaluate_crypto_learning_launcher_admission(Path.cwd())
        print("[LAUNCHER]",r.launcher_present)
        print("[CORE]",r.expected_core_present)
        print("[TRUTHFUL_HEALTH]",r.truthful_health_present)
        print("[RUNNER]",r.crypto_runner_present)
        print("[ALREADY_PRESENT]",r.crypto_child_already_present)
        print("[ADMITTED]",r.admitted)
        self.assertTrue(r.admitted)
        self.assertTrue(r.execution_boundary_preserved)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-208 physical Oracle launcher admission gate certified")
