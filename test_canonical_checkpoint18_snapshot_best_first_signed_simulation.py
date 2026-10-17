import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint18_snapshot_best_first_signed_simulation.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_full_ladder_before_rpc(self):
        pricing=self.s.index("for size in c12.SIZES:")
        ranking=self.s.index("rows.sort(")
        compiling=self.s.index("c15._compile_all_legal(")
        self.assertLess(pricing,ranking)
        self.assertLess(ranking,compiling)

    def test_best_first(self):
        self.assertIn(
            'key=lambda x:int(x["local_net"])',
            self.s,
        )
        self.assertIn(
            "reverse=True",
            self.s,
        )

    def test_fallback_next_size(self):
        self.assertIn(
            "for rank,op in enumerate(rows,1):",
            self.s,
        )

    def test_pair_key_execution_reused(self):
        self.assertIn(
            "return c17.main()",
            self.s,
        )

    def test_signed_sim(self):
        self.assertIn(
            "c14._signed_simulation(",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
