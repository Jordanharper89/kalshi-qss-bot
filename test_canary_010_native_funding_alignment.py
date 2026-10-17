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
        cls.src=RT.read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.src)

    def fn(self,name):
        rows=[
            n for n in self.tree.body
            if isinstance(
                n,
                (ast.FunctionDef,ast.AsyncFunctionDef),
            )
            and n.name==name
        ]
        self.assertEqual(len(rows),1,name)
        return ast.get_source_segment(
            self.src,
            rows[0],
        ) or ""

    def test_exact_010_constants(self):
        self.assertIn(
            "CANARY_TRADE_SOL=0.010",
            self.src,
        )
        self.assertIn(
            "CANARY_TRADE_LAMPORTS=10_000_000",
            self.src,
        )

    def test_template_uses_010_principal(self):
        s=self.fn("prebuild_templates")
        self.assertIn(
            "CANARY_TRADE_LAMPORTS",
            s,
        )
        self.assertNotIn(
            "1_000_000",
            s,
        )

    def test_template_records_funding(self):
        s=self.fn("prebuild_templates")
        self.assertIn(
            '"template_quote_lamports"',
            s,
        )

    def test_template_guard_exists(self):
        s=self.fn(
            "_assert_010_template_funding"
        )
        self.assertIn(
            "PUMP_TEMPLATE_FUNDING_DRIFT",
            s,
        )

    def test_forward_route_calls_guard(self):
        s=self.fn("same_snapshot_route")
        self.assertIn(
            "_assert_010_template_funding(",
            s,
        )

    def test_single_compile_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertEqual(
            s.count("compile_current("),
            1,
        )

    def test_direct_send_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertIn(
            "_live_010_certify_or_send(",
            s,
        )
        self.assertNotIn(
            "_fast_010_prime_live_gate(",
            s,
        )

    def test_no_post_compile_supersede(self):
        s=self.fn("fast_live_attack")
        self.assertNotIn(
            "newer_waiting(",
            s,
        )

    def test_preflight_no_retry_preserved(self):
        s=self.fn("_live_010_send_once")
        self.assertIn(
            '"skipPreflight":False',
            s,
        )
        self.assertIn(
            '"maxRetries":0',
            s,
        )

    def test_profit_lock_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertIn(
            "_fast_010_profit_lock_route(",
            s,
        )
        self.assertIn(
            "FAST_010_MIN_REALIZED_LAMPORTS",
            s,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
