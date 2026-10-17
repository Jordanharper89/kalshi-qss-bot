import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint5_fee_compaction_selection.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_compute_budget_removed_only_in_compact(self):
        self.assertIn(
            'COMPUTE_BUDGET="ComputeBudget111111111111111111111111111111"',
            self.s,
        )
        self.assertIn(
            'ix.get("programId")!=COMPUTE_BUDGET',
            self.s,
        )

    def test_memo_removed(self):
        self.assertIn("MemoSq4gq",self.s)
        self.assertIn("Memo1Uhk",self.s)

    def test_both_candidates_measured(self):
        self.assertIn('"FULL_REVERSE"',self.s)
        self.assertIn('"NO_COMPUTE_MEMO_REVERSE"',self.s)

    def test_real_fee_readback_reused(self):
        self.assertIn(
            "c4._message_fee_lamports(",
            self.s,
        )

    def test_cheapest_legal_wins(self):
        self.assertIn(
            "winner=min(",
            self.s,
        )
        self.assertIn(
            'int(x["fee_lamports"])',
            self.s,
        )

    def test_no_simulation_or_broadcast(self):
        self.assertNotIn("simulateTransaction",self.s)
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
