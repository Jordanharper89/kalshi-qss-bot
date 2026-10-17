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

    def test_reverse_uses_forward_seed_only_for_legacy_consumer(self):
        self.assertIn(
            "CHECKPOINT17_LEGACY_REVERSE_SEED",
            self.s,
        )
        self.assertIn(
            "seed_key=_direction_key(",
            self.s,
        )
        self.assertIn(
            "FORWARD,",
            self.s,
        )

    def test_quote_is_not_mutated(self):
        self.assertNotIn(
            'quote["swap_for_y"]=',
            self.s,
        )
        self.assertNotIn(
            'opportunity["mq"]["swap_for_y"]=',
            self.s,
        )

    def test_exact_reverse_quote_guard_preserved(self):
        self.assertIn(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH",
            self.s,
        )
        self.assertIn(
            "if quote_swap!=exact_swap:",
            self.s,
        )

    def test_reverse_seed_must_be_opposite(self):
        self.assertIn(
            "CHECKPOINT17_REVERSE_SEED_NOT_OPPOSITE",
            self.s,
        )
        self.assertIn(
            "if seed_swap==exact_swap:",
            self.s,
        )

    def test_source_destination_invariant(self):
        self.assertIn(
            "CHECKPOINT17_REVERSE_SEED_ACCOUNT_INVARIANT",
            self.s,
        )
        self.assertIn(
            "str(seed_accounts[5][0])",
            self.s,
        )
        self.assertIn(
            "str(exact_accounts[4][0])",
            self.s,
        )

    def test_forward_uses_exact_template(self):
        self.assertIn(
            "elif direction==FORWARD:",
            self.s,
        )

    def test_direction_specific_templates_preserved(self):
        self.assertIn(
            "expected_templates=expected_pairs*2",
            self.s,
        )
        self.assertIn(
            "identity=token|meteora_pool|direction",
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
