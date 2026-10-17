
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

    def test_idempotent_ata_helper(self):
        s=self.fn(
            "_ata_create_idempotent_ix"
        )
        self.assertIn(
            "bytes([1])",
            s,
        )
        self.assertIn(
            "q87.c.ATA",
            s,
        )

    def test_reverse_readiness_helper(self):
        s=self.fn(
            "_reverse_prepend_ata_readiness"
        )
        self.assertIn(
            "ATA_READY_",
            s,
        )
        self.assertIn(
            "_ata_create_idempotent_ix(",
            s,
        )

    def test_reverse_path_calls_readiness(self):
        matches=[
            self.fn(n.name)
            for n in self.tree.body
            if isinstance(
                n,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and "_reverse_prepend_ata_readiness("
            in (
                ast.get_source_segment(
                    self.src,
                    n,
                )
                or ""
            )
        ]
        self.assertGreaterEqual(
            len(matches),
            1,
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

    def test_direct_send_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertIn(
            "_live_010_certify_or_send(",
            s,
        )

    def test_preflight_preserved(self):
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

    def test_profit_lock_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertIn(
            "_fast_010_profit_lock_route(",
            s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
