from __future__ import annotations
import ast
from pathlib import Path
import unittest

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

JS=Path(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native/"
    "build_sell_ix.mjs"
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

    def test_sell_helper_exists(self):
        self.assertTrue(JS.is_file())
        s=JS.read_text(encoding="utf-8")
        self.assertIn("sellBaseInput",s)
        self.assertIn("instructions:ixs.map(encIx)",s)

    def test_reverse_is_exact_005(self):
        s=self.fn("same_snapshot_reverse_route")
        self.assertIn("5_000_000",s)
        self.assertIn('"METEORA_TO_PUMP"',s)

    def test_reverse_order(self):
        s=self.fn("_reverse_instruction_sets")
        self.assertIn("[meteora_ix,pump]",s)

    def test_reverse_min_bound(self):
        s=self.fn("same_snapshot_reverse_route")
        self.assertIn('"local_min_end"',s)
        self.assertIn("rewrite_pump_sell_bounds",s)

    def test_reverse_fee_gate(self):
        s=self.fn("attack_reverse")
        self.assertIn("after_fee_min",s)
        self.assertIn("AFTER_FEE_MIN_NONPOSITIVE",s)

    def test_reverse_signed_sim_path(self):
        s=self.fn("attack_reverse")
        self.assertIn("_execute_route_once",s)
        self.assertIn("REVERSE_005_CERTIFIED",s)

    def test_forward_attack_preserved(self):
        s=self.fn("attack")
        self.assertIn("pump_6040_actual_base_out",s)

    def test_no_broadcast(self):
        self.assertIn('"[BROADCAST] disabled"',self.src)
        self.assertNotIn("q87.c.send(",self.src)


if __name__=="__main__":
    unittest.main(verbosity=2)
