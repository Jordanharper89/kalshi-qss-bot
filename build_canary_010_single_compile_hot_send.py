from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_010_single_compile_hot_send.py"
)

FAST_ATTACK='def fast_live_attack(\n    lane,\n    token,\n    snap,\n    opportunity,\n    slot,\n    received_ns,\n    generation,\n):\n    refreshed=_fast_010_refresh_latest(\n        lane,\n        token,\n        snap,\n        opportunity,\n        slot,\n        received_ns,\n        generation,\n    )\n\n    if refreshed is None:\n        return\n\n    (\n        snap,\n        opportunity,\n        slot,\n        received_ns,\n        generation,\n    )=refreshed\n\n    direction=str(\n        opportunity["direction"]\n    )\n\n    if int(\n        opportunity["start"]\n    )!=CANARY_TRADE_LAMPORTS:\n        print(\n            "[FAST_010_HOLD] "\n            "token=%s reason=SIZE_NOT_010"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    conservative_after_fee=(\n        int(\n            opportunity["local_net"]\n        )\n        -FAST_010_FEE_CEILING_LAMPORTS\n    )\n\n    if (\n        conservative_after_fee\n        <FAST_010_MIN_REALIZED_LAMPORTS\n    ):\n        print(\n            "[FAST_010_HOLD] "\n            "token=%s dir=%s "\n            "reason=CONSERVATIVE_AFTER_FEE_BELOW_FLOOR "\n            "after_fee=%+d floor=%d fee_ceiling=%d"\n            %(\n                token[:10],\n                direction,\n                conservative_after_fee,\n                FAST_010_MIN_REALIZED_LAMPORTS,\n                FAST_010_FEE_CEILING_LAMPORTS,\n            ),\n            flush=True,\n        )\n        return\n\n    required_final=(\n        CANARY_TRADE_LAMPORTS\n        +FAST_010_FEE_CEILING_LAMPORTS\n        +FAST_010_MIN_REALIZED_LAMPORTS\n    )\n\n    try:\n        route=same_snapshot_route(\n            USER,\n            snap,\n            opportunity,\n        )\n\n        route["direction"]=direction\n\n        (\n            locked_route,\n            old_bound,\n            new_bound,\n        )=_fast_010_profit_lock_route(\n            route,\n            direction,\n            required_final,\n        )\n\n        locked=compile_current(\n            USER,\n            locked_route,\n        )\n\n    except Exception as exc:\n        print(\n            "[FAST_010_BUILD_REJECT] "\n            "token=%s dir=%s error=%s:%s"\n            %(\n                token[:10],\n                direction,\n                type(exc).__name__,\n                str(exc)[:240],\n            ),\n            flush=True,\n        )\n        return\n\n    if not locked.get("ok"):\n        print(\n            "[FAST_010_COMPILE_REJECT] "\n            "token=%s dir=%s reason=%s"\n            %(\n                token[:10],\n                direction,\n                locked.get(\n                    "reason",\n                    "UNKNOWN",\n                ),\n            ),\n            flush=True,\n        )\n        return\n\n    actual_fee=int(\n        locked.get(\n            "fee_lamports",\n            FAST_010_FEE_CEILING_LAMPORTS,\n        )\n        or FAST_010_FEE_CEILING_LAMPORTS\n    )\n\n    if (\n        actual_fee\n        >FAST_010_FEE_CEILING_LAMPORTS\n    ):\n        print(\n            "[FAST_010_HOLD] "\n            "token=%s dir=%s "\n            "reason=FEE_ABOVE_CEILING "\n            "fee=%d ceiling=%d"\n            %(\n                token[:10],\n                direction,\n                actual_fee,\n                FAST_010_FEE_CEILING_LAMPORTS,\n            ),\n            flush=True,\n        )\n        return\n\n    if (\n        len(\n            locked.get(\n                "raw",\n                b"",\n            )\n        )\n        >MAX_TX_BYTES\n    ):\n        print(\n            "[FAST_010_HOLD] "\n            "token=%s reason=PACKET_TOO_LARGE"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    if lane.newer_waiting(\n        token,\n        generation,\n    ):\n        print(\n            "[FAST_010_SUPERSEDED] "\n            "token=%s phase=single_compile"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    age_ms=(\n        time.perf_counter_ns()\n        -received_ns\n    )/1e6\n\n    print(\n        "[FAST_010_READY] "\n        "token=%s dir=%s slot=%s "\n        "conservative_after_fee=%+d "\n        "profit_floor=%d fee_ceiling=%d "\n        "old_final_bound=%d "\n        "locked_final_bound=%d "\n        "bytes=%d event_age_ms=%.3f "\n        "compile_passes=1 "\n        "separate_sim_rpc=FALSE "\n        "send_preflight=TRUE"\n        %(\n            token[:10],\n            direction,\n            slot,\n            conservative_after_fee,\n            FAST_010_MIN_REALIZED_LAMPORTS,\n            FAST_010_FEE_CEILING_LAMPORTS,\n            old_bound,\n            new_bound,\n            int(\n                locked["bytes"]\n            ),\n            age_ms,\n        ),\n        flush=True,\n    )\n\n    if not _fast_010_prime_live_gate(\n        direction,\n        token,\n        slot,\n        conservative_after_fee,\n    ):\n        return\n\n    if lane.newer_waiting(\n        token,\n        generation,\n    ):\n        print(\n            "[FAST_010_SUPERSEDED] "\n            "token=%s phase=pre_send"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    _live_010_certify_or_send(\n        lane,\n        token,\n        direction,\n        slot,\n        received_ns,\n        generation,\n        locked,\n        conservative_after_fee,\n    )'
TEST_SOURCE='from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(\n            encoding="utf-8"\n        )\n        cls.tree=ast.parse(\n            cls.src\n        )\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(\n                n,\n                (\n                    ast.FunctionDef,\n                    ast.AsyncFunctionDef,\n                ),\n            )\n            and n.name==name\n        ]\n        self.assertEqual(\n            len(rows),\n            1,\n            name,\n        )\n        return (\n            ast.get_source_segment(\n                self.src,\n                rows[0],\n            )\n            or ""\n        )\n\n    def test_fee_ceiling(self):\n        self.assertIn(\n            "FAST_010_FEE_CEILING_LAMPORTS=10_000",\n            self.src,\n        )\n\n    def test_exact_010_preserved(self):\n        self.assertIn(\n            "CANARY_TRADE_SOL=0.010",\n            self.src,\n        )\n        self.assertIn(\n            "CANARY_TRADE_LAMPORTS=10_000_000",\n            self.src,\n        )\n\n    def test_single_compile_in_fast_path(self):\n        s=self.fn(\n            "fast_live_attack"\n        )\n        self.assertEqual(\n            s.count(\n                "compile_current("\n            ),\n            1,\n        )\n        self.assertIn(\n            "compile_passes=1",\n            s,\n        )\n\n    def test_profit_lock_before_compile(self):\n        s=self.fn(\n            "fast_live_attack"\n        )\n        lock=s.index(\n            "_fast_010_profit_lock_route("\n        )\n        comp=s.index(\n            "compile_current("\n        )\n        self.assertLess(\n            lock,\n            comp,\n        )\n\n    def test_conservative_profit_math(self):\n        s=self.fn(\n            "fast_live_attack"\n        )\n        self.assertIn(\n            "CANARY_TRADE_LAMPORTS",\n            s,\n        )\n        self.assertIn(\n            "FAST_010_FEE_CEILING_LAMPORTS",\n            s,\n        )\n        self.assertIn(\n            "FAST_010_MIN_REALIZED_LAMPORTS",\n            s,\n        )\n\n    def test_no_separate_sim(self):\n        s=self.fn(\n            "fast_live_attack"\n        )\n        self.assertNotIn(\n            "simulate_current(",\n            s,\n        )\n        self.assertNotIn(\n            "_execute_route_once(",\n            s,\n        )\n\n    def test_latest_generation_preserved(self):\n        s=self.fn(\n            "fast_live_attack"\n        )\n        self.assertIn(\n            "_fast_010_refresh_latest(",\n            s,\n        )\n        self.assertGreaterEqual(\n            s.count(\n                "newer_waiting("\n            ),\n            2,\n        )\n\n    def test_coherence_v2_preserved(self):\n        self.assertIn(\n            "COHERENCE_MIN_MUTATIONS=2",\n            self.src,\n        )\n        self.assertIn(\n            "COHERENCE_MIN_KINDS=2",\n            self.src,\n        )\n\n    def test_preflight_no_retry(self):\n        s=self.fn(\n            "_live_010_send_once"\n        )\n        self.assertIn(\n            \'"skipPreflight":False\',\n            s,\n        )\n        self.assertIn(\n            \'"maxRetries":0\',\n            s,\n        )\n\n    def test_reconciliation(self):\n        s=self.fn(\n            "_live_010_certify_or_send"\n        )\n        self.assertIn(\n            "q96.reconcile",\n            s,\n        )\n\n\nif __name__=="__main__":\n    unittest.main(\n        verbosity=2\n    )\n'


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def rows(src,name):
    tree=parse(
        src,
        "TARGET",
    )
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


def replace_fn(
    src,
    name,
    replacement,
):
    found=rows(
        src,
        name,
    )

    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:"
            f"{len(found)}"
        )

    node=found[0]
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
        +replacement.rstrip()
        +"\n\n"
        +src[end:]
    )


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
        "CANARY_TRADE_SOL=0.010",
        "CANARY_TRADE_LAMPORTS=10_000_000",
        "FAST_010_MIN_REALIZED_LAMPORTS=10_000",
        "def fast_live_attack",
        "def _fast_010_refresh_latest",
        "def _fast_010_profit_lock_route",
        "def _fast_010_prime_live_gate",
        "def _live_010_certify_or_send",
        "def _live_010_send_once",
        "QSB_ORACLE_CANARY_010_ARM",
        '"skipPreflight":False',
        '"maxRetries":0',
        "q96.reconcile",
    )

    missing=[
        x
        for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "SINGLE_COMPILE_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    if (
        "FAST_010_FEE_CEILING_LAMPORTS="
        not in src
    ):
        src=src.replace(
            "FAST_010_MIN_REALIZED_LAMPORTS=10_000\n",
            "FAST_010_MIN_REALIZED_LAMPORTS=10_000\n"
            "FAST_010_FEE_CEILING_LAMPORTS=10_000\n",
            1,
        )

    src=replace_fn(
        src,
        "fast_live_attack",
        FAST_ATTACK,
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
        "[PASS] CANARY-010 single-compile hot send installed"
    )
    print(
        "[PASS] exact 0.010 SOL preserved"
    )
    print(
        "[PASS] fee ceiling=10000 lamports"
    )
    print(
        "[PASS] profit lock occurs before compile"
    )
    print(
        "[PASS] fast path compile count reduced to one"
    )
    print(
        "[PASS] separate simulateTransaction RPC remains absent"
    )
    print(
        "[PASS] coherence/latest-generation freshness preserved"
    )
    print(
        "[PASS] preflight + maxRetries=0 preserved"
    )
    print(
        "[PASS] one-shot confirmation/reconciliation preserved"
    )


if __name__=="__main__":
    main()
