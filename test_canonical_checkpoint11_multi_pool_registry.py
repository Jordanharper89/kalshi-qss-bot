import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint11_multi_pool_registry.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_pair_identity(self):
        self.assertIn(
            'return token+"|"+pool',
            self.s,
        )

    def test_collision_gate(self):
        self.assertIn(
            "CHECKPOINT11_PAIR_KEY_COLLISION",
            self.s,
        )

    def test_registry_persisted(self):
        self.assertIn(
            "multi_dlmm_pair_registry.json",
            self.s,
        )

    def test_quoteability_required(self):
        self.assertIn(
            "if best is None or quotes<=0:",
            self.s,
        )

    def test_selected_and_alternate_preserved(self):
        self.assertIn(
            '"selected_legacy":',
            self.s,
        )
        self.assertIn(
            '"alternate_ready_count":',
            self.s,
        )

    def test_no_execution(self):
        self.assertNotIn(
            "simulateTransaction",
            self.s,
        )
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
