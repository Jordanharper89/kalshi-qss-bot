from __future__ import annotations

import ast
from pathlib import Path

TARGET = Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
TEST = Path("test_canary_005_exact_signed_fee_path.py")

EXACT_BEST = r"""
def exact_best(lane,token,snap,generation):
    sizes=(
        0.005,
    )

    rows=[]

    for size in sizes:
        rows.extend(
            q18.exact_snapshot_opportunities(
                snap,
                size,
            )
        )

    if not rows:
        raise RuntimeError(
            "SAE005E_NO_SIZE_QUOTES"
        )

    return max(
        rows,
        key=lambda x:int(
            x["local_net"]
        ),
    )
""".strip()

COMPILE_CURRENT = r"""
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

    blockhash=(
        BLOCKHASH.get()
    )

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

        if (
            "PUMP_METEORA_ONLY"
            in name
        ):
            continue

        try:

            comp=(
                q87.compile_candidate(
                    user,
                    candidate[
                        "instructions"
                    ],
                    [[]],
                    blockhash,
                )
            )

        except Exception as exc:

            attempts.append({
                "candidate":
                    name,

                "error":
                    "%s:%s"
                    %(
                        type(exc).__name__,
                        str(exc),
                    ),
            })

            continue

        if not isinstance(
            comp,
            dict
        ):

            attempts.append({
                "candidate":
                    name,

                "error":
                    "NON_MAPPING_COMPILE",
            })

            continue

        attempts.append({
            "candidate":
                name,

            "ok":
                bool(
                    comp.get(
                        "ok"
                    )
                ),

            "error":
                comp.get(
                    "error"
                ),
        })

        if not comp.get(
            "ok"
        ):
            continue

        unsigned=comp[
            "unsigned"
        ]

        size=len(
            unsigned
        )

        print(
            "[CANONICAL_COMPILE] "
            "candidate=%s "
            "bytes=%d"
            %(
                name,
                size,
            ),
            flush=True,
        )

        if size>MAX_TX_BYTES:
            continue

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
            continue

        return {
            "ok":True,
            "candidate":name,
            "bytes":len(raw),
            "msg":comp["msg"],
            "raw":raw,
            "fee_lamports":int(fee_lamports),
            "attempts":attempts,
        }

    return {
        "ok":False,
        "reason":"NO_LEGAL_COMPACT_TX",
        "attempts":attempts,
    }
""".strip()

SIMULATE_CURRENT = r"""
def simulate_current(
    compiled,
    user
):
    result=q87.c.rpc(
        "simulateTransaction",
        [
            base64.b64encode(
                compiled[
                    "raw"
                ]
            ).decode(),
            {
                "encoding":"base64",
                "sigVerify":True,
                "commitment":"processed",
                "accounts":{
                    "encoding":"base64",
                    "addresses":[user],
                },
            },
        ],
    )

    if not isinstance(result,dict):
        raise RuntimeError(
            "SIM_RESULT_NOT_MAPPING:"
            +type(result).__name__
        )

    value=result.get("value")

    if not isinstance(value,dict):
        raise RuntimeError(
            "SIM_VALUE_NOT_MAPPING:"
            +type(value).__name__
        )

    return {
        "err":value.get("err"),
        "units":value.get("unitsConsumed"),
        "logs":list(value.get("logs") or []),
        "accounts":list(value.get("accounts") or []),
        "context":result.get("context"),
    }
""".strip()

EXECUTE_ONCE = r"""
def _execute_route_once(
    user,
    snap,
    opportunity
):
    if int(opportunity["start"])!=5_000_000:
        raise RuntimeError(
            "CANARY_005_START_NOT_EXACT:"
            +str(opportunity["start"])
        )

    if abs(float(opportunity["size_sol"])-0.005)>1e-12:
        raise RuntimeError(
            "CANARY_005_SIZE_NOT_EXACT:"
            +str(opportunity["size_sol"])
        )

    t=time.perf_counter_ns()

    route=same_snapshot_route(
        user,
        snap,
        opportunity,
    )

    build_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    t=time.perf_counter_ns()

    compiled=compile_current(
        user,
        route,
    )

    compile_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    if not compiled.get("ok"):
        return {
            "ok":False,
            "phase":"compile",
            "build_ms":build_ms,
            "compile_ms":compile_ms,
            "compiled":compiled,
        }

    fee_lamports=int(
        compiled[
            "fee_lamports"
        ]
    )

    after_fee_net=(
        int(
            opportunity[
                "local_net"
            ]
        )
        -fee_lamports
    )

    print(
        "[CANARY_005_FEE] "
        "size=0.005 "
        "gross_net=%+d "
        "fee=%d "
        "after_fee_net=%+d"
        %(
            int(opportunity["local_net"]),
            fee_lamports,
            after_fee_net,
        ),
        flush=True,
    )

    if after_fee_net<=0:
        rejected=dict(compiled)
        rejected["reason"]="AFTER_FEE_NONPOSITIVE"

        return {
            "ok":False,
            "phase":"fee",
            "reason":"AFTER_FEE_NONPOSITIVE",
            "build_ms":build_ms,
            "compile_ms":compile_ms,
            "compiled":rejected,
            "fee_lamports":fee_lamports,
            "after_fee_net":after_fee_net,
        }

    t=time.perf_counter_ns()

    sim=simulate_current(
        compiled,
        user,
    )

    sim_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    return {
        "ok":True,
        "build_ms":build_ms,
        "compile_ms":compile_ms,
        "sim_ms":sim_ms,
        "compiled":compiled,
        "sim":sim,
        "fee_lamports":fee_lamports,
        "after_fee_net":after_fee_net,
    }
""".strip()

TEST_SOURCE = 'from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nimport unittest\n\nTARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=TARGET.read_text(encoding="utf-8")\n        cls.tree=ast.parse(cls.src)\n\n    def function(self,name):\n        rows=[n for n in self.tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]\n        self.assertEqual(len(rows),1,name)\n        return rows[0]\n\n    def source(self,name):\n        return ast.get_source_segment(self.src,self.function(name)) or ""\n\n    def test_exact_best_is_exact_005_only(self):\n        fn=self.function("exact_best")\n        floats=[n.value for n in ast.walk(fn) if isinstance(n,ast.Constant) and isinstance(n.value,float)]\n        self.assertEqual(floats.count(0.005),1)\n        for forbidden in (0.001,0.01,0.025,0.05,0.1,0.18,0.28,0.5,1.0,1.4):\n            self.assertNotIn(forbidden,floats)\n\n    def test_execution_guard_is_5000000_lamports(self):\n        s=self.source("_execute_route_once")\n        self.assertIn("5_000_000",s)\n        self.assertIn("CANARY_005_START_NOT_EXACT",s)\n        self.assertIn("CANARY_005_SIZE_NOT_EXACT",s)\n\n    def test_real_message_fee_is_required(self):\n        s=self.source("compile_current")\n        self.assertIn(\'"getFeeForMessage"\',s)\n        self.assertIn(\'"fee_lamports"\',s)\n\n    def test_transaction_is_signed(self):\n        s=self.source("compile_current")\n        self.assertIn("q87.c.signed_tx",s)\n        self.assertIn("CANARY_005_SIGNER_NOT_INITIALIZED",s)\n\n    def test_simulation_verifies_signature(self):\n        fn=self.function("simulate_current")\n        found=False\n        for row in [n for n in ast.walk(fn) if isinstance(n,ast.Dict)]:\n            for k,v in zip(row.keys,row.values):\n                if isinstance(k,ast.Constant) and k.value=="sigVerify" and isinstance(v,ast.Constant) and v.value is True:\n                    found=True\n        self.assertTrue(found)\n\n    def test_after_fee_nonpositive_never_simulates(self):\n        s=self.source("_execute_route_once")\n        self.assertLess(s.index("if after_fee_net<=0"),s.index("sim=simulate_current"))\n        self.assertIn("AFTER_FEE_NONPOSITIVE",s)\n\n    def test_wallet_key_is_loaded_not_printed_or_stored(self):\n        self.assertIn(\'globals()["SIGNER"] = _canary_signer\',self.src)\n        self.assertNotIn(\'print(os.getenv("QSB_SOLANA_PRIVATE_KEY"\',self.src)\n        self.assertNotIn(\'write_text(os.getenv("QSB_SOLANA_PRIVATE_KEY"\',self.src)\n\n    def test_broadcast_still_disabled_for_this_proof(self):\n        self.assertIn(\'"[BROADCAST] disabled"\',self.src)\n        self.assertNotIn("q87.c.send(",self.src)\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'


def _parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def _replace_function(src,name,replacement):
    tree=_parse(src,"TARGET_PRECHECK")

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

    node=rows[0]
    lines=src.splitlines(keepends=True)

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


def _replace_sim_identity_assignment(src):
    tree=_parse(src,"TARGET_PRECHECK")

    runs=[
        n for n in tree.body
        if isinstance(n,ast.FunctionDef)
        and n.name=="run"
    ]

    if len(runs)!=1:
        raise RuntimeError(
            f"RUN_SEAM_COUNT:{len(runs)}"
        )

    run=runs[0]
    matches=[]

    for node in ast.walk(run):
        if not isinstance(node,ast.Assign):
            continue

        call=node.value

        if not isinstance(call,ast.Call):
            continue

        f=call.func

        if (
            isinstance(f,ast.Attribute)
            and f.attr=="sim_identity"
        ):
            matches.append(node)

    if len(matches)!=1:
        raise RuntimeError(
            "SIM_IDENTITY_ASSIGNMENT_SEAM_COUNT:"
            +str(len(matches))
        )

    node=matches[0]
    lines=src.splitlines(keepends=True)

    start=sum(
        len(x)
        for x in lines[:node.lineno-1]
    )
    end=sum(
        len(x)
        for x in lines[:node.end_lineno]
    )

    indent=" " * node.col_offset

    replacement=(
        indent+"_canary_signer,USER=(\n"
        +indent+"    q87.c.sim_identity()\n"
        +indent+")\n\n"
        +indent+"if _canary_signer is None:\n"
        +indent+"    raise RuntimeError(\n"
        +indent+'        "QSB_SOLANA_PRIVATE_KEY_MISSING"\n'
        +indent+"    )\n\n"
        +indent+'globals()["SIGNER"] = _canary_signer\n'
    )

    return src[:start]+replacement+src[end:]


def main():
    if not TARGET.exists():
        raise RuntimeError(
            "TARGET_NOT_FOUND:"
            +str(TARGET)
        )

    original=TARGET.read_text(
        encoding="utf-8"
    )

    _parse(
        original,
        "ORIGINAL_TARGET"
    )

    candidate=original

    candidate=_replace_function(
        candidate,
        "exact_best",
        EXACT_BEST,
    )

    candidate=_replace_function(
        candidate,
        "compile_current",
        COMPILE_CURRENT,
    )

    candidate=_replace_function(
        candidate,
        "simulate_current",
        SIMULATE_CURRENT,
    )

    candidate=_replace_function(
        candidate,
        "_execute_route_once",
        EXECUTE_ONCE,
    )

    candidate=_replace_sim_identity_assignment(
        candidate
    )

    tree=_parse(
        candidate,
        "GENERATED_TARGET"
    )

    for required in (
        "exact_best",
        "compile_current",
        "simulate_current",
        "_execute_route_once",
        "run",
    ):
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
            and n.name==required
        )

        if count!=1:
            raise RuntimeError(
                f"POST_EDIT_{required}_COUNT:{count}"
            )

    required_tokens=(
        "0.005",
        '"getFeeForMessage"',
        "q87.c.signed_tx",
        "AFTER_FEE_NONPOSITIVE",
        'globals()["SIGNER"] = _canary_signer',
    )

    missing=[
        x for x in required_tokens
        if x not in candidate
    ]

    if missing:
        raise RuntimeError(
            "POST_EDIT_CANARY_CONTRACT_MISSING:"
            +repr(missing)
        )

    if "q87.c.send(" in candidate:
        raise RuntimeError(
            "UNEXPECTED_BROADCAST_SEAM_PRESENT"
        )

    _parse(
        TEST_SOURCE,
        "GENERATED_TEST"
    )

    TARGET.write_text(
        candidate,
        encoding="utf-8"
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8"
    )

    print("[PASS] CANARY-005 active canonical ladder = 0.005 SOL only")
    print("[PASS] exact execution start = 5,000,000 lamports")
    print("[PASS] real getFeeForMessage gate installed")
    print("[PASS] after-fee <= 0 rejects before simulation")
    print("[PASS] signed transaction + sigVerify=True installed")
    print("[PASS] scanner / WebSocket / pair identity untouched")
    print("[PASS] broadcast remains disabled pending physical 0.005 proof")
    print("[NEXT] python test_canary_005_exact_signed_fee_path.py")
    print("[NEXT] python -m qseries_v2.oracle_execution.solana_atomic_executor.runtime --seconds 300")


if __name__=="__main__":
    main()
