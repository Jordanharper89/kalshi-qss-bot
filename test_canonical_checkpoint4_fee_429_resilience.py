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

    def test_fee_retry_present(self):
        self.assertIn(
            "[CHECKPOINT4_FEE_429_RETRY]",
            self.s,
        )

    def test_bounded_attempts(self):
        self.assertIn(
            "for attempt in range(6):",
            self.s,
        )

    def test_only_429_retried(self):
        self.assertIn(
            'getattr(exc,"code",None)!=429',
            self.s,
        )

    def test_fee_rpc_preserved(self):
        self.assertIn(
            '"getFeeForMessage"',
            self.s,
        )

    def test_economics_unchanged(self):
        self.assertIn(
            "after=gross-fee",
            self.s,
        )
        self.assertIn(
            "admitted=after>0",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
