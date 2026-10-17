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
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
            and n.name==name
        ]
        self.assertEqual(len(rows),1,name)
        return ast.get_source_segment(self.src,rows[0]) or ""

    def test_010_constants(self):
        self.assertIn("CANARY_TRADE_SOL=0.010",self.src)
        self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",self.src)

    def test_exact_best_010(self):
        s=self.fn("exact_best")
        self.assertIn("CANARY_TRADE_SOL",s)
        self.assertNotIn("0.005",s)

    def test_refresh_010(self):
        s=self.fn("_fast_010_refresh_latest")
        self.assertIn("CANARY_TRADE_SOL",s)
        self.assertNotIn("0.005",s)

    def test_fast_principal_010(self):
        s=self.fn("fast_live_attack")
        self.assertIn("CANARY_TRADE_LAMPORTS",s)
        self.assertNotIn("5_000_000",s)

    def test_reverse_principal_010(self):
        s=self.fn("same_snapshot_reverse_route")
        self.assertIn("CANARY_TRADE_LAMPORTS",s)
        self.assertNotIn("5_000_000",s)

    def test_dedicated_live_arm_state(self):
        self.assertIn("QSB_ORACLE_CANARY_010_ARM",self.src)
        self.assertIn("I_ACCEPT_0_01_SOL_CANARY",self.src)
        self.assertIn("canary_010_live_state.json",self.src)
        self.assertNotIn("QSB_ORACLE_CANARY_005_ARM",self.src)

    def test_coherence_gate(self):
        self.assertIn("COHERENCE_QUIET_NS=3_000_000",self.src)
        self.assertIn("COHERENCE_MAX_HOLD_NS=12_000_000",self.src)
        p=self.fn("process_event")
        self.assertIn("_coherence_stage(",p)
        self.assertNotIn("lane.submit(",p)

    def test_serve_flushes(self):
        s=self.fn("serve_canonical")
        self.assertGreaterEqual(s.count("_coherence_flush("),2)

    def test_profit_floor(self):
        self.assertIn(
            "FAST_010_MIN_REALIZED_LAMPORTS=10_000",
            self.src,
        )

    def test_preflight_no_retry(self):
        s=self.fn("_live_010_send_once")
        self.assertIn('"skipPreflight":False',s)
        self.assertIn('"maxRetries":0',s)

    def test_reconciliation(self):
        s=self.fn("_live_010_certify_or_send")
        self.assertIn("q96.reconcile",s)
        self.assertIn("LIVE_010_REALIZED_PROFIT",s)


if __name__=="__main__":
    unittest.main(verbosity=2)
