import ast
import unittest
from pathlib import Path

P=Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "checkpoint17_pair_key_execution_templates.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_single_prewarm_handoff_present(self):
        self.assertIn(
            "CHECKPOINT17_SINGLE_PREWARM_HANDOFF",
            self.s,
        )
        self.assertIn(
            "duplicate_network_prewarm=False",
            self.s,
        )

    def test_checkpoint15_reuses_existing_warm_rows(self):
        self.assertIn(
            "return list(warmed)",
            self.s,
        )
        self.assertIn(
            "r.q25.install_hot_math_and_prewarm=(",
            self.s,
        )

    def test_state_drift_fails_closed(self):
        self.assertIn(
            "CHECKPOINT17_PREWARM_STATE_DRIFT",
            self.s,
        )
        self.assertIn(
            "if child_tokens!=parent_tokens:",
            self.s,
        )

    def test_original_prewarm_restored(self):
        self.assertIn(
            "old_prewarm=r.q25.install_hot_math_and_prewarm",
            self.s,
        )
        self.assertIn(
            "r.q25.install_hot_math_and_prewarm=old_prewarm",
            self.s,
        )

    def test_reverse_seed_fix_preserved(self):
        self.assertIn(
            "CHECKPOINT17_LEGACY_REVERSE_SEED",
            self.s,
        )
        self.assertIn(
            "CHECKPOINT17_REVERSE_SEED_ACCOUNT_INVARIANT",
            self.s,
        )

    def test_direction_guards_preserved(self):
        self.assertIn(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH",
            self.s,
        )
        self.assertIn(
            "expected_templates=expected_pairs*2",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )
        self.assertIn(
            "[BROADCAST] disabled",
            self.s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
