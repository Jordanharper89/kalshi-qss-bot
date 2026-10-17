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
        return ast.get_source_segment(self.src,rows[0]) or ""

    def test_010_preserved(self):
        self.assertIn("CANARY_TRADE_SOL=0.010",self.src)
        self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",self.src)

    def test_deadline_constants(self):
        self.assertIn("COHERENCE_QUIET_NS=3_000_000",self.src)
        self.assertIn("COHERENCE_MAX_HOLD_NS=12_000_000",self.src)
        self.assertIn("COHERENCE_MIN_MUTATIONS=2",self.src)
        self.assertIn("COHERENCE_MIN_KINDS=2",self.src)

    def test_incomplete_holds(self):
        s=self.fn("_coherence_flush")
        self.assertIn("COHERENCE_INCOMPLETE_HOLD",s)
        self.assertIn("if not coherent:",s)

    def test_fast_pending_wake(self):
        s=self.fn("serve_canonical")
        self.assertIn(".002",s)
        self.assertIn("COHERENCE_PENDING",s)
        self.assertNotIn("timeout=.25",s)

    def test_profit_floor_preserved(self):
        self.assertIn(
            "FAST_010_MIN_REALIZED_LAMPORTS=10_000",
            self.src,
        )

    def test_live_arm_preserved(self):
        self.assertIn("QSB_ORACLE_CANARY_010_ARM",self.src)
        self.assertIn("I_ACCEPT_0_01_SOL_CANARY",self.src)

    def test_preflight_no_retry(self):
        s=self.fn("_live_010_send_once")
        self.assertIn('"skipPreflight":False',s)
        self.assertIn('"maxRetries":0',s)

    def test_reconciliation(self):
        s=self.fn("_live_010_certify_or_send")
        self.assertIn("q96.reconcile",s)


if __name__=="__main__":
    unittest.main(verbosity=2)
