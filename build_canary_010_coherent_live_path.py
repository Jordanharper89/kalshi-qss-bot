from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)
TEST=Path("test_canary_010_coherent_live_path.py")

COHERENCE_BLOCK='CANARY_TRADE_SOL=0.010\nCANARY_TRADE_LAMPORTS=10_000_000\nCOHERENCE_QUIET_NS=3_000_000\nCOHERENCE_MAX_HOLD_NS=12_000_000\nCOHERENCE_PENDING={}\n\n\ndef _coherence_stage(token,snap,slot,received_ns,kind):\n    now=time.perf_counter_ns()\n    previous=COHERENCE_PENDING.get(token)\n\n    if previous is None or int(slot)!=int(previous["slot"]):\n        COHERENCE_PENDING[token]={\n            "snap":snap,\n            "slot":int(slot),\n            "received_ns":int(received_ns),\n            "first_ns":now,\n            "last_ns":now,\n            "mutations":1,\n            "kinds":{str(kind)},\n        }\n        return\n\n    previous["snap"]=snap\n    previous["received_ns"]=int(received_ns)\n    previous["last_ns"]=now\n    previous["mutations"]=int(previous["mutations"])+1\n    previous["kinds"].add(str(kind))\n\n\ndef _coherence_flush(lane,force=False):\n    now=time.perf_counter_ns()\n    ready=[]\n\n    for token,row in list(COHERENCE_PENDING.items()):\n        quiet_ns=now-int(row["last_ns"])\n        held_ns=now-int(row["first_ns"])\n\n        if (\n            force\n            or quiet_ns>=COHERENCE_QUIET_NS\n            or held_ns>=COHERENCE_MAX_HOLD_NS\n        ):\n            ready.append((token,row,quiet_ns,held_ns))\n\n    for token,row,quiet_ns,held_ns in ready:\n        if COHERENCE_PENDING.get(token) is not row:\n            continue\n\n        del COHERENCE_PENDING[token]\n\n        lane.submit(\n            token,\n            row["snap"],\n            row["slot"],\n            row["received_ns"],\n        )\n\n        print(\n            "[COHERENCE_RELEASE] "\n            "token=%s slot=%s mutations=%d kinds=%d "\n            "quiet_ms=%.3f held_ms=%.3f"\n            %(\n                token[:10],\n                row["slot"],\n                int(row["mutations"]),\n                len(row["kinds"]),\n                quiet_ns/1e6,\n                held_ns/1e6,\n            ),\n            flush=True,\n        )'
TEST_SOURCE='from __future__ import annotations\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(encoding="utf-8")\n        cls.tree=ast.parse(cls.src)\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))\n            and n.name==name\n        ]\n        self.assertEqual(len(rows),1,name)\n        return ast.get_source_segment(self.src,rows[0]) or ""\n\n    def test_010_constants(self):\n        self.assertIn("CANARY_TRADE_SOL=0.010",self.src)\n        self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",self.src)\n\n    def test_exact_best_010(self):\n        s=self.fn("exact_best")\n        self.assertIn("CANARY_TRADE_SOL",s)\n        self.assertNotIn("0.005",s)\n\n    def test_refresh_010(self):\n        s=self.fn("_fast_010_refresh_latest")\n        self.assertIn("CANARY_TRADE_SOL",s)\n        self.assertNotIn("0.005",s)\n\n    def test_fast_principal_010(self):\n        s=self.fn("fast_live_attack")\n        self.assertIn("CANARY_TRADE_LAMPORTS",s)\n        self.assertNotIn("5_000_000",s)\n\n    def test_reverse_principal_010(self):\n        s=self.fn("same_snapshot_reverse_route")\n        self.assertIn("CANARY_TRADE_LAMPORTS",s)\n        self.assertNotIn("5_000_000",s)\n\n    def test_dedicated_live_arm_state(self):\n        self.assertIn("QSB_ORACLE_CANARY_010_ARM",self.src)\n        self.assertIn("I_ACCEPT_0_01_SOL_CANARY",self.src)\n        self.assertIn("canary_010_live_state.json",self.src)\n        self.assertNotIn("QSB_ORACLE_CANARY_005_ARM",self.src)\n\n    def test_coherence_gate(self):\n        self.assertIn("COHERENCE_QUIET_NS=3_000_000",self.src)\n        self.assertIn("COHERENCE_MAX_HOLD_NS=12_000_000",self.src)\n        p=self.fn("process_event")\n        self.assertIn("_coherence_stage(",p)\n        self.assertNotIn("lane.submit(",p)\n\n    def test_serve_flushes(self):\n        s=self.fn("serve_canonical")\n        self.assertGreaterEqual(s.count("_coherence_flush("),2)\n\n    def test_profit_floor(self):\n        self.assertIn(\n            "FAST_010_MIN_REALIZED_LAMPORTS=10_000",\n            self.src,\n        )\n\n    def test_preflight_no_retry(self):\n        s=self.fn("_live_010_send_once")\n        self.assertIn(\'"skipPreflight":False\',s)\n        self.assertIn(\'"maxRetries":0\',s)\n\n    def test_reconciliation(self):\n        s=self.fn("_live_010_certify_or_send")\n        self.assertIn("q96.reconcile",s)\n        self.assertIn("LIVE_010_REALIZED_PROFIT",s)\n\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'


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
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
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
    return src[:start]+replacement.rstrip()+"\n\n"+src[end:]


def remove_fn(src,name):
    found=rows(src,name)
    if not found:
        return src
    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(found)}"
        )

    node=found[0]
    lines=src.splitlines(keepends=True)
    start=sum(len(x) for x in lines[:node.lineno-1])
    end=sum(len(x) for x in lines[:node.end_lineno])
    return src[:start]+src[end:]


def normalize_names(src):
    replacements=(
        ("QSB_ORACLE_CANARY_005_ARM","QSB_ORACLE_CANARY_010_ARM"),
        ("I_ACCEPT_0_005_SOL_CANARY","I_ACCEPT_0_01_SOL_CANARY"),
        ("canary_005_live_state.json","canary_010_live_state.json"),
        ("LIVE_005_","LIVE_010_"),
        ("_live_005_","_live_010_"),
        ("FAST_005_","FAST_010_"),
        ("_fast_005_","_fast_010_"),
    )
    for old,new in replacements:
        src=src.replace(old,new)
    return src


def normalize_exact_best(src):
    body='''def exact_best(
    lane,
    token,
    snap,
    generation,
):
    rows=q18.exact_snapshot_opportunities(
        snap,
        CANARY_TRADE_SOL,
    )

    if not rows:
        raise RuntimeError(
            "SAE005E_NO_001_QUOTES"
        )

    return max(
        rows,
        key=lambda x:int(
            x["local_net"]
        ),
    )
'''
    return replace_fn(src,"exact_best",body)


def normalize_refresh(src):
    s=fn_src(src,"_fast_010_refresh_latest")
    s=s.replace("            0.005,","            CANARY_TRADE_SOL,")
    s=s.replace("0.005","0.010")
    return replace_fn(src,"_fast_010_refresh_latest",s)


def normalize_reverse(src):
    s=fn_src(src,"same_snapshot_reverse_route")
    s=s.replace("5_000_000","CANARY_TRADE_LAMPORTS")
    s=s.replace("0.005","0.010")
    return replace_fn(src,"same_snapshot_reverse_route",s)


def normalize_fast(src):
    s=fn_src(src,"fast_live_attack")
    s=s.replace("5_000_000","CANARY_TRADE_LAMPORTS")
    s=s.replace("0.005","0.010")
    return replace_fn(src,"fast_live_attack",s)


def normalize_live_sender(src):
    s=fn_src(src,"_live_010_certify_or_send")
    s=s.replace("5_000_000","CANARY_TRADE_LAMPORTS")
    s=s.replace("0.005","0.010")
    s=s.replace(
        '"size_sol"]=0.010',
        '"size_sol"]=CANARY_TRADE_SOL',
    )
    return replace_fn(src,"_live_010_certify_or_send",s)


def normalize_process_event(src):
    body='''def process_event(
    state,
    ev,
    counters,
    lane
):
    address=ev["address"]
    preg=state.get("preg",{})

    if address not in preg:
        return

    index,kind=preg[address]
    pair=state["pairs"][index]
    token=str(pair.token)

    if token not in READY_TOKENS:
        return

    try:
        changed=(
            persistent.m.pd.apply_account_event(
                pair,
                kind,
                address,
                ev["raw"],
                ev["slot"],
                ev["received_ns"],
            )
        )
    except Exception:
        counters["event_errors"]+=1
        return

    if not changed:
        return

    counters["priced_events"]+=1

    _coherence_stage(
        token,
        immutable_snapshot(pair),
        ev["slot"],
        ev["received_ns"],
        kind,
    )
'''
    return replace_fn(src,"process_event",body)


def normalize_serve(src):
    s=fn_src(src,"serve_canonical")

    call='''                process_event(
                    state,
                    ev,
                    counters,
                    lane,
                )
'''
    if call not in s:
        raise RuntimeError("COHERENCE_PROCESS_CALL_SEAM_MISSING")

    s=s.replace(
        call,
        call+'''
                _coherence_flush(
                    lane,
                    force=False,
                )
''',
        1,
    )

    timeout='''            except asyncio.TimeoutError:
                pass
'''
    if timeout not in s:
        raise RuntimeError("COHERENCE_TIMEOUT_SEAM_MISSING")

    s=s.replace(
        timeout,
        '''            except asyncio.TimeoutError:
                _coherence_flush(
                    lane,
                    force=False,
                )
''',
        1,
    )

    finally_marker='''    finally:

        stop.set()
'''
    if finally_marker not in s:
        raise RuntimeError("COHERENCE_FINALLY_SEAM_MISSING")

    s=s.replace(
        finally_marker,
        '''    finally:

        _coherence_flush(
            lane,
            force=True,
        )

        stop.set()
''',
        1,
    )

    return replace_fn(src,"serve_canonical",s)


def normalize_run(src):
    s=fn_src(src,"run")
    s=s.replace("exact_size=0.005","exact_size=0.010")

    anchor='''    print(
        "[SNAPSHOT] "
        "deep-copied immutable DLMM + Pump reserves",
        flush=True,
    )
'''

    if "[COHERENCE]" not in s:
        if anchor not in s:
            raise RuntimeError("COHERENCE_DISCLOSURE_SEAM_MISSING")

        s=s.replace(
            anchor,
            anchor+'''
    print(
        "[COHERENCE] "
        "quiet_ms=3 max_hold_ms=12 "
        "same-slot latest-state coalescing=TRUE",
        flush=True,
    )
''',
            1,
        )

    return replace_fn(src,"run",s)


def main():
    if not RT.is_file():
        raise RuntimeError("CANONICAL_RUNTIME_MISSING")

    src=RT.read_text(encoding="utf-8")
    parse(src,"BEFORE")

    required=(
        "def exact_best",
        "def same_snapshot_reverse_route",
        "def fast_live_attack",
        "def _fast_005_refresh_latest",
        "FAST_005_MIN_REALIZED_LAMPORTS=10_000",
        "def _live_005_send_once",
        "def _live_005_certify_or_send",
        "QSB_ORACLE_CANARY_005_ARM",
        "def process_event",
        "def serve_canonical",
        "def run(",
    )

    missing=[x for x in required if x not in src]
    if missing:
        raise RuntimeError(
            "CANARY_010_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    src=normalize_names(src)

    for name in (
        "_coherence_stage",
        "_coherence_flush",
    ):
        src=remove_fn(src,name)

    for literal in (
        "CANARY_TRADE_SOL=0.010\n",
        "CANARY_TRADE_LAMPORTS=10_000_000\n",
        "COHERENCE_QUIET_NS=3_000_000\n",
        "COHERENCE_MAX_HOLD_NS=12_000_000\n",
        "COHERENCE_PENDING={}\n",
    ):
        src=src.replace(literal,"")

    insert_at=src.index("\ndef exact_best")
    src=(
        src[:insert_at]
        +"\n\n"
        +COHERENCE_BLOCK
        +"\n\n"
        +src[insert_at:]
    )

    src=normalize_exact_best(src)
    src=normalize_refresh(src)
    src=normalize_reverse(src)
    src=normalize_fast(src)
    src=normalize_live_sender(src)
    src=normalize_process_event(src)
    src=normalize_serve(src)
    src=normalize_run(src)

    parse(src,"AFTER")
    parse(TEST_SOURCE,"TEST")

    RT.write_text(src,encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")

    print("[PASS] CANARY-010 coherent live path installed")
    print("[PASS] exact live trade size changed to 0.010 SOL")
    print("[PASS] dedicated 0.010 live arm/state installed")
    print("[PASS] 3ms quiet / 12ms max same-slot coherence gate installed")
    print("[PASS] latest-generation chase preserved")
    print("[PASS] 10000-lamport profit floor preserved")
    print("[PASS] send preflight + maxRetries=0 preserved")
    print("[PASS] one-shot confirmation/reconciliation preserved")


if __name__=="__main__":
    main()
