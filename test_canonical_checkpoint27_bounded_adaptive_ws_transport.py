import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint27_bounded_adaptive_ws_transport.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(
            encoding="utf-8"
        )
        ast.parse(cls.s)

    def test_direct_runtime_owner(self):
        self.assertIn(
            "runtime as canonical_runtime",
            self.s,
        )
        self.assertIn(
            "persistent=canonical_runtime.persistent",
            self.s,
        )
        self.assertIn(
            "merged=persistent.m",
            self.s,
        )

    def test_no_checkpoint_chain_owner(self):
        self.assertNotIn(
            "c17.c15.persistent",
            self.s,
        )

    def test_connection_cap(self):
        self.assertIn(
            "MAX_CONNECTIONS=8",
            self.s,
        )

    def test_full_coverage_guard(self):
        self.assertIn(
            "CHECKPOINT27_ACCOUNT_COVERAGE_MISMATCH",
            self.s,
        )

    def test_http_429_is_counted(self):
        self.assertIn(
            '"http 429"',
            self.s,
        )
        self.assertIn(
            '"too many requests"',
            self.s,
        )

    def test_exact_transport_owner(self):
        self.assertIn(
            "merged._shards=adaptive_shards",
            self.s,
        )
        self.assertIn(
            "persistent._worker=bounded_worker",
            self.s,
        )

    def test_subscription_pacing_preserved(self):
        self.assertIn(
            "merged.SUB_DELAY_MS",
            self.s,
        )

    def test_checkpoint26_preserved(self):
        self.assertIn(
            "return c26.main()",
            self.s,
        )

    def test_broadcast_disabled(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
