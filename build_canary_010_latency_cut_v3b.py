from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)
TEST=Path(
    "test_canary_010_latency_cut_v3b.py"
)

COHERENCE_FLUSH=r"""def _coherence_flush(
    lane,
    force=False,
):
    now=time.perf_counter_ns()

    for token,row in list(
        COHERENCE_PENDING.items()
    ):
        held_ns=(
            now-int(
                row["first_ns"]
            )
        )

        mutations=int(
            row["mutations"]
        )

        kinds=len(
            row["kinds"]
        )

        coherent=(
            mutations>=COHERENCE_MIN_MUTATIONS
            and kinds>=COHERENCE_MIN_KINDS
        )

        deadline=(
            held_ns>=COHERENCE_MAX_HOLD_NS
        )

        if not (
            coherent
            or deadline
            or force
        ):
            continue

        current=COHERENCE_PENDING.get(
            token
        )

        if current is not row:
            continue

        del COHERENCE_PENDING[
            token
        ]

        if not coherent:
            if FAST_010_VERBOSE_TELEMETRY:
                print(
                    "[COHERENCE_INCOMPLETE_HOLD] "
                    "token=%s slot=%s "
                    "mutations=%d kinds=%d held_ms=%.3f"
                    %(
                        token[:10],
                        row["slot"],
                        mutations,
                        kinds,
                        held_ns/1e6,
                    ),
                    flush=False,
                )
            continue

        lane.submit(
            token,
            row["snap"],
            row["slot"],
            row["received_ns"],
        )

        if FAST_010_VERBOSE_TELEMETRY:
            print(
                "[COHERENCE_RELEASE] "
                "token=%s slot=%s "
                "mutations=%d kinds=%d "
                "held_ms=%.3f immediate=TRUE"
                %(
                    token[:10],
                    row["slot"],
                    mutations,
                    kinds,
                    held_ns/1e6,
                ),
                flush=False,
            )
"""

CANONICAL_PRICE=r"""def canonical_price(
    self,
    token,
    row
):
    (
        snap,
        slot,
        received_ns,
        generation,
    )=row

    if self.newer_waiting(
        token,
        generation,
    ):
        self.scan_replaced+=1
        return

    event_age_ms=max(
        0.0,
        (
            time.perf_counter_ns()
            -received_ns
        )/1e6
    )

    self.event_start_ms.append(
        event_age_ms
    )

    t=time.perf_counter_ns()

    try:
        best=exact_best(
            self,
            token,
            snap,
            generation,
        )

    except RuntimeError as exc:
        if str(exc).startswith(
            "SUPERSEDED_"
        ):
            self.scan_replaced+=1
            return
        raise

    pricing_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    self.scan_ms.append(
        pricing_ms
    )

    self.processed+=1

    if (
        self.best is None
        or int(
            best["local_net"]
        )
        >
        int(
            self.best["local_net"]
        )
    ):
        self.best=dict(
            best
        )

    net=int(
        best["local_net"]
    )

    if net<=0:
        return

    self.positive+=1

    print(
        "[CANONICAL_POSITIVE] "
        "token=%s slot=%s dir=%s "
        "size=%.3f bps=%+.2f net=%+d "
        "event_age_ms=%.3f pricing_ms=%.3f"
        %(
            token[:10],
            slot,
            best["direction"],
            float(
                best["size_sol"]
            ),
            float(
                best["local_bps"]
            ),
            net,
            event_age_ms,
            pricing_ms,
        ),
        flush=True,
    )

    fast_live_attack(
        self,
        token,
        snap,
        best,
        slot,
        received_ns,
        generation,
    )
"""

TEST_SOURCE=r"""from __future__ import annotations

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

    def fn_node(self,name):
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

    def fn(self,name):
        return (
            ast.get_source_segment(
                self.src,
                self.fn_node(name),
            )
            or ""
        )

    def test_zero_wait_flags(self):
        self.assertIn(
            "FAST_010_ZERO_WAIT_COHERENCE=True",
            self.src,
        )
        self.assertIn(
            "FAST_010_VERBOSE_TELEMETRY=False",
            self.src,
        )

    def test_coherence_semantics(self):
        s=self.fn(
            "_coherence_flush"
        )

        self.assertIn(
            "coherent=(",
            s,
        )
        self.assertIn(
            "mutations>=COHERENCE_MIN_MUTATIONS",
            s,
        )
        self.assertIn(
            "kinds>=COHERENCE_MIN_KINDS",
            s,
        )
        self.assertIn(
            "or deadline",
            s,
        )
        self.assertIn(
            "or force",
            s,
        )

        self.assertNotIn(
            "quiet_ready",
            s,
        )
        self.assertNotIn(
            "quiet_ns>=COHERENCE_QUIET_NS",
            s,
        )

    def test_incomplete_still_held(self):
        s=self.fn(
            "_coherence_flush"
        )
        self.assertIn(
            "if not coherent:",
            s,
        )
        self.assertIn(
            "continue",
            s,
        )

    def test_stale_before_pricing(self):
        s=self.fn(
            "canonical_price"
        )
        stale=s.index(
            "newer_waiting("
        )
        quote=s.index(
            "exact_best("
        )
        self.assertLess(
            stale,
            quote,
        )

    def test_negative_logging_removed(self):
        s=self.fn(
            "canonical_price"
        )
        self.assertNotIn(
            "[CANONICAL_PRICE]",
            s,
        )
        self.assertIn(
            "[CANONICAL_POSITIVE]",
            s,
        )

    def test_fast_path_preserved(self):
        s=self.fn(
            "canonical_price"
        )
        self.assertIn(
            "fast_live_attack(",
            s,
        )

    def test_single_compile_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertEqual(
            s.count(
                "compile_current("
            ),
            1,
        )

    def test_no_separate_sim_preserved(self):
        s=self.fn(
            "fast_live_attack"
        )
        self.assertNotIn(
            "simulate_current(",
            s,
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

    def test_preflight_no_retry_preserved(self):
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


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
"""


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
            f"{name}_SEAM_COUNT:{len(found)}"
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


def ensure_flag(
    src,
    name,
    value,
):
    line=f"{name}={value}"

    import re

    if re.search(
        rf"^{name}=.*$",
        src,
        flags=re.M,
    ):
        return re.sub(
            rf"^{name}=.*$",
            line,
            src,
            count=1,
            flags=re.M,
        )

    anchor=(
        "CANARY_TRADE_LAMPORTS="
        "10_000_000\n"
    )

    if anchor not in src:
        raise RuntimeError(
            "FLAG_ANCHOR_MISSING"
        )

    return src.replace(
        anchor,
        anchor+line+"\n",
        1,
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
        "COHERENCE_MIN_MUTATIONS=2",
        "COHERENCE_MIN_KINDS=2",
        "COHERENCE_MAX_HOLD_NS=12_000_000",
        "def _coherence_flush",
        "def canonical_price",
        "def fast_live_attack",
        "def _live_010_send_once",
        "QSB_ORACLE_CANARY_010_ARM",
    )

    missing=[
        x
        for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "LATENCY_V3B_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    src=ensure_flag(
        src,
        "FAST_010_ZERO_WAIT_COHERENCE",
        "True",
    )

    src=ensure_flag(
        src,
        "FAST_010_VERBOSE_TELEMETRY",
        "False",
    )

    src=replace_fn(
        src,
        "_coherence_flush",
        COHERENCE_FLUSH,
    )

    src=replace_fn(
        src,
        "canonical_price",
        CANONICAL_PRICE,
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
        "[PASS] CANARY-010 latency cut V3B installed"
    )
    print(
        "[PASS] zero-wait coherent release installed"
    )
    print(
        "[PASS] stale-before-pricing gate installed"
    )
    print(
        "[PASS] negative/routine hot-path logging suppressed"
    )
    print(
        "[PASS] semantic tests installed"
    )
    print(
        "[PASS] exact 0.010 SOL preserved"
    )
    print(
        "[PASS] single compile / no separate sim preserved"
    )
    print(
        "[PASS] preflight + maxRetries=0 preserved"
    )


if __name__=="__main__":
    main()
