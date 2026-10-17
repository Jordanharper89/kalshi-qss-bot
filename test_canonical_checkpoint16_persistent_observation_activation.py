import ast
import unittest
from pathlib import Path

P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint16_persistent_observation_activation.py")

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_reuses_checkpoint15(self):
        self.assertIn("checkpoint15_cheapest_legal_fee_signed_simulation",self.s)

    def test_duration_configurable(self):
        self.assertIn("--seconds",self.s)
        self.assertIn("default=3600.0",self.s)

    def test_no_execution_bypass(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
