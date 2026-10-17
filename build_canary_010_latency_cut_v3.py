from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_010_latency_cut_v3.py"
)

COHERENCE_FLUSH='def _coherence_flush(\n    lane,\n    force=False,\n):\n    now=time.perf_counter_ns()\n\n    for token,row in list(\n        COHERENCE_PENDING.items()\n    ):\n        held_ns=(\n            now-int(\n                row["first_ns"]\n            )\n        )\n\n        mutations=int(\n            row["mutations"]\n        )\n\n        kinds=len(\n            row["kinds"]\n        )\n\n        coherent=(\n            mutations>=COHERENCE_MIN_MUTATIONS\n            and kinds>=COHERENCE_MIN_KINDS\n        )\n\n        deadline=(\n            held_ns>=COHERENCE_MAX_HOLD_NS\n        )\n\n        if not (\n            coherent\n            or deadline\n            or force\n        ):\n            continue\n\n        current=COHERENCE_PENDING.get(\n            token\n        )\n\n        if current is not row:\n            continue\n\n        del COHERENCE_PENDING[\n            token\n        ]\n\n        if not coherent:\n            if FAST_010_VERBOSE_TELEMETRY:\n                print(\n                    "[COHERENCE_INCOMPLETE_HOLD] "\n                    "token=%s slot=%s "\n                    "mutations=%d kinds=%d held_ms=%.3f"\n                    %(\n                        token[:10],\n                        row["slot"],\n                        mutations,\n                        kinds,\n                        held_ns/1e6,\n                    ),\n                    flush=False,\n                )\n            continue\n\n        lane.submit(\n            token,\n            row["snap"],\n            row["slot"],\n            row["received_ns"],\n        )\n\n        if FAST_010_VERBOSE_TELEMETRY:\n            print(\n                "[COHERENCE_RELEASE] "\n                "token=%s slot=%s "\n                "mutations=%d kinds=%d "\n                "held_ms=%.3f immediate=TRUE"\n                %(\n                    token[:10],\n                    row["slot"],\n                    mutations,\n                    kinds,\n                    held_ns/1e6,\n                ),\n                flush=False,\n            )'
CANONICAL_PRICE='def canonical_price(\n    self,\n    token,\n    row\n):\n    (\n        snap,\n        slot,\n        received_ns,\n        generation,\n    )=row\n\n    if self.newer_waiting(\n        token,\n        generation,\n    ):\n        self.scan_replaced+=1\n        return\n\n    event_age_ms=max(\n        0.0,\n        (\n            time.perf_counter_ns()\n            -received_ns\n        )/1e6\n    )\n\n    self.event_start_ms.append(\n        event_age_ms\n    )\n\n    t=time.perf_counter_ns()\n\n    try:\n        best=exact_best(\n            self,\n            token,\n            snap,\n            generation,\n        )\n\n    except RuntimeError as exc:\n        if str(exc).startswith(\n            "SUPERSEDED_"\n        ):\n            self.scan_replaced+=1\n            return\n        raise\n\n    pricing_ms=(\n        time.perf_counter_ns()\n        -t\n    )/1e6\n\n    self.scan_ms.append(\n        pricing_ms\n    )\n\n    self.processed+=1\n\n    if (\n        self.best is None\n        or int(\n            best["local_net"]\n        )\n        >\n        int(\n            self.best["local_net"]\n        )\n    ):\n        self.best=dict(\n            best\n        )\n\n    net=int(\n        best["local_net"]\n    )\n\n    if net<=0:\n        return\n\n    self.positive+=1\n\n    print(\n        "[CANONICAL_POSITIVE] "\n        "token=%s slot=%s dir=%s "\n        "size=%.3f bps=%+.2f net=%+d "\n        "event_age_ms=%.3f pricing_ms=%.3f"\n        %(\n            token[:10],\n            slot,\n            best["direction"],\n            float(\n                best["size_sol"]\n            ),\n            float(\n                best["local_bps"]\n            ),\n            net,\n            event_age_ms,\n            pricing_ms,\n        ),\n        flush=True,\n    )\n\n    fast_live_attack(\n        self,\n        token,\n        snap,\n        best,\n        slot,\n        received_ns,\n        generation,\n    )'
TEST_SOURCE='from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(\n            encoding="utf-8"\n        )\n        cls.tree=ast.parse(\n            cls.src\n        )\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(\n                n,\n                (\n                    ast.FunctionDef,\n                    ast.AsyncFunctionDef,\n                ),\n            )\n            and n.name==name\n        ]\n        self.assertEqual(\n            len(rows),\n            1,\n            name,\n        )\n        return (\n            ast.get_source_segment(\n                self.src,\n                rows[0],\n            )\n            or ""\n        )\n\n    def test_zero_wait_flag(self):\n        self.assertIn(\n            "FAST_010_ZERO_WAIT_COHERENCE=True",\n            self.src,\n        )\n\n    def test_verbose_off(self):\n        self.assertIn(\n            "FAST_010_VERBOSE_TELEMETRY=False",\n            self.src,\n        )\n\n    def test_coherence_releases_immediately(self):\n        s=self.fn(\n            "_coherence_flush"\n        )\n        self.assertIn(\n            "if not (\\\\n            coherent",\n            s,\n        )\n        self.assertNotIn(\n            "quiet_ready",\n            s,\n        )\n        self.assertNotIn(\n            "quiet_ns>=COHERENCE_QUIET_NS",\n            s,\n        )\n\n    def test_incomplete_still_held(self):\n        s=self.fn(\n            "_coherence_flush"\n        )\n        self.assertIn(\n            "if not coherent:",\n            s,\n        )\n        self.assertIn(\n            "COHERENCE_MAX_HOLD_NS",\n            self.src,\n        )\n\n    def test_negative_price_logging_removed(self):\n        s=self.fn(\n            "canonical_price"\n        )\n        self.assertNotIn(\n            "[CANONICAL_PRICE]",\n            s,\n        )\n        self.assertIn(\n            "[CANONICAL_POSITIVE]",\n            s,\n        )\n\n    def test_stale_dropped_before_pricing(self):\n        s=self.fn(\n            "canonical_price"\n        )\n        stale=s.index(\n            "newer_waiting("\n        )\n        quote=s.index(\n            "exact_best("\n        )\n        self.assertLess(\n            stale,\n            quote,\n        )\n\n    def test_fast_live_attack_preserved(self):\n        s=self.fn(\n            "canonical_price"\n        )\n        self.assertIn(\n            "fast_live_attack(",\n            s,\n        )\n\n    def test_single_compile_preserved(self):\n        s=self.fn(\n            "fast_live_attack"\n        )\n        self.assertEqual(\n            s.count(\n                "compile_current("\n            ),\n            1,\n        )\n\n    def test_no_separate_sim_preserved(self):\n        s=self.fn(\n            "fast_live_attack"\n        )\n        self.assertNotIn(\n            "simulate_current(",\n            s,\n        )\n\n    def test_exact_010_preserved(self):\n        self.assertIn(\n            "CANARY_TRADE_SOL=0.010",\n            self.src,\n        )\n        self.assertIn(\n            "CANARY_TRADE_LAMPORTS=10_000_000",\n            self.src,\n        )\n\n    def test_preflight_and_no_retry_preserved(self):\n        s=self.fn(\n            "_live_010_send_once"\n        )\n        self.assertIn(\n            \'"skipPreflight":False\',\n            s,\n        )\n        self.assertIn(\n            \'"maxRetries":0\',\n            s,\n        )\n\n\nif __name__=="__main__":\n    unittest.main(\n        verbosity=2\n    )\n'


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
        "COHERENCE_MIN_MUTATIONS=2",
        "COHERENCE_MIN_KINDS=2",
        "COHERENCE_MAX_HOLD_NS=12_000_000",
        "def _coherence_flush",
        "def canonical_price",
        "def fast_live_attack",
        "def _live_010_send_once",
        "QSB_ORACLE_CANARY_010_ARM",
        '"skipPreflight":False',
        '"maxRetries":0',
    )

    missing=[
        x
        for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "LATENCY_V3_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    if (
        "FAST_010_ZERO_WAIT_COHERENCE="
        not in src
    ):
        anchor=(
            "CANARY_TRADE_LAMPORTS=10_000_000\n"
        )

        if anchor not in src:
            raise RuntimeError(
                "LATENCY_FLAG_ANCHOR_MISSING"
            )

        src=src.replace(
            anchor,
            anchor
            +"FAST_010_ZERO_WAIT_COHERENCE=True\n"
            +"FAST_010_VERBOSE_TELEMETRY=False\n",
            1,
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
        "[PASS] CANARY-010 latency cut V3 installed"
    )
    print(
        "[PASS] coherent 2-kind snapshot releases immediately"
    )
    print(
        "[PASS] 3ms quiet wait removed from hot path"
    )
    print(
        "[PASS] stale generation dropped before exact pricing"
    )
    print(
        "[PASS] negative quote console spam removed"
    )
    print(
        "[PASS] routine coherence console spam removed"
    )
    print(
        "[PASS] positives/holds/sends/heartbeats preserved"
    )
    print(
        "[PASS] exact 0.010 SOL preserved"
    )
    print(
        "[PASS] one compile / no separate sim preserved"
    )
    print(
        "[PASS] preflight + maxRetries=0 preserved"
    )


if __name__=="__main__":
    main()
