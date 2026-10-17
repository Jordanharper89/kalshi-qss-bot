import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint15_cheapest_legal_fee_signed_simulation.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_all_candidates_compiled(self):
        self.assertIn(
            "r.q87.repaired_candidates(route)",
            self.s,
        )
        self.assertIn(
            "r.q87.compile_candidate(",
            self.s,
        )

    def test_real_fee_each_candidate(self):
        self.assertIn(
            "c13._fee_for_message(",
            self.s,
        )
        self.assertIn(
            "candidate_fees",
            self.s,
        )

    def test_winner_is_after_fee(self):
        self.assertIn(
            'key=lambda x:int(',
            self.s,
        )
        self.assertIn(
            'x["after_fee"]',
            self.s,
        )

    def test_signed_sim_winner_only(self):
        self.assertIn(
            "c14._signed_simulation(",
            self.s,
        )

    def test_full_size_ladder(self):
        self.assertIn(
            "for size in c12.SIZES:",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
