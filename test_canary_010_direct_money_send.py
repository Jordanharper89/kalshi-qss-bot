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

    def test_exact_010(self):
        self.assertIn(
            "CANARY_TRADE_SOL=0.010",
            self.src,
        )
        self.assertIn(
            "CANARY_TRADE_LAMPORTS=10_000_000",
            self.src,
        )

    def test_no_post_compile_supersede(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertNotIn(
            "newer_waiting(",
            s,
        )
        self.assertIn(
            "post_compile_supersede=FALSE",
            s,
        )

    def test_no_prime_certification_gate(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertNotIn(
            "_fast_010_prime_live_gate(",
            s,
        )
        self.assertIn(
            "prior_certification=FALSE",
            s,
        )

    def test_direct_live_dispatch(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertIn(
            "_live_010_certify_or_send(",
            s,
        )

    def test_live_function_no_two_pass(self):
        s=self.fn(
            "_live_010_certify_or_send"
        )
        self.assertNotIn(
            "CERTIFICATION_RECORDED",
            s,
        )
        self.assertNotIn(
            "CERTIFIED_WAITING_SECOND_PASS",
            s,
        )
        self.assertNotIn(
            "prior=",
            s,
        )

    def test_live_function_no_freshness_abort(self):
        s=self.fn(
            "_live_010_certify_or_send"
        )
        self.assertNotIn(
            "newer_waiting(",
            s,
        )

    def test_no_hot_balance_rpc(self):
        s=self.fn(
            "_live_010_certify_or_send"
        )
        self.assertNotIn(
            '"getBalance"',
            s,
        )
        self.assertIn(
            "wallet_before_lamports",
            s,
        )

    def test_attempt_marked_before_send(self):
        s=self.fn(
            "_live_010_certify_or_send"
        )
        self.assertLess(
            s.index(
                'state["send_attempted"]=True'
            ),
            s.index(
                "_live_010_send_once("
            ),
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

    def test_reconciliation_preserved(self):
        s=self.fn(
            "_live_010_certify_or_send"
        )
        self.assertIn(
            "q96.reconcile",
            s,
        )
        self.assertIn(
            "LIVE_010_REALIZED_PROFIT",
            s,
        )

    def test_profit_floor_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertIn(
            "FAST_010_MIN_REALIZED_LAMPORTS",
            s,
        )
        self.assertIn(
            "_fast_010_profit_lock_route(",
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


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
