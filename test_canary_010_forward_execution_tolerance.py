from __future__ import annotations
import ast
from pathlib import Path
import unittest

RT=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=RT.read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.src)

    def fn(self,name):
        rows=[
            n for n in cls.tree.body
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
            and n.name==name
        ]
        self.assertEqual(len(rows),1,name)
        return ast.get_source_segment(self.src,rows[0]) or ""

    def test_tolerance_constant(self):
        self.assertIn(
            "FAST_010_PUMP_EXECUTION_TOLERANCE_BPS=20",
            self.src
        )

    def test_forward_uses_floor(self):
        s=self.fn("same_snapshot_route")
        self.assertIn("execution_base_floor=max(",s)
        self.assertIn("execution_net_floor=int(",s)
        self.assertIn("execution_mq",s)

    def test_meteora_uses_floor(self):
        s=self.fn("same_snapshot_route")
        self.assertIn("build_meteora_ix_hot(",s)
        self.assertIn("execution_net_floor",s)

    def test_native_010_template_preserved(self):
        s=self.fn("prebuild_templates")
        self.assertIn("CANARY_TRADE_LAMPORTS",s)
        self.assertIn('"template_quote_lamports"',s)

    def test_exact_010_preserved(self):
        self.assertIn("CANARY_TRADE_SOL=0.010",self.src)
        self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",self.src)

    def test_profit_lock_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertIn("_fast_010_profit_lock_route(",s)
        self.assertIn("FAST_010_MIN_REALIZED_LAMPORTS",s)

    def test_direct_send_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertIn("_live_010_certify_or_send(",s)
        self.assertNotIn("_fast_010_prime_live_gate(",s)

    def test_single_compile_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertEqual(s.count("compile_current("),1)

    def test_preflight_no_retry_preserved(self):
        s=self.fn("_live_010_send_once")
        self.assertIn('"skipPreflight":False',s)
        self.assertIn('"maxRetries":0',s)

if __name__=="__main__":
    unittest.main(verbosity=2)
