from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_005_reverse_startup_order.py"
)

PRELOAD_BLOCK = (
    '    reverse_sell_template_count=(\n'
    '        prebuild_sell_templates(\n'
    '            state,\n'
    '            USER,\n'
    '        )\n'
    '    )\n\n'
    '    print(\n'
    '        "[REVERSE_005_PRELOAD] "\n'
    '        "sell_templates=%d broadcast=FALSE"\n'
    '        %reverse_sell_template_count,\n'
    '        flush=True,\n'
    '    )'
)


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def function_node(src,name):
    tree=parse(src,"TARGET")

    rows=[
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

    if len(rows)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(rows)}"
        )

    return rows[0]


def function_source(src,name):
    node=function_node(
        src,
        name,
    )

    return (
        ast.get_source_segment(
            src,
            node,
        )
        or ""
    )


def replace_function(
    src,
    name,
    new_source,
):
    node=function_node(
        src,
        name,
    )

    lines=src.splitlines(
        keepends=True
    )

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

    return (
        src[:start]
        +new_source.rstrip()
        +"\n\n"
        +src[end:]
    )


def remove_preload_block(run_src):
    marker="reverse_sell_template_count=("

    if marker not in run_src:
        raise RuntimeError(
            "REVERSE_PRELOAD_BLOCK_MISSING"
        )

    start=run_src.index(marker)
    line_start=run_src.rfind(
        "\n",
        0,
        start,
    )+1

    print_marker='        "[REVERSE_005_PRELOAD] "'

    p=run_src.index(
        print_marker,
        start,
    )

    end=run_src.index(
        "\n    )",
        p,
    )+len("\n    )")

    while (
        end<len(run_src)
        and run_src[end] in "\r\n"
    ):
        end+=1

    return (
        run_src[:line_start]
        +run_src[end:]
    )


def insert_after_ready_gate(run_src):
    gate=(
        '    if not READY_TOKENS:\n\n'
        '        raise RuntimeError(\n'
        '            "NO_FULLY_PREWARMED_PAIRS"\n'
        '        )\n'
    )

    if gate not in run_src:
        raise RuntimeError(
            "READY_GATE_SEAM_MISSING"
        )

    replacement=(
        gate
        +"\n"
        +PRELOAD_BLOCK
        +"\n"
    )

    return run_src.replace(
        gate,
        replacement,
        1,
    )


TEST_SOURCE = r'''from __future__ import annotations

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
'''


def main():
    if not RT.is_file():
        raise RuntimeError(
            "CANONICAL_RUNTIME_MISSING"
        )

    src=RT.read_text(
        encoding="utf-8"
    )

    parse(
        src,
        "BEFORE",
    )

    required=(
        "def prebuild_sell_templates",
        "def attack_reverse",
        "I_ACCEPT_0_005_SOL_CANARY",
        "LIVE_005_REALIZED_PROFIT",
        "[REVERSE_005_PRELOAD]",
        "q18.worker().warm(",
    )

    missing=[
        x
        for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "REVERSE_STARTUP_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    run=function_source(
        src,
        "run",
    )

    run=remove_preload_block(
        run
    )

    run=insert_after_ready_gate(
        run
    )

    if run.count(
        "reverse_sell_template_count=("
    )!=1:
        raise RuntimeError(
            "REVERSE_PRELOAD_COUNT_AFTER_NORMALIZATION"
        )

    warm_pos=run.index(
        "q18.worker().warm("
    )

    reverse_pos=run.index(
        "reverse_sell_template_count=("
    )

    gate_pos=run.index(
        "NO_FULLY_PREWARMED_PAIRS"
    )

    blockhash_pos=run.index(
        "BLOCKHASH.start()"
    )

    if not (
        warm_pos
        <gate_pos
        <reverse_pos
        <blockhash_pos
    ):
        raise RuntimeError(
            "REVERSE_STARTUP_ORDER_INVALID"
        )

    src=replace_function(
        src,
        "run",
        run,
    )

    parse(
        src,
        "AFTER",
    )

    parse(
        TEST_SOURCE,
        "TEST",
    )

    RT.write_text(
        src,
        encoding="utf-8",
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    print(
        "[PASS] reverse startup ordering normalized"
    )
    print(
        "[PASS] Pump SDK pools warm before reverse sell templates"
    )
    print(
        "[PASS] READY_TOKENS gate occurs before reverse preload"
    )
    print(
        "[PASS] reverse preload remains before blockhash/WebSocket runtime"
    )
    print(
        "[PASS] exact 0.005 one-shot live canary preserved"
    )
    print(
        "[PASS] no additional broadcast path introduced"
    )


if __name__=="__main__":
    main()
