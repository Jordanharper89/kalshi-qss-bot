import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint6_all_pairs_fee_ranked_sweep.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_all_sizes(self):
        for value in (
            "0.001",
            "0.010",
            "0.025",
            "0.050",
            "0.100",
            "0.180",
            "0.280",
            "0.500",
            "1.000",
            "1.400",
        ):
            self.assertIn(value,self.s)

    def test_both_directions(self):
        self.assertIn("METEORA_TO_PUMP",self.s)
        self.assertIn("PUMP_TO_METEORA",self.s)

    def test_local_positive_only_compile(self):
        self.assertIn(
            "if gross<=0:",
            self.s,
        )

    def test_real_fee(self):
        self.assertIn(
            "c4._message_fee_lamports(",
            self.s,
        )

    def test_compact_candidates(self):
        self.assertIn(
            "NO_COMPUTE_MEMO_REVERSE",
            self.s,
        )
        self.assertIn(
            "NO_COMPUTE_MEMO_FORWARD",
            self.s,
        )

    def test_no_sim_or_broadcast(self):
        self.assertNotIn("simulateTransaction",self.s)
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
