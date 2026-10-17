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
        cls.s=P.read_text(
            encoding="utf-8"
        )
        ast.parse(cls.s)

    def test_pair_key_identity(self):
        self.assertIn(
            'str(token)+"|"+str(pool)',
            self.s,
        )
        self.assertIn(
            '+"|"+direction',
            self.s,
        )

    def test_single_batched_bitmap_rpc(self):
        self.assertIn(
            "CHECKPOINT17_BITMAP_BATCH",
            self.s,
        )
        self.assertIn(
            '"getMultipleAccounts"',
            self.s,
        )
        self.assertNotIn(
            'r.prebuild_meteora_templates({"pairs":[pair]}',
            self.s,
        )

    def test_transport_failures_retry(self):
        self.assertIn(
            "urllib.error.URLError",
            self.s,
        )
        self.assertIn(
            "TimeoutError",
            self.s,
        )
        self.assertIn(
            "CHECKPOINT17_BITMAP_RETRY",
            self.s,
        )

    def test_all_direction_templates_preserved(self):
        self.assertIn(
            "expected_templates=expected_pairs*2",
            self.s,
        )
        self.assertIn(
            "CHECKPOINT17_DIRECTION_TEMPLATE_COVERAGE",
            self.s,
        )

    def test_pool_drift_fails_closed(self):
        self.assertIn(
            "CHECKPOINT17_ROUTE_POOL_DRIFT",
            self.s,
        )

    def test_route_is_pair_direction_bound(self):
        self.assertIn(
            "c7._route=_pair_bound_route",
            self.s,
        )
        self.assertIn(
            "PAIR_KEY_DIRECTION_TEMPLATE_MISSING",
            self.s,
        )
        self.assertIn(
            "CHECKPOINT17_ROUTE_DIRECTION_DRIFT",
            self.s,
        )

    def test_forward_semantics(self):
        self.assertIn(
            'if direction==FORWARD:',
            self.s,
        )
        self.assertIn(
            '"PUMP_TO_METEORA"',
            self.s,
        )
        self.assertIn(
            '"METEORA_TO_PUMP"',
            self.s,
        )

    def test_reverse_semantics(self):
        self.assertIn(
            '"dest":token_ata',
            self.s,
        )
        self.assertIn(
            '"source":wsol_ata',
            self.s,
        )
        self.assertIn(
            "cp26_account5_create_idempotent_target=True",
            self.s,
        )

    def test_quote_direction_must_match_template(self):
        self.assertIn(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH",
            self.s,
        )

    def test_reuses_checkpoint15(self):
        self.assertIn(
            "return c15.main()",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
