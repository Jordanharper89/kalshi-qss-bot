import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint20_canonical_alt_bidirectional_compile.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_canonical_alt_required(self):
        self.assertIn(
            "canonical_alt.json",
            self.s,
        )
        self.assertIn(
            "_load_canonical_alt()",
            self.s,
        )

    def test_compile_uses_alt(self):
        self.assertIn(
            "[[canonical_alt]]",
            self.s,
        )
        self.assertNotIn(
            "candidate[\"instructions\"],\n            [[]],",
            self.s,
        )

    def test_compile_fail_visible(self):
        self.assertIn(
            "[CHECKPOINT20_COMPILE_HOLD]",
            self.s,
        )
        self.assertIn(
            'comp.get("error")',
            self.s,
        )

    def test_real_fee_preserved(self):
        self.assertIn(
            "c13._fee_for_message(",
            self.s,
        )

    def test_checkpoint19_reused(self):
        self.assertIn(
            "return c19.main()",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
