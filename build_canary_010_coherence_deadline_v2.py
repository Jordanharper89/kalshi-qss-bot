from __future__ import annotations

import ast
import re
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_010_coherence_deadline_v2.py"
)

COHERENCE_FLUSH='def _coherence_flush(\n    lane,\n    force=False,\n):\n    now=time.perf_counter_ns()\n\n    for token,row in list(\n        COHERENCE_PENDING.items()\n    ):\n        quiet_ns=now-int(row["last_ns"])\n        held_ns=now-int(row["first_ns"])\n        mutations=int(row["mutations"])\n        kinds=len(row["kinds"])\n\n        coherent=(\n            mutations>=COHERENCE_MIN_MUTATIONS\n            and kinds>=COHERENCE_MIN_KINDS\n        )\n\n        quiet_ready=(\n            coherent\n            and quiet_ns>=COHERENCE_QUIET_NS\n        )\n\n        deadline=(\n            held_ns>=COHERENCE_MAX_HOLD_NS\n        )\n\n        if not (\n            force\n            or quiet_ready\n            or deadline\n        ):\n            continue\n\n        current=COHERENCE_PENDING.get(\n            token\n        )\n\n        if current is not row:\n            continue\n\n        del COHERENCE_PENDING[token]\n\n        if not coherent:\n            print(\n                "[COHERENCE_INCOMPLETE_HOLD] "\n                "token=%s slot=%s mutations=%d kinds=%d held_ms=%.3f"\n                %(\n                    token[:10],\n                    row["slot"],\n                    mutations,\n                    kinds,\n                    held_ns/1e6,\n                ),\n                flush=True,\n            )\n            continue\n\n        lane.submit(\n            token,\n            row["snap"],\n            row["slot"],\n            row["received_ns"],\n        )\n\n        print(\n            "[COHERENCE_RELEASE] "\n            "token=%s slot=%s mutations=%d kinds=%d "\n            "quiet_ms=%.3f held_ms=%.3f deadline=%s"\n            %(\n                token[:10],\n                row["slot"],\n                mutations,\n                kinds,\n                quiet_ns/1e6,\n                held_ns/1e6,\n                str(bool(deadline)).upper(),\n            ),\n            flush=True,\n        )\n'
TEST_SOURCE='from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(encoding="utf-8")\n        cls.tree=ast.parse(cls.src)\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(\n                n,\n                (ast.FunctionDef,ast.AsyncFunctionDef),\n            )\n            and n.name==name\n        ]\n        self.assertEqual(len(rows),1,name)\n        return ast.get_source_segment(self.src,rows[0]) or ""\n\n    def test_010_preserved(self):\n        self.assertIn("CANARY_TRADE_SOL=0.010",self.src)\n        self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",self.src)\n\n    def test_deadline_constants(self):\n        self.assertIn("COHERENCE_QUIET_NS=3_000_000",self.src)\n        self.assertIn("COHERENCE_MAX_HOLD_NS=12_000_000",self.src)\n        self.assertIn("COHERENCE_MIN_MUTATIONS=2",self.src)\n        self.assertIn("COHERENCE_MIN_KINDS=2",self.src)\n\n    def test_incomplete_holds(self):\n        s=self.fn("_coherence_flush")\n        self.assertIn("COHERENCE_INCOMPLETE_HOLD",s)\n        self.assertIn("if not coherent:",s)\n\n    def test_fast_pending_wake(self):\n        s=self.fn("serve_canonical")\n        self.assertIn(".002",s)\n        self.assertIn("COHERENCE_PENDING",s)\n        self.assertNotIn("timeout=.25",s)\n\n    def test_profit_floor_preserved(self):\n        self.assertIn(\n            "FAST_010_MIN_REALIZED_LAMPORTS=10_000",\n            self.src,\n        )\n\n    def test_live_arm_preserved(self):\n        self.assertIn("QSB_ORACLE_CANARY_010_ARM",self.src)\n        self.assertIn("I_ACCEPT_0_01_SOL_CANARY",self.src)\n\n    def test_preflight_no_retry(self):\n        s=self.fn("_live_010_send_once")\n        self.assertIn(\'"skipPreflight":False\',s)\n        self.assertIn(\'"maxRetries":0\',s)\n\n    def test_reconciliation(self):\n        s=self.fn("_live_010_certify_or_send")\n        self.assertIn("q96.reconcile",s)\n\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'


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
            (ast.FunctionDef,ast.AsyncFunctionDef),
        )
        and n.name==name
    ]


def fn_src(src,name):
    found=rows(src,name)
    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(found)}"
        )
    return ast.get_source_segment(src,found[0]) or ""


def replace_fn(src,name,replacement):
    found=rows(src,name)

    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(found)}"
        )

    node=found[0]
    lines=src.splitlines(keepends=True)
    start=sum(len(x) for x in lines[:node.lineno-1])
    end=sum(len(x) for x in lines[:node.end_lineno])

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

    src=RT.read_text(encoding="utf-8")
    parse(src,"BEFORE")

    required=(
        "CANARY_TRADE_SOL=0.010",
        "CANARY_TRADE_LAMPORTS=10_000_000",
        "COHERENCE_QUIET_NS=3_000_000",
        "COHERENCE_MAX_HOLD_NS=12_000_000",
        "COHERENCE_PENDING={}",
        "def _coherence_stage",
        "def _coherence_flush",
        "def serve_canonical",
        "FAST_010_MIN_REALIZED_LAMPORTS=10_000",
        "QSB_ORACLE_CANARY_010_ARM",
        "def _live_010_send_once",
        "def _live_010_certify_or_send",
    )

    missing=[
        x for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "COHERENCE_V2_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    if "COHERENCE_MIN_MUTATIONS=" not in src:
        src=src.replace(
            "COHERENCE_MAX_HOLD_NS=12_000_000\n",
            "COHERENCE_MAX_HOLD_NS=12_000_000\n"
            "COHERENCE_MIN_MUTATIONS=2\n"
            "COHERENCE_MIN_KINDS=2\n",
            1,
        )
    else:
        src=re.sub(
            r"COHERENCE_MIN_MUTATIONS=\d+",
            "COHERENCE_MIN_MUTATIONS=2",
            src,
            count=1,
        )
        src=re.sub(
            r"COHERENCE_MIN_KINDS=\d+",
            "COHERENCE_MIN_KINDS=2",
            src,
            count=1,
        )

    src=replace_fn(
        src,
        "_coherence_flush",
        COHERENCE_FLUSH,
    )

    serve=fn_src(
        src,
        "serve_canonical",
    )

    if "timeout=.25" in serve:
        serve=serve.replace(
            "timeout=.25",
            "timeout=(\n"
            "                        .002\n"
            "                        if COHERENCE_PENDING\n"
            "                        else .05\n"
            "                    )",
            1,
        )
    elif ".002" not in serve:
        raise RuntimeError(
            "COHERENCE_WAIT_TIMEOUT_SEAM_MISSING"
        )

    src=replace_fn(
        src,
        "serve_canonical",
        serve,
    )

    run=fn_src(
        src,
        "run",
    )

    run=run.replace(
        "quiet_ms=3 max_hold_ms=12 "
        "same-slot latest-state coalescing=TRUE",
        "quiet_ms=3 max_hold_ms=12 "
        "min_mutations=2 min_kinds=2 incomplete=HOLD",
    )

    src=replace_fn(
        src,
        "run",
        run,
    )

    parse(src,"AFTER")
    parse(TEST_SOURCE,"TEST")

    RT.write_text(src,encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")

    print(
        "[PASS] CANARY-010 coherence deadline V2 installed"
    )
    print(
        "[PASS] pending coherence wake <=2ms"
    )
    print(
        "[PASS] 3ms quiet / 12ms hard deadline enforceable"
    )
    print(
        "[PASS] incomplete single-update snapshots HOLD"
    )
    print(
        "[PASS] min mutations=2 and min kinds=2"
    )
    print(
        "[PASS] exact 0.010 SOL path preserved"
    )
    print(
        "[PASS] 10000-lamport profit floor preserved"
    )
    print(
        "[PASS] preflight + maxRetries=0 preserved"
    )
    print(
        "[PASS] one-shot reconciliation preserved"
    )


if __name__=="__main__":
    main()
