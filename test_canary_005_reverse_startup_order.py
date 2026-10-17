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

    def test_reverse_preload_once(self):
        run=self.fn("run")

        self.assertEqual(
            run.count(
                "reverse_sell_template_count=("
            ),
            1,
        )

        self.assertEqual(
            run.count(
                "[REVERSE_005_PRELOAD]"
            ),
            1,
        )

    def test_warm_before_reverse_preload(self):
        run=self.fn("run")

        warm=run.index(
            "q18.worker().warm("
        )

        reverse=run.index(
            "reverse_sell_template_count=("
        )

        self.assertLess(
            warm,
            reverse,
        )

    def test_ready_gate_before_reverse_preload(self):
        run=self.fn("run")

        gate=run.index(
            "NO_FULLY_PREWARMED_PAIRS"
        )

        reverse=run.index(
            "reverse_sell_template_count=("
        )

        self.assertLess(
            gate,
            reverse,
        )

    def test_reverse_preload_before_blockhash(self):
        run=self.fn("run")

        reverse=run.index(
            "reverse_sell_template_count=("
        )

        bh=run.index(
            "BLOCKHASH.start()"
        )

        self.assertLess(
            reverse,
            bh,
        )

    def test_reverse_builder_preserved(self):
        self.assertIn(
            "def prebuild_sell_templates",
            self.src,
        )

        self.assertIn(
            "def attack_reverse",
            self.src,
        )

    def test_live_005_preserved(self):
        self.assertIn(
            "I_ACCEPT_0_005_SOL_CANARY",
            self.src,
        )

        self.assertIn(
            "LIVE_005_REALIZED_PROFIT",
            self.src,
        )

    def test_exact_size_preserved(self):
        route=self.fn(
            "same_snapshot_reverse_route"
        )

        self.assertIn(
            "5_000_000",
            route,
        )

    def test_no_extra_send_path(self):
        self.assertEqual(
            self.src.count(
                '"sendTransaction"'
            ),
            1,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
