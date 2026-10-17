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

    def test_profit_floor(self):
        self.assertIn(
            "FAST_005_MIN_REALIZED_LAMPORTS=10_000",
            self.src,
        )

    def test_no_separate_sim_in_fast_path(self):
        s=self.fn("fast_live_attack")
        self.assertNotIn("simulate_current(",s)
        self.assertNotIn("_execute_route_once(",s)

    def test_both_directions_profit_locked(self):
        s=self.fn("_fast_005_profit_lock_route")
        self.assertIn("PUMP_TO_METEORA",s)
        self.assertIn("METEORA_TO_PUMP",s)
        self.assertIn("rewrite_pump_sell_bounds",s)
        self.assertIn("_fast_005_rewrite_meteora_min_out",s)

    def test_principal_fee_profit_floor(self):
        s=self.fn("fast_live_attack")
        self.assertIn("5_000_000",s)
        self.assertIn("FAST_005_MIN_REALIZED_LAMPORTS",s)

    def test_compile_contract_preserved(self):
        s=self.fn("compile_current")
        self.assertIn("PRELOADED_SHARED_ALTS",s)
        self.assertIn("getFeeForMessage",s)
        self.assertIn("signed_tx",s)

    def test_send_preflight_and_no_retry(self):
        s=self.fn("_live_005_send_once")
        self.assertIn('"skipPreflight":False',s)
        self.assertIn('"maxRetries":0',s)

    def test_reconciliation_preserved(self):
        s=self.fn("_live_005_certify_or_send")
        self.assertIn("q96.reconcile",s)
        self.assertIn("LIVE_005_REALIZED_PROFIT",s)

    def test_live_dispatch_fast(self):
        s=self.fn("canonical_price")
        self.assertIn("_live_005_armed()",s)
        self.assertIn("fast_live_attack(",s)

    def test_unarmed_paths_preserved(self):
        s=self.fn("canonical_price")
        self.assertIn("attack_reverse(",s)
        self.assertIn("attack(",s)


if __name__=="__main__":
    unittest.main(verbosity=2)
