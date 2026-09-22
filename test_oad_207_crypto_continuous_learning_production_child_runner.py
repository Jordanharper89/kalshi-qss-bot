import ast
import unittest
from pathlib import Path

ROOT=Path.cwd().resolve()
RUNNER=ROOT/"run_oad_207_crypto_continuous_learning_production_child.py"

class T(unittest.TestCase):
    def test_runner_contract(self):
        src=RUNNER.read_text(encoding="utf-8")
        tree=ast.parse(src)
        self.assertIn("run_resilient_crypto_learning_worker",src)
        self.assertIn("--check",src)
        self.assertIn("execution_authority=FALSE",src)
        self.assertNotIn("execution_authority=TRUE",src)
        self.assertIn("probability_enabled=FALSE",src)
        self.assertIn("direction_enabled=FALSE",src)
        self.assertTrue(any(isinstance(x,ast.FunctionDef) and x.name=="main" for x in tree.body))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-207 production child runner contract certified")
