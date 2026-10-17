import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint4_message_fee_economics_gate.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_real_fee_rpc(self):
        self.assertIn('"getFeeForMessage"',self.s)

    def test_fee_subtracted(self):
        self.assertIn("after=gross-fee",self.s)

    def test_positive_only_gate(self):
        self.assertIn("admitted=after>0",self.s)
        self.assertIn("HOLD_NONPOSITIVE_AFTER_MESSAGE_FEE",self.s)

    def test_scope_is_honest(self):
        self.assertIn(
            "priority_fee_and_simulation_pending=True",
            self.s,
        )

    def test_no_simulation(self):
        self.assertNotIn("simulateTransaction",self.s)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)
        self.assertNotIn(".send(",self.s)

    def test_reuses_clean_reverse_path(self):
        self.assertIn("c3._reverse_opportunity(",self.s)
        self.assertIn("c3._reverse_route(",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
