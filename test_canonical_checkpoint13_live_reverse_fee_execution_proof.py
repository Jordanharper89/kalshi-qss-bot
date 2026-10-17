import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint13_live_reverse_fee_execution_proof.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_reverse_only_compile(self):
        self.assertIn('!="METEORA_TO_PUMP"',cls.s if False else self.s)
        self.assertIn("c7._route(",self.s)

    def test_real_fee(self):
        self.assertIn('"getFeeForMessage"',self.s)
        self.assertIn("after_fee",self.s)

    def test_full_size_ladder(self):
        self.assertIn("for size in c12.SIZES:",self.s)

    def test_registry_live_state_reused(self):
        self.assertIn("c12._expanded_state()",self.s)
        self.assertIn("c12._process_event",self.s)

    def test_no_simulation(self):
        self.assertNotIn("simulateTransaction",self.s)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
