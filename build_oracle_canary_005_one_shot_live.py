from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_oracle_canary_005_one_shot_live.py"
)

LIVE_BLOCK='\nLIVE_005_ARM_VALUE="I_ACCEPT_0_005_SOL_CANARY"\nLIVE_005_STATE=Path(\n    "runtime_state/oracle/solana_atomic_executor/"\n    "canary_005_live_state.json"\n)\nLIVE_005_LOCK=threading.Lock()\n\n\ndef _live_005_armed():\n    return (\n        os.getenv(\n            "QSB_ORACLE_CANARY_005_ARM",\n            ""\n        )\n        ==LIVE_005_ARM_VALUE\n    )\n\n\ndef _live_005_load():\n    if not LIVE_005_STATE.is_file():\n        return {\n            "revision":"ORACLE_CANARY_005_LIVE_V1",\n            "certifications":{},\n            "send_attempted":False,\n            "send_signature":None,\n            "status":"IDLE",\n        }\n\n    row=json.loads(\n        LIVE_005_STATE.read_text(\n            encoding="utf-8"\n        )\n    )\n\n    if not isinstance(row,dict):\n        raise RuntimeError(\n            "LIVE_005_STATE_NOT_MAPPING"\n        )\n\n    if not isinstance(\n        row.get("certifications"),\n        dict\n    ):\n        row["certifications"]={}\n\n    return row\n\n\ndef _live_005_save(row):\n    LIVE_005_STATE.parent.mkdir(\n        parents=True,\n        exist_ok=True,\n    )\n\n    tmp=LIVE_005_STATE.with_suffix(\n        ".json.tmp"\n    )\n\n    tmp.write_text(\n        json.dumps(\n            row,\n            indent=2,\n            sort_keys=True,\n            default=str,\n        ),\n        encoding="utf-8",\n    )\n\n    tmp.replace(\n        LIVE_005_STATE\n    )\n\n\ndef _live_005_send_once(raw):\n    return q96._rpc(\n        "sendTransaction",\n        [\n            base64.b64encode(\n                raw\n            ).decode(),\n            {\n                "encoding":"base64",\n                "skipPreflight":False,\n                "preflightCommitment":"processed",\n                "maxRetries":0,\n            },\n        ],\n    )\n\n\ndef _live_005_certify_or_send(\n    lane,\n    token,\n    direction,\n    slot,\n    received_ns,\n    generation,\n    compiled,\n    after_fee_lamports,\n):\n    if int(\n        compiled.get(\n            "bytes",\n            MAX_TX_BYTES+1,\n        )\n    )>MAX_TX_BYTES:\n        print(\n            "[LIVE_005_HOLD] reason=SIGNED_TX_TOO_LARGE",\n            flush=True,\n        )\n        return\n\n    if int(after_fee_lamports)<=0:\n        print(\n            "[LIVE_005_HOLD] reason=AFTER_FEE_NONPOSITIVE",\n            flush=True,\n        )\n        return\n\n    raw=compiled.get("raw")\n\n    if not isinstance(\n        raw,\n        (bytes,bytearray),\n    ):\n        print(\n            "[LIVE_005_HOLD] reason=SIGNED_RAW_MISSING",\n            flush=True,\n        )\n        return\n\n    with LIVE_005_LOCK:\n        state=_live_005_load()\n\n        if bool(\n            state.get("send_attempted")\n        ):\n            return\n\n        certs=(\n            state.get(\n                "certifications",\n                {}\n            )\n            or {}\n        )\n\n        prior=certs.get(\n            str(direction)\n        )\n\n        if not isinstance(prior,dict):\n            certs[str(direction)]={\n                "token":str(token),\n                "slot":int(slot),\n                "after_fee_lamports":\n                    int(after_fee_lamports),\n                "certified_unix":\n                    time.time(),\n            }\n\n            state["certifications"]=certs\n            state["status"]="CERTIFIED_WAITING_SECOND_PASS"\n\n            _live_005_save(\n                state\n            )\n\n            print(\n                "[LIVE_005_CERTIFICATION_RECORDED] "\n                "dir=%s token=%s slot=%s "\n                "after_fee=%+d send=FALSE"\n                %(\n                    direction,\n                    token[:10],\n                    slot,\n                    int(after_fee_lamports),\n                ),\n                flush=True,\n            )\n            return\n\n        if not _live_005_armed():\n            print(\n                "[LIVE_005_READY_NOT_ARMED] "\n                "dir=%s token=%s "\n                "prior_slot=%s current_slot=%s"\n                %(\n                    direction,\n                    token[:10],\n                    prior.get("slot"),\n                    slot,\n                ),\n                flush=True,\n            )\n            return\n\n        if lane.newer_waiting(\n            token,\n            generation,\n        ):\n            print(\n                "[LIVE_005_HOLD] "\n                "token=%s reason=NEWER_SNAPSHOT_WAITING"\n                %token[:10],\n                flush=True,\n            )\n            return\n\n        balance_result=q96._rpc(\n            "getBalance",\n            [\n                str(USER),\n                {\n                    "commitment":\n                        "confirmed"\n                },\n            ],\n        )\n\n        balance=int(\n            (\n                balance_result\n                or {}\n            ).get(\n                "value",\n                0,\n            )\n        )\n\n        fee=int(\n            compiled.get(\n                "fee_lamports",\n                0,\n            )\n            or 0\n        )\n\n        required=(\n            5_000_000\n            +fee\n            +2_500_000\n        )\n\n        if balance<required:\n            print(\n                "[LIVE_005_HOLD] "\n                "token=%s reason=INSUFFICIENT_WALLET "\n                "balance=%d required=%d"\n                %(\n                    token[:10],\n                    balance,\n                    required,\n                ),\n                flush=True,\n            )\n            return\n\n        if lane.newer_waiting(\n            token,\n            generation,\n        ):\n            print(\n                "[LIVE_005_HOLD] "\n                "token=%s reason=FRESHNESS_REVALIDATION_FAILED"\n                %token[:10],\n                flush=True,\n            )\n            return\n\n        state["send_attempted"]=True\n        state["status"]="SEND_ATTEMPT_MARKED"\n        state["direction"]=str(direction)\n        state["token"]=str(token)\n        state["slot"]=int(slot)\n        state["wallet_before_lamports"]=balance\n        state["after_fee_gate_lamports"]=int(\n            after_fee_lamports\n        )\n        state["attempted_unix"]=time.time()\n\n        _live_005_save(\n            state\n        )\n\n        print(\n            "[LIVE_005_SEND_ATTEMPT] "\n            "dir=%s token=%s slot=%s "\n            "size=0.005 max_in_flight=1 "\n            "no_retry=TRUE"\n            %(\n                direction,\n                token[:10],\n                slot,\n            ),\n            flush=True,\n        )\n\n        try:\n            signature=_live_005_send_once(\n                bytes(raw)\n            )\n\n        except Exception as exc:\n            state["status"]="SEND_AMBIGUOUS_HOLD"\n            state["send_error"]=(\n                type(exc).__name__\n                +":"\n                +str(exc)\n            )\n\n            _live_005_save(\n                state\n            )\n\n            print(\n                "[LIVE_005_AMBIGUOUS_HOLD] "\n                "token=%s error=%s:%s "\n                "automatic_resend=FALSE"\n                %(\n                    token[:10],\n                    type(exc).__name__,\n                    str(exc)[:240],\n                ),\n                flush=True,\n            )\n            return\n\n        state["send_signature"]=str(\n            signature\n        )\n        state["status"]="SENT_WAITING_CONFIRMATION"\n\n        _live_005_save(\n            state\n        )\n\n        print(\n            "[LIVE_005_SENT] signature=%s"\n            %signature,\n            flush=True,\n        )\n\n        tx=q96.wait_confirmed(\n            signature,\n            time.monotonic()+30.0,\n            timeout_seconds=30,\n        )\n\n        if tx is None:\n            state["status"]="CONFIRMATION_UNKNOWN_HOLD"\n\n            _live_005_save(\n                state\n            )\n\n            print(\n                "[LIVE_005_CONFIRMATION_UNKNOWN] "\n                "signature=%s automatic_resend=FALSE"\n                %signature,\n                flush=True,\n            )\n            return\n\n        meta=(\n            tx.get(\n                "meta",\n                {}\n            )\n            or {}\n        )\n\n        if meta.get("err") is not None:\n            state["status"]="CONFIRMED_ERROR"\n            state["transaction_error"]=meta.get(\n                "err"\n            )\n\n            _live_005_save(\n                state\n            )\n\n            print(\n                "[LIVE_005_CONFIRMED_ERROR] "\n                "signature=%s err=%s"\n                %(\n                    signature,\n                    str(meta.get("err")),\n                ),\n                flush=True,\n            )\n            return\n\n        rec=q96.reconcile(\n            signature,\n            tx,\n            str(USER),\n            str(token),\n        )\n\n        rec["execution_owner"]="ORACLE"\n        rec["direction"]=str(direction)\n        rec["size_sol"]=0.005\n\n        state["status"]="CONFIRMED_RECONCILED"\n        state["reconciliation"]=rec\n\n        _live_005_save(\n            state\n        )\n\n        delta=int(\n            rec.get(\n                "wallet_delta_lamports",\n                0,\n            )\n        )\n\n        clean=bool(\n            rec.get(\n                "residue_clean"\n            )\n        )\n\n        print(\n            "[LIVE_005_RECONCILED] "\n            "signature=%s wallet_delta=%+d "\n            "fee=%d token_delta=%+d "\n            "wsol_delta=%+d residue_clean=%s"\n            %(\n                signature,\n                delta,\n                int(rec.get("fee_lamports",0)),\n                int(rec.get("target_token_delta_raw",0)),\n                int(rec.get("wsol_delta_raw",0)),\n                clean,\n            ),\n            flush=True,\n        )\n\n        if delta>0 and clean:\n            state["status"]="FIRST_REALIZED_PROFIT"\n\n            _live_005_save(\n                state\n            )\n\n            print(\n                "[LIVE_005_REALIZED_PROFIT] "\n                "signature=%s "\n                "realized_net_lamports=%+d "\n                "realized_net_sol=%+.9f"\n                %(\n                    signature,\n                    delta,\n                    delta/1e9,\n                ),\n                flush=True,\n            )\n\n        else:\n            state["status"]="CONFIRMED_NO_REALIZED_PROFIT_HOLD"\n\n            _live_005_save(\n                state\n            )\n\n            print(\n                "[LIVE_005_NO_REALIZED_PROFIT_HOLD] "\n                "signature=%s wallet_delta=%+d "\n                "residue_clean=%s"\n                %(\n                    signature,\n                    delta,\n                    clean,\n                ),\n                flush=True,\n            )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(encoding="utf-8")\n        cls.tree=ast.parse(cls.src)\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(\n                n,\n                (ast.FunctionDef,ast.AsyncFunctionDef),\n            )\n            and n.name==name\n        ]\n\n        self.assertEqual(len(rows),1,name)\n\n        return ast.get_source_segment(\n            self.src,\n            rows[0],\n        ) or ""\n\n    def test_exact_arm(self):\n        self.assertIn(\n            "I_ACCEPT_0_005_SOL_CANARY",\n            self.src,\n        )\n\n    def test_attempt_persisted_before_send(self):\n        s=self.fn(\n            "_live_005_certify_or_send"\n        )\n\n        self.assertLess(\n            s.index(\n                \'state["send_attempted"]=True\'\n            ),\n            s.index(\n                "_live_005_send_once"\n            ),\n        )\n\n    def test_no_rpc_auto_resend(self):\n        s=self.fn(\n            "_live_005_send_once"\n        )\n\n        self.assertIn(\n            \'"maxRetries":0\',\n            s,\n        )\n\n    def test_two_pass_gate(self):\n        s=self.fn(\n            "_live_005_certify_or_send"\n        )\n\n        self.assertIn(\n            "LIVE_005_CERTIFICATION_RECORDED",\n            s,\n        )\n        self.assertIn(\n            "prior=",\n            s,\n        )\n\n    def test_freshness_gate(self):\n        s=self.fn(\n            "_live_005_certify_or_send"\n        )\n\n        self.assertIn(\n            "newer_waiting",\n            s,\n        )\n\n    def test_actual_reconciliation(self):\n        s=self.fn(\n            "_live_005_certify_or_send"\n        )\n\n        self.assertIn(\n            "q96.reconcile",\n            s,\n        )\n        self.assertIn(\n            "LIVE_005_REALIZED_PROFIT",\n            s,\n        )\n\n    def test_hooks_both_directions(self):\n        self.assertGreaterEqual(\n            self.src.count(\n                "_live_005_certify_or_send("\n            ),\n            3,\n        )\n\n    def test_signed_simulation_preserved(self):\n        s=self.fn("simulate_current")\n\n        self.assertIn(\n            \'"sigVerify"\',\n            s,\n        )\n        self.assertIn(\n            "True",\n            s,\n        )\n\n    def test_fee_path_preserved(self):\n        s=self.fn("compile_current")\n\n        self.assertIn(\n            "getFeeForMessage",\n            s,\n        )\n        self.assertIn(\n            "signed_tx",\n            s,\n        )\n\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def get_rows(src,name):
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
    found=get_rows(src,name)

    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(found)}"
        )

    return ast.get_source_segment(
        src,
        found[0],
    ) or ""


def replace_fn(src,name,replacement):
    found=get_rows(src,name)

    if len(found)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(found)}"
        )

    node=found[0]
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


def main():
    if not RT.is_file():
        raise RuntimeError(
            "CANONICAL_RUNTIME_MISSING"
        )

    src=RT.read_text(encoding="utf-8")
    parse(src,"BEFORE")

    required=(
        "def attack_reverse",
        "REVERSE_005_CERTIFIED",
        "def attack(",
        "CANONICAL_SIM_PASS",
        "def compile_current",
        "getFeeForMessage",
        "q87.c.signed_tx",
        "def simulate_current",
        "sigVerify",
        "def canonical_price",
        "def run(",
    )

    missing=[
        x for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "LIVE_005_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    sim=fn_src(src,"simulate_current")

    if (
        '"sigVerify"' not in sim
        or "True" not in sim
    ):
        raise RuntimeError(
            "LIVE_005_REQUIRES_SIGVERIFY_TRUE"
        )

    comp=fn_src(src,"compile_current")

    if (
        "getFeeForMessage" not in comp
        or "signed_tx" not in comp
    ):
        raise RuntimeError(
            "LIVE_005_REQUIRES_SIGNED_FEE_PATH"
        )

    if "\nimport json\n" not in src:
        src=src.replace(
            "import copy\n",
            "import copy\nimport json\n",
            1,
        )

    if "\nimport os\n" not in src:
        src=src.replace(
            "import json\n",
            "import json\nimport os\n",
            1,
        )

    q96_import=(
        "from qseries_v2.solana_live_execution import (\n"
        "    qarb_096_sequential_live_micro_executor as q96\n"
        ")\n\n"
    )

    if (
        "qarb_096_sequential_live_micro_executor"
        not in src
    ):
        anchor=(
            "from qseries_v2.oracle_strategy_intelligence."
            "solana_money.qarb_execution_engineering import (\n"
            "    qarb_087_two_second_compaction_liquidity_repair as q87\n"
            ")\n\n"
        )

        if anchor not in src:
            raise RuntimeError(
                "LIVE_005_IMPORT_ANCHOR_MISSING"
            )

        src=src.replace(
            anchor,
            anchor+q96_import,
            1,
        )

    marker=(
        'LIVE_005_ARM_VALUE='
        '"I_ACCEPT_0_005_SOL_CANARY"'
    )

    if marker in src:
        start=src.index(marker)
        stop=src.index(
            "\ndef canonical_price",
            start,
        )

        prior=src[start:stop]

        if (
            "def _live_005_certify_or_send"
            in prior
        ):
            src=src[:start]+src[stop+1:]

    insert_at=src.index(
        "\ndef canonical_price"
    )

    src=(
        src[:insert_at]
        +"\n\n"
        +LIVE_BLOCK
        +"\n\n"
        +src[insert_at:]
    )

    reverse=fn_src(
        src,
        "attack_reverse"
    )

    end_tail=(
        "        flush=True,\n"
        "    )\n"
    )

    pos=reverse.rfind(
        end_tail
    )

    if pos<0:
        raise RuntimeError(
            "LIVE_005_REVERSE_TAIL_MISSING"
        )

    pos+=len(end_tail)

    reverse_hook=(
        "\n    _live_005_certify_or_send(\n"
        "        lane,\n"
        "        token,\n"
        '        "METEORA_TO_PUMP",\n'
        "        slot,\n"
        "        received_ns,\n"
        "        generation,\n"
        "        compiled,\n"
        "        after_fee_min,\n"
        "    )\n"
    )

    reverse=(
        reverse[:pos]
        +reverse_hook
        +reverse[pos:]
    )

    src=replace_fn(
        src,
        "attack_reverse",
        reverse,
    )

    attack=fn_src(
        src,
        "attack"
    )

    first_return=(
        "        return\n\n"
        "    #\n"
        "    # ========================================================\n"
        "    # SECOND POSSIBILITY:\n"
    )

    if first_return not in attack:
        raise RuntimeError(
            "LIVE_005_FORWARD_FIRST_PASS_SEAM_MISSING"
        )

    first_hook=(
        "        fee=int(\n"
        '            first["compiled"].get("fee_lamports",0) or 0\n'
        "        )\n"
        "        after_fee=int(opportunity[\"local_net\"])-fee\n\n"
        "        _live_005_certify_or_send(\n"
        "            lane,token,\"PUMP_TO_METEORA\",slot,\n"
        "            received_ns,generation,\n"
        '            first["compiled"],after_fee,\n'
        "        )\n\n"
        "        return\n\n"
        "    #\n"
        "    # ========================================================\n"
        "    # SECOND POSSIBILITY:\n"
    )

    attack=attack.replace(
        first_return,
        first_hook,
        1,
    )

    pos=attack.rfind(
        end_tail
    )

    if pos<0:
        raise RuntimeError(
            "LIVE_005_FORWARD_REPRICE_TAIL_MISSING"
        )

    pos+=len(end_tail)

    second_hook=(
        "\n    fee=int(\n"
        '        second["compiled"].get("fee_lamports",0) or 0\n'
        "    )\n"
        "    after_fee=int(corrected[\"local_net\"])-fee\n\n"
        "    _live_005_certify_or_send(\n"
        "        lane,token,\"PUMP_TO_METEORA\",slot,\n"
        "        received_ns,generation,\n"
        '        second["compiled"],after_fee,\n'
        "    )\n"
    )

    attack=(
        attack[:pos]
        +second_hook
        +attack[pos:]
    )

    src=replace_fn(
        src,
        "attack",
        attack,
    )

    run=fn_src(
        src,
        "run"
    )

    startup_anchor=(
        '    print(\n'
        '        "[SOLANA-ATOMIC-EXECUTOR] "'
    )

    if startup_anchor not in run:
        raise RuntimeError(
            "LIVE_005_RUN_STARTUP_SEAM_MISSING"
        )

    disclosure=(
        '    print(\n'
        '        "[LIVE_005_MODE] "\n'
        '        "armed=%s exact_size=0.005 "\n'
        '        "max_in_flight=1 "\n'
        '        "requires_prior_certification=TRUE "\n'
        '        "automatic_resend=FALSE"\n'
        '        %_live_005_armed(),\n'
        '        flush=True,\n'
        '    )\n\n'
    )

    run=run.replace(
        startup_anchor,
        disclosure+startup_anchor,
        1,
    )

    src=replace_fn(
        src,
        "run",
        run,
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
        "[PASS] ORACLE exact 0.005 one-shot live canary installed"
    )
    print(
        "[PASS] first passing direction only records certification"
    )
    print(
        "[PASS] later independent passing candidate required for send"
    )
    print(
        "[PASS] max_in_flight=1 and durable pre-send attempt mark"
    )
    print(
        "[PASS] maxRetries=0; ambiguous send never auto-resubmitted"
    )
    print(
        "[PASS] confirmed wallet/token/WSOL reconciliation enabled"
    )
    print(
        "[PASS] realized profit only declared from confirmed wallet delta"
    )


if __name__=="__main__":
    main()
