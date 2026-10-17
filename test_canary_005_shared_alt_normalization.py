from __future__ import annotations

import ast
from pathlib import Path
import unittest

TARGET=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=TARGET.read_text(
            encoding="utf-8"
        )
        cls.tree=ast.parse(cls.src)

    def count(self,name):
        return len([
            n for n in self.tree.body
            if isinstance(
                n,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and n.name==name
        ])

    def fn_src(self,name):
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

    def test_exactly_one_cached_alt_helper(self):
        self.assertEqual(
            self.count(
                "_canonical_cached_alt_accounts"
            ),
            1,
        )

    def test_exactly_one_preload(self):
        self.assertEqual(
            self.count(
                "preload_canary_saved_alts"
            ),
            1,
        )

    def test_exactly_one_compile(self):
        self.assertEqual(
            self.count(
                "compile_current"
            ),
            1,
        )

    def test_cached_helper_has_no_rpc(self):
        s=self.fn_src(
            "_canonical_cached_alt_accounts"
        )
        self.assertNotIn(
            "rpc(",
            s,
        )
        self.assertIn(
            "PRELOADED_ALT_TABLES",
            s,
        )

    def test_shared_alt_preload_preserved(self):
        s=self.fn_src(
            "preload_canary_saved_alts"
        )
        self.assertIn(
            "PRELOADED_SHARED_ALTS",
            s,
        )
        self.assertIn(
            "shared_tables=%d",
            s,
        )

    def test_shared_alt_compile_preserved(self):
        s=self.fn_src(
            "compile_current"
        )
        self.assertIn(
            "PRELOADED_SHARED_ALTS",
            s,
        )
        self.assertIn(
            "for alt in shared_alts",
            s,
        )
        self.assertIn(
            "getFeeForMessage",
            s,
        )
        self.assertIn(
            "signed_tx",
            s,
        )

    def test_canary_and_safety_preserved(self):
        s=self.fn_src(
            "exact_best"
        )
        self.assertIn(
            "0.005",
            s,
        )
        self.assertIn(
            '"[BROADCAST] disabled"',
            self.src,
        )
        self.assertNotIn(
            "q87.c.send(",
            self.src,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
