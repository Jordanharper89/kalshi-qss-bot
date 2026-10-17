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
        return rows[0]

    def srcfn(self,name):
        return (
            ast.get_source_segment(
                self.src,
                self.fn(name),
            )
            or ""
        )

    def test_canary_size_preserved(self):
        s=self.srcfn("exact_best")
        self.assertIn("0.005",s)

    def test_preload_all_saved_tables(self):
        s=self.srcfn(
            "preload_canary_saved_alts"
        )
        self.assertIn(
            "PRELOADED_SHARED_ALTS",
            s,
        )
        self.assertIn(
            "tables.items()",
            s,
        )
        self.assertNotIn(
            "for token in sorted(\\n        str(x)\\n        for x in READY_TOKENS",
            s,
        )

    def test_compile_tries_shared_alts(self):
        s=self.srcfn(
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
            "shared=%s",
            s,
        )

    def test_token_specific_first(self):
        s=self.srcfn(
            "compile_current"
        )
        self.assertLess(
            s.index("if token_alts:"),
            s.index("for alt in shared_alts"),
        )

    def test_no_hot_alt_rpc(self):
        s=self.srcfn(
            "_canonical_cached_alt_accounts"
        )
        self.assertNotIn(
            "rpc(",
            s,
        )

    def test_signed_fee_contract(self):
        s=self.srcfn(
            "compile_current"
        )
        self.assertIn(
            '"getFeeForMessage"',
            s,
        )
        self.assertIn(
            "q87.c.signed_tx",
            s,
        )

    def test_shell_still_rejected(self):
        s=self.srcfn(
            "compile_current"
        )
        self.assertIn(
            "LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",
            s,
        )

    def test_broadcast_still_disabled(self):
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
