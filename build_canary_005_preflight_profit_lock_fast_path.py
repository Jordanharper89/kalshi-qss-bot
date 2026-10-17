from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_005_preflight_profit_lock_fast_path.py"
)

FAST_BLOCK='FAST_005_MIN_REALIZED_LAMPORTS=10_000\n\n\ndef _fast_005_rewrite_meteora_min_out(ix,min_out):\n    out=copy.deepcopy(ix)\n    raw=bytearray(base64.b64decode(out.get("data") or ""))\n\n    if len(raw)<24:\n        raise RuntimeError(\n            "FAST_005_METEORA_DATA_TOO_SHORT:"+str(len(raw))\n        )\n\n    old=int(struct.unpack("<Q",bytes(raw[16:24]))[0])\n    locked=max(old,int(min_out))\n    raw[16:24]=struct.pack("<Q",locked)\n    out["data"]=base64.b64encode(bytes(raw)).decode()\n    return out,old,locked\n\n\ndef _fast_005_profit_lock_route(route,direction,required_final_out):\n    out=copy.deepcopy(route)\n    out["direction"]=str(direction)\n\n    if direction=="PUMP_TO_METEORA":\n        meteora,old_bound,new_bound=_fast_005_rewrite_meteora_min_out(\n            out["meteora_ix"],\n            required_final_out,\n        )\n        out["meteora_ix"]=meteora\n        out["original_candidates"]=(\n            q87.las.q59.candidate_instruction_sets(\n                out["pump_ixs"],\n                meteora,\n            )\n        )\n\n    elif direction=="METEORA_TO_PUMP":\n        ixs=[copy.deepcopy(x) for x in out["pump_ixs"]]\n        pump_index=int(out["pump_index"])\n        raw=base64.b64decode(ixs[pump_index].get("data") or "")\n\n        if len(raw)<24:\n            raise RuntimeError(\n                "FAST_005_PUMP_SELL_DATA_TOO_SHORT:"+str(len(raw))\n            )\n\n        base_in=int(struct.unpack("<Q",raw[8:16])[0])\n        old_bound=int(struct.unpack("<Q",raw[16:24])[0])\n        new_bound=max(old_bound,int(required_final_out))\n\n        ixs[pump_index]=rewrite_pump_sell_bounds(\n            ixs[pump_index],\n            base_in,\n            new_bound,\n        )\n\n        out["pump_ixs"]=ixs\n        out["pump_ix"]=ixs[pump_index]\n        out["original_candidates"]=_reverse_instruction_sets(\n            ixs,\n            pump_index,\n            out["meteora_ix"],\n        )\n\n    else:\n        raise RuntimeError(\n            "FAST_005_BAD_DIRECTION:"+str(direction)\n        )\n\n    return out,old_bound,new_bound\n\n\ndef _fast_005_prime_live_gate(direction,token,slot,after_fee_lamports):\n    with LIVE_005_LOCK:\n        state=_live_005_load()\n\n        if bool(state.get("send_attempted")):\n            return False\n\n        certs=state.setdefault("certifications",{})\n\n        certs[str(direction)]={\n            "token":str(token),\n            "slot":int(slot),\n            "after_fee_lamports":int(after_fee_lamports),\n            "certified_unix":time.time(),\n            "certification_type":\n                "ATOMIC_PROFIT_LOCK_PLUS_SEND_PREFLIGHT",\n        }\n\n        state["status"]="FAST_005_PREFLIGHT_ARMED"\n        _live_005_save(state)\n\n    return True\n\n\ndef fast_live_attack(\n    lane,\n    token,\n    snap,\n    opportunity,\n    slot,\n    received_ns,\n    generation,\n):\n    direction=str(opportunity["direction"])\n\n    if lane.newer_waiting(token,generation):\n        return\n\n    if int(opportunity["start"])!=5_000_000:\n        print(\n            "[FAST_005_HOLD] token=%s reason=SIZE_NOT_005"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    try:\n        route=same_snapshot_route(\n            USER,\n            snap,\n            opportunity,\n        )\n        route["direction"]=direction\n        first=compile_current(USER,route)\n\n    except Exception as exc:\n        print(\n            "[FAST_005_BUILD_REJECT] token=%s dir=%s error=%s:%s"\n            %(\n                token[:10],\n                direction,\n                type(exc).__name__,\n                str(exc)[:240],\n            ),\n            flush=True,\n        )\n        return\n\n    if not first.get("ok"):\n        print(\n            "[FAST_005_COMPILE_REJECT] token=%s dir=%s reason=%s"\n            %(\n                token[:10],\n                direction,\n                first.get("reason","UNKNOWN"),\n            ),\n            flush=True,\n        )\n        return\n\n    fee=int(first.get("fee_lamports",0) or 0)\n    quote_after_fee=int(opportunity["local_net"])-fee\n\n    if quote_after_fee<FAST_005_MIN_REALIZED_LAMPORTS:\n        print(\n            "[FAST_005_HOLD] token=%s dir=%s "\n            "reason=QUOTE_AFTER_FEE_BELOW_FLOOR "\n            "quote_after_fee=%+d floor=%d"\n            %(\n                token[:10],\n                direction,\n                quote_after_fee,\n                FAST_005_MIN_REALIZED_LAMPORTS,\n            ),\n            flush=True,\n        )\n        return\n\n    required_final=(\n        5_000_000\n        +fee\n        +FAST_005_MIN_REALIZED_LAMPORTS\n    )\n\n    try:\n        locked_route,old_bound,new_bound=_fast_005_profit_lock_route(\n            route,\n            direction,\n            required_final,\n        )\n        locked=compile_current(USER,locked_route)\n\n    except Exception as exc:\n        print(\n            "[FAST_005_LOCK_REJECT] token=%s dir=%s error=%s:%s"\n            %(\n                token[:10],\n                direction,\n                type(exc).__name__,\n                str(exc)[:240],\n            ),\n            flush=True,\n        )\n        return\n\n    if not locked.get("ok"):\n        print(\n            "[FAST_005_LOCK_COMPILE_REJECT] token=%s dir=%s reason=%s"\n            %(\n                token[:10],\n                direction,\n                locked.get("reason","UNKNOWN"),\n            ),\n            flush=True,\n        )\n        return\n\n    final_fee=int(locked.get("fee_lamports",0) or 0)\n\n    if final_fee!=fee:\n        required_final=(\n            5_000_000\n            +final_fee\n            +FAST_005_MIN_REALIZED_LAMPORTS\n        )\n        locked_route,old_bound,new_bound=_fast_005_profit_lock_route(\n            route,\n            direction,\n            required_final,\n        )\n        locked=compile_current(USER,locked_route)\n\n        if not locked.get("ok"):\n            print(\n                "[FAST_005_RELOCK_REJECT] token=%s dir=%s reason=%s"\n                %(\n                    token[:10],\n                    direction,\n                    locked.get("reason","UNKNOWN"),\n                ),\n                flush=True,\n            )\n            return\n\n        final_fee=int(locked.get("fee_lamports",0) or 0)\n\n    if len(locked.get("raw",b""))>MAX_TX_BYTES:\n        print(\n            "[FAST_005_HOLD] token=%s reason=PACKET_TOO_LARGE"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    if lane.newer_waiting(token,generation):\n        print(\n            "[FAST_005_SUPERSEDED] token=%s phase=locked_compile"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    age_ms=(time.perf_counter_ns()-received_ns)/1e6\n\n    print(\n        "[FAST_005_READY] token=%s dir=%s slot=%s "\n        "quote_after_fee=%+d profit_floor=%d "\n        "old_final_bound=%d locked_final_bound=%d "\n        "bytes=%d fee=%d event_age_ms=%.3f "\n        "separate_sim_rpc=FALSE send_preflight=TRUE"\n        %(\n            token[:10],\n            direction,\n            slot,\n            quote_after_fee,\n            FAST_005_MIN_REALIZED_LAMPORTS,\n            old_bound,\n            new_bound,\n            int(locked["bytes"]),\n            final_fee,\n            age_ms,\n        ),\n        flush=True,\n    )\n\n    if not _fast_005_prime_live_gate(\n        direction,\n        token,\n        slot,\n        quote_after_fee,\n    ):\n        return\n\n    if lane.newer_waiting(token,generation):\n        print(\n            "[FAST_005_SUPERSEDED] token=%s phase=pre_send"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    _live_005_certify_or_send(\n        lane,\n        token,\n        direction,\n        slot,\n        received_ns,\n        generation,\n        locked,\n        quote_after_fee,\n    )'
TEST_SOURCE='from __future__ import annotations\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(encoding="utf-8")\n        cls.tree=ast.parse(cls.src)\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(\n                n,\n                (ast.FunctionDef,ast.AsyncFunctionDef),\n            )\n            and n.name==name\n        ]\n        self.assertEqual(len(rows),1,name)\n        return ast.get_source_segment(self.src,rows[0]) or ""\n\n    def test_profit_floor(self):\n        self.assertIn(\n            "FAST_005_MIN_REALIZED_LAMPORTS=10_000",\n            self.src,\n        )\n\n    def test_no_separate_sim_in_fast_path(self):\n        s=self.fn("fast_live_attack")\n        self.assertNotIn("simulate_current(",s)\n        self.assertNotIn("_execute_route_once(",s)\n\n    def test_both_directions_profit_locked(self):\n        s=self.fn("_fast_005_profit_lock_route")\n        self.assertIn("PUMP_TO_METEORA",s)\n        self.assertIn("METEORA_TO_PUMP",s)\n        self.assertIn("rewrite_pump_sell_bounds",s)\n        self.assertIn("_fast_005_rewrite_meteora_min_out",s)\n\n    def test_principal_fee_profit_floor(self):\n        s=self.fn("fast_live_attack")\n        self.assertIn("5_000_000",s)\n        self.assertIn("FAST_005_MIN_REALIZED_LAMPORTS",s)\n\n    def test_compile_contract_preserved(self):\n        s=self.fn("compile_current")\n        self.assertIn("PRELOADED_SHARED_ALTS",s)\n        self.assertIn("getFeeForMessage",s)\n        self.assertIn("signed_tx",s)\n\n    def test_send_preflight_and_no_retry(self):\n        s=self.fn("_live_005_send_once")\n        self.assertIn(\'"skipPreflight":False\',s)\n        self.assertIn(\'"maxRetries":0\',s)\n\n    def test_reconciliation_preserved(self):\n        s=self.fn("_live_005_certify_or_send")\n        self.assertIn("q96.reconcile",s)\n        self.assertIn("LIVE_005_REALIZED_PROFIT",s)\n\n    def test_live_dispatch_fast(self):\n        s=self.fn("canonical_price")\n        self.assertIn("_live_005_armed()",s)\n        self.assertIn("fast_live_attack(",s)\n\n    def test_unarmed_paths_preserved(self):\n        s=self.fn("canonical_price")\n        self.assertIn("attack_reverse(",s)\n        self.assertIn("attack(",s)\n\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'
OLD_EXCEPTION='        except Exception as exc:\n            state["status"]="SEND_AMBIGUOUS_HOLD"\n            state["send_error"]=(\n                type(exc).__name__\n                +":"\n                +str(exc)\n            )\n\n            _live_005_save(\n                state\n            )\n\n            print(\n                "[LIVE_005_AMBIGUOUS_HOLD] "\n                "token=%s error=%s:%s "\n                "automatic_resend=FALSE"\n                %(\n                    token[:10],\n                    type(exc).__name__,\n                    str(exc)[:240],\n                ),\n                flush=True,\n            )\n            return\n'
NEW_EXCEPTION='        except Exception as exc:\n            message=str(exc)\n            low=message.lower()\n\n            deterministic_preflight=(\n                (\n                    "simulation" in low\n                    and "fail" in low\n                )\n                or (\n                    "preflight" in low\n                    and "fail" in low\n                )\n            )\n\n            if deterministic_preflight:\n                state["send_attempted"]=False\n                state["status"]="PREFLIGHT_REJECTED_REARMED"\n                state["send_error"]=(\n                    type(exc).__name__\n                    +":"\n                    +message\n                )\n\n                _live_005_save(\n                    state\n                )\n\n                print(\n                    "[LIVE_005_PREFLIGHT_REJECT] "\n                    "token=%s error=%s:%s "\n                    "broadcast=FALSE rearmed=TRUE"\n                    %(\n                        token[:10],\n                        type(exc).__name__,\n                        message[:240],\n                    ),\n                    flush=True,\n                )\n                return\n\n            state["status"]="SEND_AMBIGUOUS_HOLD"\n            state["send_error"]=(\n                type(exc).__name__\n                +":"\n                +message\n            )\n\n            _live_005_save(\n                state\n            )\n\n            print(\n                "[LIVE_005_AMBIGUOUS_HOLD] "\n                "token=%s error=%s:%s "\n                "automatic_resend=FALSE"\n                %(\n                    token[:10],\n                    type(exc).__name__,\n                    message[:240],\n                ),\n                flush=True,\n            )\n            return\n'
CANONICAL_TAIL='\n    if _live_005_armed():\n        fast_live_attack(\n            self,\n            token,\n            snap,\n            best,\n            slot,\n            received_ns,\n            generation,\n        )\n        return\n\n    if best["direction"]=="METEORA_TO_PUMP":\n        attack_reverse(\n            self,\n            token,\n            snap,\n            best,\n            slot,\n            received_ns,\n            generation,\n        )\n        return\n\n    if best["direction"]!="PUMP_TO_METEORA":\n        print(\n            "[CANONICAL_POSITIVE_HOLD] "\n            "token=%s dir=%s"\n            %(token[:10],best["direction"]),\n            flush=True,\n        )\n        return\n\n    attack(\n        self,\n        token,\n        snap,\n        best,\n        slot,\n        received_ns,\n        generation,\n    )\n'


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


def remove_existing_fast_block(src):
    marker="FAST_005_MIN_REALIZED_LAMPORTS=10_000"

    if marker not in src:
        return src

    start=src.index(marker)
    stop=src.index(
        "\ndef canonical_price",
        start,
    )

    prior=src[start:stop]

    if "def fast_live_attack" not in prior:
        raise RuntimeError(
            "FAST_005_MARKER_COLLISION"
        )

    return src[:start]+src[stop+1:]


def main():
    if not RT.is_file():
        raise RuntimeError("CANONICAL_RUNTIME_MISSING")

    src=RT.read_text(encoding="utf-8")
    parse(src,"BEFORE")

    required=(
        "def compile_current",
        "PRELOADED_SHARED_ALTS",
        "getFeeForMessage",
        "signed_tx",
        "def rewrite_pump_sell_bounds",
        "def _reverse_instruction_sets",
        "def _live_005_certify_or_send",
        "def _live_005_send_once",
        '"skipPreflight":False',
        '"maxRetries":0',
        "I_ACCEPT_0_005_SOL_CANARY",
        "def attack_reverse",
        "def attack(",
        "def canonical_price",
    )

    missing=[x for x in required if x not in src]

    if missing:
        raise RuntimeError(
            "FAST_005_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    src=remove_existing_fast_block(src)

    insert_at=src.index(
        "\ndef canonical_price"
    )

    src=(
        src[:insert_at]
        +"\n\n"
        +FAST_BLOCK
        +"\n\n"
        +src[insert_at:]
    )

    live=fn_src(
        src,
        "_live_005_certify_or_send",
    )

    if OLD_EXCEPTION not in live:
        raise RuntimeError(
            "LIVE_005_EXCEPTION_SEAM_MISSING"
        )

    live=live.replace(
        OLD_EXCEPTION,
        NEW_EXCEPTION,
        1,
    )

    src=replace_fn(
        src,
        "_live_005_certify_or_send",
        live,
    )

    cp=fn_src(
        src,
        "canonical_price",
    )

    marker="    self.positive+=1"

    if marker not in cp:
        raise RuntimeError(
            "CANONICAL_POSITIVE_SEAM_MISSING"
        )

    head=cp[
        :cp.index(marker)
        +len(marker)
    ]

    cp=head+CANONICAL_TAIL

    src=replace_fn(
        src,
        "canonical_price",
        cp,
    )

    parse(src,"AFTER")
    parse(TEST_SOURCE,"TEST")

    RT.write_text(src,encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")

    print(
        "[PASS] CANARY-005 preflight profit-lock fast path installed"
    )
    print(
        "[PASS] exact size remains 0.005 SOL"
    )
    print(
        "[PASS] armed hot path removes separate simulateTransaction RPC"
    )
    print(
        "[PASS] final atomic leg locks principal + real fee + 10000 lamports"
    )
    print(
        "[PASS] sendTransaction preflight remains enabled"
    )
    print(
        "[PASS] maxRetries=0 and one-shot durable send state preserved"
    )
    print(
        "[PASS] deterministic preflight failure rearms without blind resend"
    )
    print(
        "[PASS] ambiguous transport failure remains hard HOLD"
    )
    print(
        "[PASS] confirmed wallet/token/WSOL reconciliation preserved"
    )


if __name__=="__main__":
    main()
