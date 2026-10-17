from __future__ import annotations

import ast
from pathlib import Path
import unittest

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=RT.read_text(
            encoding="utf-8"
        )
        cls.tree=ast.parse(
            cls.src
        )

    def fn_node(self,name):
        rows=[
            n for n in self.tree.body
            if isinstance(
                n,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and n.name==name
        ]
        self.assertEqual(
            len(rows),
            1,
            name,
        )
        return rows[0]

    def fn(self,name):
        return (
            ast.get_source_segment(
                self.src,
                self.fn_node(name),
            )
            or ""
        )

    def test_zero_wait_flags(self):
        self.assertIn(
            "FAST_010_ZERO_WAIT_COHERENCE=True",
            self.src,
        )
        self.assertIn(
            "FAST_010_VERBOSE_TELEMETRY=False",
            self.src,
        )

    def test_coherence_semantics(self):
        s=self.fn(
            "_coherence_flush"
        )

        self.assertIn(
            "coherent=(",
            s,
        )
        self.assertIn(
            "mutations>=COHERENCE_MIN_MUTATIONS",
            s,
        )
        self.assertIn(
            "kinds>=COHERENCE_MIN_KINDS",
            s,
        )
        self.assertIn(
            "or deadline",
            s,
        )
        self.assertIn(
            "or force",
            s,
        )

        self.assertNotIn(
            "quiet_ready",
            s,
        )
        self.assertNotIn(
            "quiet_ns>=COHERENCE_QUIET_NS",
            s,
        )

    def test_incomplete_still_held(self):
        s=self.fn(
            "_coherence_flush"
        )
        self.assertIn(
            "if not coherent:",
            s,
        )
        self.assertIn(
            "continue",
            s,
        )

    def test_stale_before_pricing(self):
        s=self.fn(
            "canonical_price"
        )
        stale=s.index(
            "newer_waiting("
        )
        quote=s.index(
            "exact_best("
        )
        self.assertLess(
            stale,
            quote,
        )

    def test_negative_logging_removed(self):
        s=self.fn(
            "canonical_price"
        )
        self.assertNotIn(
            "[CANONICAL_PRICE]",
            s,
        )
        self.assertIn(
            "[CANONICAL_POSITIVE]",
            s,
        )

    def test_fast_path_preserved(self):
        s=self.fn(
            "canonical_price"
        )
        self.assertIn(
            "fast_live_attack(",
            s,
        )

    def test_single_compile_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertEqual(
            s.count(
                "compile_current("
            ),
            1,
        )

    def test_no_separate_sim_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertNotIn(
            "simulate_current(",
            s,
        )

    def test_exact_010_preserved(self):
        self.assertIn(
            "CANARY_TRADE_SOL=0.010",
            self.src,
        )
        self.assertIn(
            "CANARY_TRADE_LAMPORTS=10_000_000",
            self.src,
        )

    def test_preflight_no_retry_preserved(self):
        s=self.fn(
            "_live_010_send_once"
        )
        self.assertIn(
            '"skipPreflight":False',
            s,
        )
        self.assertIn(
            '"maxRetries":0',
            s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
