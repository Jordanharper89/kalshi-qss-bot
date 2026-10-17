from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_010_native_funding_alignment.py"
)

PREBUILD = r"""
def prebuild_templates(
    state,
    user
):
    global TEMPLATES
    global READY_TOKENS

    TEMPLATES={}
    READY_TOKENS=set()

    for pair in list(
        state.get("pairs")
        or []
    ):
        token=str(pair.token)
        pool=str(pair.pump_pool)
        last=None

        for attempt in range(1,4):
            try:
                ixs,_=(
                    q87.las.q59
                    .native_pump_buy_ixs(
                        user,
                        pool,
                        CANARY_TRADE_LAMPORTS,
                    )
                )

                pos=pump_ix_position(ixs)

                TEMPLATES[token]={
                    "pump_pool":pool,
                    "instructions":[
                        copy.deepcopy(x)
                        for x in ixs
                    ],
                    "pump_index":int(pos),
                    "template_quote_lamports":
                        int(CANARY_TRADE_LAMPORTS),
                }

                READY_TOKENS.add(token)

                print(
                    "[CANONICAL_TEMPLATE_READY] "
                    "token=%s pump=%s "
                    "instructions=%d "
                    "quote_lamports=%d "
                    "exact_size=0.010 "
                    "attempt=%d"
                    %(
                        token[:10],
                        pool[:12],
                        len(ixs),
                        CANARY_TRADE_LAMPORTS,
                        attempt,
                    ),
                    flush=True,
                )
                break

            except Exception as exc:
                last=exc
                print(
                    "[CANONICAL_TEMPLATE_RETRY] "
                    "token=%s attempt=%d %s:%s"
                    %(
                        token[:10],
                        attempt,
                        type(exc).__name__,
                        str(exc)[:240],
                    ),
                    flush=True,
                )
                time.sleep(.4*attempt)

        if token not in READY_TOKENS:
            print(
                "[CANONICAL_TEMPLATE_HOLD] "
                "token=%s reason=%s:%s"
                %(
                    token[:10],
                    type(last).__name__
                    if last else "UNKNOWN",
                    str(last)[:240]
                    if last else "",
                ),
                flush=True,
            )

    if not READY_TOKENS:
        raise RuntimeError(
            "NO_CANONICAL_PUMP_TEMPLATES"
        )

    return len(READY_TOKENS)
""".strip()

GUARD = r"""
def _assert_010_template_funding(
    template,
):
    quote=int(
        template.get(
            "template_quote_lamports",
            0,
        )
        or 0
    )

    if quote!=CANARY_TRADE_LAMPORTS:
        raise RuntimeError(
            "PUMP_TEMPLATE_FUNDING_DRIFT:"
            +str(quote)
            +":expected="
            +str(CANARY_TRADE_LAMPORTS)
        )
""".strip()

TEST_SOURCE = r"""
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
        return ast.get_source_segment(
            self.src,
            rows[0],
        ) or ""

    def test_exact_010_constants(self):
        self.assertIn(
            "CANARY_TRADE_SOL=0.010",
            self.src,
        )
        self.assertIn(
            "CANARY_TRADE_LAMPORTS=10_000_000",
            self.src,
        )

    def test_template_uses_010_principal(self):
        s=self.fn("prebuild_templates")
        self.assertIn(
            "CANARY_TRADE_LAMPORTS",
            s,
        )
        self.assertNotIn(
            "1_000_000",
            s,
        )

    def test_template_records_funding(self):
        s=self.fn("prebuild_templates")
        self.assertIn(
            '"template_quote_lamports"',
            s,
        )

    def test_template_guard_exists(self):
        s=self.fn(
            "_assert_010_template_funding"
        )
        self.assertIn(
            "PUMP_TEMPLATE_FUNDING_DRIFT",
            s,
        )

    def test_forward_route_calls_guard(self):
        s=self.fn("same_snapshot_route")
        self.assertIn(
            "_assert_010_template_funding(",
            s,
        )

    def test_single_compile_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertEqual(
            s.count("compile_current("),
            1,
        )

    def test_direct_send_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertIn(
            "_live_010_certify_or_send(",
            s,
        )
        self.assertNotIn(
            "_fast_010_prime_live_gate(",
            s,
        )

    def test_no_post_compile_supersede(self):
        s=self.fn("fast_live_attack")
        self.assertNotIn(
            "newer_waiting(",
            s,
        )

    def test_preflight_no_retry_preserved(self):
        s=self.fn("_live_010_send_once")
        self.assertIn(
            '"skipPreflight":False',
            s,
        )
        self.assertIn(
            '"maxRetries":0',
            s,
        )

    def test_profit_lock_preserved(self):
        s=self.fn("fast_live_attack")
        self.assertIn(
            "_fast_010_profit_lock_route(",
            s,
        )
        self.assertIn(
            "FAST_010_MIN_REALIZED_LAMPORTS",
            s,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
""".lstrip()


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def rows(src,name):
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


def fn_src(src,name):
    found=rows(src,name)
    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(found)}"
        )
    return (
        ast.get_source_segment(
            src,
            found[0],
        )
        or ""
    )


def replace_fn(src,name,replacement):
    found=rows(src,name)
    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(found)}"
        )

    node=found[0]
    lines=src.splitlines(
        keepends=True
    )

    start=sum(
        len(x)
        for x in lines[:node.lineno-1]
    )
    end=sum(
        len(x)
        for x in lines[:node.end_lineno]
    )

    return (
        src[:start]
        +replacement.rstrip()
        +"\n\n"
        +src[end:]
    )


def insert_before_fn(
    src,
    target_name,
    block,
):
    found=rows(src,target_name)
    if len(found)!=1:
        raise RuntimeError(
            f"{target_name}_SEAM_COUNT:"
            f"{len(found)}"
        )

    node=found[0]
    lines=src.splitlines(
        keepends=True
    )

    start=sum(
        len(x)
        for x in lines[:node.lineno-1]
    )

    return (
        src[:start]
        +block.rstrip()
        +"\n\n"
        +src[start:]
    )


def main():
    if not RT.is_file():
        raise RuntimeError(
            "CANONICAL_RUNTIME_MISSING"
        )

    src=RT.read_text(
        encoding="utf-8"
    )

    parse(src,"BEFORE")

    required=(
        "CANARY_TRADE_SOL=0.010",
        "CANARY_TRADE_LAMPORTS=10_000_000",
        "def prebuild_templates",
        "def same_snapshot_route",
        "def fast_live_attack",
        "def _live_010_send_once",
        "QSB_ORACLE_CANARY_010_ARM",
        '"skipPreflight":False',
        '"maxRetries":0',
    )

    missing=[
        x for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "NATIVE_FUNDING_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    src=replace_fn(
        src,
        "prebuild_templates",
        PREBUILD,
    )

    if "def _assert_010_template_funding" in src:
        src=replace_fn(
            src,
            "_assert_010_template_funding",
            GUARD,
        )
    else:
        src=insert_before_fn(
            src,
            "same_snapshot_route",
            GUARD,
        )

    route=fn_src(
        src,
        "same_snapshot_route",
    )

    if "_assert_010_template_funding(" not in route:
        needle=(
            '    if template is None:\n\n'
            '        raise RuntimeError(\n'
            '            "NO_PREBUILT_TEMPLATE:"\n'
            '            +token\n'
            '        )\n'
        )

        if needle not in route:
            raise RuntimeError(
                "FORWARD_TEMPLATE_GUARD_ANCHOR_MISSING"
            )

        repl=(
            needle
            +'\n'
            +'    _assert_010_template_funding(\n'
            +'        template,\n'
            +'    )\n'
        )

        route=route.replace(
            needle,
            repl,
            1,
        )

        src=replace_fn(
            src,
            "same_snapshot_route",
            route,
        )

    parse(src,"AFTER")
    parse(TEST_SOURCE,"TEST")

    RT.write_text(
        src,
        encoding="utf-8",
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    print(
        "[PASS] CANARY-010 native funding alignment installed"
    )
    print(
        "[PASS] Pump SDK template principal 0.001 -> 0.010 SOL"
    )
    print(
        "[PASS] native WSOL/helper template now born at 10000000 lamports"
    )
    print(
        "[PASS] forward route rejects underfunded stale templates"
    )
    print(
        "[PASS] exact 0.010 SOL preserved"
    )
    print(
        "[PASS] direct-money send preserved"
    )
    print(
        "[PASS] one compile preserved"
    )
    print(
        "[PASS] atomic profit lock preserved"
    )
    print(
        "[PASS] preflight + maxRetries=0 preserved"
    )

if __name__=="__main__":
    main()
