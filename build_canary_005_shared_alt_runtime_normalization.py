from __future__ import annotations

import ast
from pathlib import Path

TARGET=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_005_shared_alt_normalization.py"
)

NAMES=(
    "_canonical_cached_alt_accounts",
    "preload_canary_saved_alts",
    "compile_current",
)


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def function_rows(src,name):
    tree=parse(src,"TARGET")
    return [
        n for n in tree.body
        if isinstance(
            n,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and n.name==name
    ]


def remove_duplicate_functions(
    src,
    name,
):
    rows=function_rows(
        src,
        name,
    )

    if not rows:
        raise RuntimeError(
            f"{name}_MISSING"
        )

    if len(rows)==1:
        return src

    # Keep the LAST definition because Python itself
    # uses the last top-level definition and our newest
    # shared-ALT implementation was installed last.
    keep=rows[-1]
    lines=src.splitlines(
        keepends=True
    )

    spans=[]

    for node in rows[:-1]:
        start=sum(
            len(x)
            for x in lines[
                :node.lineno-1
            ]
        )
        end=sum(
            len(x)
            for x in lines[
                :node.end_lineno
            ]
        )
        spans.append(
            (start,end)
        )

    for start,end in reversed(spans):
        src=(
            src[:start]
            +src[end:]
        )

    return src


TEST_SOURCE=r"""
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
""".lstrip()


def main():
    if not TARGET.is_file():
        raise RuntimeError(
            "CANONICAL_RUNTIME_MISSING"
        )

    src=TARGET.read_text(
        encoding="utf-8"
    )

    parse(src,"BEFORE")

    for name in NAMES:
        src=remove_duplicate_functions(
            src,
            name,
        )

    tree=parse(src,"AFTER")

    for name in NAMES:
        count=sum(
            1
            for n in tree.body
            if isinstance(
                n,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and n.name==name
        )

        if count!=1:
            raise RuntimeError(
                f"{name}_NORMALIZATION_COUNT:{count}"
            )

    required=(
        "PRELOADED_SHARED_ALTS",
        "shared_tables=%d",
        "getFeeForMessage",
        "q87.c.signed_tx",
        '"[BROADCAST] disabled"',
    )

    missing=[
        x for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "CANARY_SHARED_ALT_CONTRACT_MISSING:"
            +repr(missing)
        )

    TARGET.write_text(
        src,
        encoding="utf-8",
    )

    parse(TEST_SOURCE,"TEST")

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    print(
        "[PASS] CANARY-005 shared ALT runtime normalized"
    )
    print(
        "[PASS] duplicate cached ALT helper removed"
    )
    print(
        "[PASS] exactly one preload path remains"
    )
    print(
        "[PASS] exactly one compile path remains"
    )
    print(
        "[PASS] shared ALT reuse preserved"
    )
    print(
        "[PASS] signed fee path preserved"
    )
    print(
        "[PASS] 0.005 canary preserved"
    )
    print(
        "[PASS] broadcast remains disabled"
    )


if __name__=="__main__":
    main()
