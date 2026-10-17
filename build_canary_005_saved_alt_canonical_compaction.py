from __future__ import annotations

import ast
from pathlib import Path

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
TEST=Path("test_canary_005_saved_alt_canonical_compaction.py")

PRELOAD = r"""
def _canonical_cached_alt_accounts(addrs):
    tables=globals().get(
        "PRELOADED_ALT_TABLES",
        {}
    )

    out={}

    for addr in list(addrs or []):
        if addr not in tables:
            raise RuntimeError(
                "CANARY_005_ALT_NOT_PRELOADED:"
                +str(addr)
            )

        out[addr]=tables[addr]

    return out


def preload_canary_saved_alts(root):
    from qseries_v2.solana_live_execution import (
        qarb_097_official_meteora_sdk_executor as q97
    )

    state=q97._load_alt_state(
        Path(root)
    )

    tables=(
        state.get("tables")
        if isinstance(state,dict)
        else {}
    )

    if not isinstance(tables,dict):
        tables={}

    token_alts={}
    addresses=[]

    for token in sorted(
        str(x)
        for x in READY_TOKENS
    ):
        row=tables.get(token)

        if not isinstance(row,dict):
            continue

        address=row.get("address")

        if not address:
            continue

        address=str(address)

        token_alts[token]=[
            address
        ]

        if address not in addresses:
            addresses.append(address)

    original=globals().get(
        "_ORIGINAL_ALT_ACCOUNTS"
    )

    if original is None:
        original=q87.c.alt_accounts
        globals()[
            "_ORIGINAL_ALT_ACCOUNTS"
        ]=original

    decoded=(
        original(addresses)
        if addresses
        else {}
    )

    if not isinstance(decoded,dict):
        raise RuntimeError(
            "CANARY_005_ALT_PRELOAD_NOT_MAPPING"
        )

    live_tables={
        str(k):v
        for k,v in decoded.items()
        if v
    }

    clean={}

    for token,alts in token_alts.items():
        usable=[
            x for x in alts
            if x in live_tables
        ]

        if usable:
            clean[token]=usable

            print(
                "[CANARY_005_ALT_READY] "
                "token=%s alt=%s"
                %(
                    token[:10],
                    usable[0],
                ),
                flush=True,
            )

        else:
            print(
                "[CANARY_005_ALT_HOLD] "
                "token=%s "
                "reason=SAVED_ALT_NOT_LIVE"
                %token[:10],
                flush=True,
            )

    globals()[
        "PRELOADED_ALTS"
    ]=clean

    globals()[
        "PRELOADED_ALT_TABLES"
    ]=live_tables

    q87.c.alt_accounts=(
        _canonical_cached_alt_accounts
    )

    print(
        "[CANARY_005_ALT_PRELOAD] "
        "ready_tokens=%d "
        "saved_token_alts=%d "
        "live_tables=%d "
        "hot_path_alt_rpc=FALSE"
        %(
            len(READY_TOKENS),
            len(clean),
            len(live_tables),
        ),
        flush=True,
    )

    return clean
""".strip()

COMPILE = r"""
def compile_current(
    user,
    route
):
    signer=globals().get(
        "SIGNER"
    )

    if signer is None:
        raise RuntimeError(
            "CANARY_005_SIGNER_NOT_INITIALIZED"
        )

    blockhash=BLOCKHASH.get()

    token=str(
        route.get("token")
        or ""
    )

    base_alts=list(
        route.get("base_alts")
        or []
    )

    saved_alts=list(
        (
            globals().get(
                "PRELOADED_ALTS",
                {}
            )
            or {}
        ).get(
            token,
            []
        )
        or []
    )

    combined=list(
        dict.fromkeys(
            base_alts+saved_alts
        )
    )

    alt_options=[]

    if combined:
        alt_options.append(
            combined
        )

    if base_alts!=combined:
        alt_options.append(
            base_alts
        )

    if not alt_options:
        alt_options=[
            []
        ]

    candidates=list(
        q87.repaired_candidates(
            route
        )
    )

    attempts=[]

    for candidate in candidates:
        name=str(
            candidate.get(
                "name",
                "UNKNOWN"
            )
        )

        if "PUMP_METEORA_ONLY" in name:
            print(
                "[CANARY_005_COMPILE_ATTEMPT] "
                "candidate=%s "
                "reject=LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL"
                %name,
                flush=True,
            )
            continue

        for alts in alt_options:
            try:
                comp=q87.compile_candidate(
                    user,
                    candidate[
                        "instructions"
                    ],
                    [list(alts)],
                    blockhash,
                )
            except Exception as exc:
                row={
                    "candidate":name,
                    "alts":len(alts),
                    "error":"%s:%s"%(
                        type(exc).__name__,
                        str(exc),
                    ),
                }
                attempts.append(row)

                print(
                    "[CANARY_005_COMPILE_ATTEMPT] "
                    "candidate=%s alts=%d error=%s"
                    %(
                        name,
                        len(alts),
                        row["error"],
                    ),
                    flush=True,
                )
                continue

            if not isinstance(comp,dict):
                attempts.append({
                    "candidate":name,
                    "alts":len(alts),
                    "error":"NON_MAPPING_COMPILE",
                })
                continue

            if not comp.get("ok"):
                error=str(
                    comp.get("error")
                    or "UNKNOWN"
                )

                attempts.append({
                    "candidate":name,
                    "alts":len(alts),
                    "error":error,
                })

                print(
                    "[CANARY_005_COMPILE_ATTEMPT] "
                    "candidate=%s alts=%d error=%s"
                    %(
                        name,
                        len(alts),
                        error,
                    ),
                    flush=True,
                )
                continue

            unsigned=comp["unsigned"]

            print(
                "[CANARY_005_COMPILE_ATTEMPT] "
                "candidate=%s alts=%d "
                "unsigned_bytes=%d status=COMPILED"
                %(
                    name,
                    len(alts),
                    len(unsigned),
                ),
                flush=True,
            )

            fee_result=q87.c.rpc(
                "getFeeForMessage",
                [
                    base64.b64encode(
                        comp["msg"]
                    ).decode(),
                    {
                        "commitment":
                            "processed"
                    },
                ],
            )

            if not isinstance(
                fee_result,
                dict
            ):
                raise RuntimeError(
                    "CANARY_005_FEE_RESULT_NOT_MAPPING:"
                    +type(
                        fee_result
                    ).__name__
                )

            fee_lamports=(
                fee_result.get(
                    "value"
                )
            )

            if (
                not isinstance(
                    fee_lamports,
                    int
                )
                or fee_lamports<0
            ):
                raise RuntimeError(
                    "CANARY_005_BAD_FEE_VALUE:"
                    +str(
                        fee_lamports
                    )
                )

            raw=q87.c.signed_tx(
                comp["msg"],
                signer,
            )

            if len(raw)>MAX_TX_BYTES:
                attempts.append({
                    "candidate":name,
                    "alts":len(alts),
                    "error":
                        "SIGNED_TX_TOO_LARGE:"
                        +str(len(raw)),
                })

                print(
                    "[CANARY_005_COMPILE_ATTEMPT] "
                    "candidate=%s alts=%d "
                    "signed_bytes=%d "
                    "status=SIGNED_TOO_LARGE"
                    %(
                        name,
                        len(alts),
                        len(raw),
                    ),
                    flush=True,
                )
                continue

            print(
                "[CANARY_005_COMPILE_PASS] "
                "candidate=%s "
                "alts=%d "
                "signed_bytes=%d "
                "fee=%d"
                %(
                    name,
                    len(alts),
                    len(raw),
                    fee_lamports,
                ),
                flush=True,
            )

            return {
                "ok":True,
                "candidate":name,
                "bytes":len(raw),
                "msg":comp["msg"],
                "raw":raw,
                "fee_lamports":
                    int(fee_lamports),
                "alts":
                    list(alts),
                "attempts":attempts,
            }

    return {
        "ok":False,
        "reason":
            "NO_LEGAL_COMPACT_TX",
        "attempts":attempts,
    }
""".strip()

TEST_SOURCE='from __future__ import annotations\nimport ast\nfrom pathlib import Path\nimport unittest\n\nTARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=TARGET.read_text(encoding="utf-8")\n        cls.tree=ast.parse(cls.src)\n\n    def fn(self,name):\n        rows=[n for n in self.tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]\n        self.assertEqual(len(rows),1,name)\n        return rows[0]\n\n    def srcfn(self,name):\n        return ast.get_source_segment(self.src,self.fn(name)) or ""\n\n    def test_canary_size_preserved(self):\n        s=self.srcfn("exact_best")\n        self.assertIn("0.005",s)\n        for bad in ("0.001","0.010","0.025","0.050","0.100","0.180","0.280","0.500","1.000","1.400"):\n            self.assertNotIn(bad,s)\n\n    def test_saved_alt_preload_exists(self):\n        s=self.srcfn("preload_canary_saved_alts")\n        self.assertIn("_load_alt_state",s)\n        self.assertIn("alt_accounts",s)\n        self.assertIn("PRELOADED_ALTS",s)\n        self.assertIn("PRELOADED_ALT_TABLES",s)\n\n    def test_hot_compile_uses_preloaded_alt_first(self):\n        s=self.srcfn("compile_current")\n        self.assertIn("PRELOADED_ALTS",s)\n        self.assertIn("CANARY_005_COMPILE_ATTEMPT",s)\n        self.assertNotIn("_saved_alt(",s)\n        self.assertNotIn("_apply_saved_alt(",s)\n\n    def test_no_hot_alt_rpc(self):\n        s=self.srcfn("_canonical_cached_alt_accounts")\n        self.assertNotIn("rpc(",s)\n        self.assertIn("CANARY_005_ALT_NOT_PRELOADED",s)\n\n    def test_preload_happens_before_blockhash(self):\n        run=self.srcfn("run")\n        self.assertLess(run.index("preload_canary_saved_alts"),run.index("BLOCKHASH.start"))\n\n    def test_shell_remains_rejected(self):\n        s=self.srcfn("compile_current")\n        self.assertIn("PUMP_METEORA_ONLY",s)\n        self.assertIn("LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",s)\n\n    def test_signed_fee_sim_contract_preserved(self):\n        c=self.srcfn("compile_current")\n        sim=self.srcfn("simulate_current")\n        self.assertIn(\'"getFeeForMessage"\',c)\n        self.assertIn("q87.c.signed_tx",c)\n        self.assertIn(\'"sigVerify":True\',sim.replace(" ","").replace("\\n",""))\n\n    def test_broadcast_still_disabled(self):\n        self.assertIn(\'"[BROADCAST] disabled"\',self.src)\n        self.assertNotIn("q87.c.send(",self.src)\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def fn_node(src,name):
    tree=parse(
        src,
        "TARGET"
    )

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


def replace_function(src,name,replacement):
    node=fn_node(
        src,
        name
    )

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


def insert_before_function(src,name,block):
    node=fn_node(
        src,
        name
    )

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
        +"\n\n\n"
        +src[start:]
    )


def insert_preload_call(src):
    tree=parse(
        src,
        "TARGET"
    )

    runs=[
        n for n in tree.body
        if isinstance(n,ast.FunctionDef)
        and n.name=="run"
    ]

    if len(runs)!=1:
        raise RuntimeError(
            f"RUN_SEAM_COUNT:{len(runs)}"
        )

    hits=[]

    for node in ast.walk(runs[0]):
        if not isinstance(node,ast.Expr):
            continue

        call=node.value

        if not isinstance(call,ast.Call):
            continue

        f=call.func

        if (
            isinstance(f,ast.Attribute)
            and isinstance(f.value,ast.Name)
            and f.value.id=="BLOCKHASH"
            and f.attr=="start"
        ):
            hits.append(node)

    if len(hits)!=1:
        raise RuntimeError(
            "BLOCKHASH_START_SEAM_COUNT:"
            +str(len(hits))
        )

    node=hits[0]
    lines=src.splitlines(
        keepends=True
    )

    start=sum(
        len(x)
        for x in lines[:node.lineno-1]
    )

    indent=" " * node.col_offset

    addition=(
        indent
        +"preload_canary_saved_alts(root)\n\n"
    )

    return (
        src[:start]
        +addition
        +src[start:]
    )


def main():
    if not TARGET.is_file():
        raise RuntimeError(
            "TARGET_NOT_FOUND:"
            +str(TARGET)
        )

    original=TARGET.read_text(
        encoding="utf-8"
    )

    parse(
        original,
        "ORIGINAL_TARGET"
    )

    # Prove we are modifying the already-certified 0.005 build,
    # not an older or guessed source state.
    exact=ast.get_source_segment(
        original,
        fn_node(
            original,
            "exact_best"
        ),
    ) or ""

    comp=ast.get_source_segment(
        original,
        fn_node(
            original,
            "compile_current"
        ),
    ) or ""

    sim=ast.get_source_segment(
        original,
        fn_node(
            original,
            "simulate_current"
        ),
    ) or ""

    if "0.005" not in exact:
        raise RuntimeError(
            "CANARY_005_ACTIVE_LADDER_NOT_FOUND"
        )

    for required in (
        '"getFeeForMessage"',
        "q87.c.signed_tx",
    ):
        if required not in comp:
            raise RuntimeError(
                "CANARY_005_PRIOR_SEAM_MISSING:"
                +required
            )

    if "sigVerify" not in sim or "True" not in sim:
        raise RuntimeError(
            "CANARY_005_SIGVERIFY_TRUE_NOT_FOUND"
        )

    if "preload_canary_saved_alts" in original:
        raise RuntimeError(
            "CANARY_005_ALT_CUTOVER_ALREADY_PRESENT"
        )

    candidate=insert_before_function(
        original,
        "compile_current",
        PRELOAD,
    )

    candidate=replace_function(
        candidate,
        "compile_current",
        COMPILE,
    )

    candidate=insert_preload_call(
        candidate
    )

    parse(
        candidate,
        "GENERATED_TARGET"
    )

    parse(
        TEST_SOURCE,
        "GENERATED_TEST"
    )

    # Required contract checks all happen before writes.
    required=(
        "preload_canary_saved_alts(root)",
        "PRELOADED_ALTS",
        "PRELOADED_ALT_TABLES",
        "hot_path_alt_rpc=FALSE",
        "LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",
        '"getFeeForMessage"',
        "q87.c.signed_tx",
        "[BROADCAST] disabled",
    )

    missing=[
        x for x in required
        if x not in candidate
    ]

    if missing:
        raise RuntimeError(
            "GENERATED_CONTRACT_MISSING:"
            +repr(missing)
        )

    if "q87.c.send(" in candidate:
        raise RuntimeError(
            "UNEXPECTED_BROADCAST_SEAM"
        )

    TARGET.write_text(
        candidate,
        encoding="utf-8"
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8"
    )

    print(
        "[PASS] CANARY-005 saved-ALT canonical compaction installed"
    )
    print(
        "[PASS] existing QARB-096 saved ALT state reused"
    )
    print(
        "[PASS] ALT table contents preloaded before hot execution"
    )
    print(
        "[PASS] hot-path ALT account RPC disabled"
    )
    print(
        "[PASS] PUMP_METEORA_ONLY remains rejected"
    )
    print(
        "[PASS] exact 0.005 + real fee + signed sigVerify path preserved"
    )
    print(
        "[PASS] scanner / WebSocket / pair identity untouched"
    )
    print(
        "[PASS] broadcast remains disabled pending physical compile+sim proof"
    )


if __name__=="__main__":
    main()
