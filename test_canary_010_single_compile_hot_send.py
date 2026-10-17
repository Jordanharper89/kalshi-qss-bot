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

    def fn(self,name):
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
        return (
            ast.get_source_segment(
                self.src,
                rows[0],
            )
            or ""
        )

    def test_fee_ceiling(self):
        self.assertIn(
            "FAST_010_FEE_CEILING_LAMPORTS=10_000",
            self.src,
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

    def test_single_compile_in_fast_path(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertEqual(
            s.count(
                "compile_current("
            ),
            1,
        )
        self.assertIn(
            "compile_passes=1",
            s,
        )

    def test_profit_lock_before_compile(self):
        s=self.fn(
            "fast_live_attack"
        )
        lock=s.index(
            "_fast_010_profit_lock_route("
        )
        comp=s.index(
            "compile_current("
        )
        self.assertLess(
            lock,
            comp,
        )

    def test_conservative_profit_math(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertIn(
            "CANARY_TRADE_LAMPORTS",
            s,
        )
        self.assertIn(
            "FAST_010_FEE_CEILING_LAMPORTS",
            s,
        )
        self.assertIn(
            "FAST_010_MIN_REALIZED_LAMPORTS",
            s,
        )

    def test_no_separate_sim(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertNotIn(
            "simulate_current(",
            s,
        )
        self.assertNotIn(
            "_execute_route_once(",
            s,
        )

    def test_latest_generation_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertIn(
            "_fast_010_refresh_latest(",
            s,
        )
        self.assertGreaterEqual(
            s.count(
                "newer_waiting("
            ),
            2,
        )

    def test_coherence_v2_preserved(self):
        self.assertIn(
            "COHERENCE_MIN_MUTATIONS=2",
            self.src,
        )
        self.assertIn(
            "COHERENCE_MIN_KINDS=2",
            self.src,
        )

    def test_preflight_no_retry(self):
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

    def test_reconciliation(self):
        s=self.fn(
            "_live_010_certify_or_send"
        )
        self.assertIn(
            "q96.reconcile",
            s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
