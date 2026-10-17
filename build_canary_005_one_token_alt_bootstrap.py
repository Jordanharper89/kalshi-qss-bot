from __future__ import annotations

import ast
from pathlib import Path

MOD=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/"
    "bootstrap_canary_005_alts.py"
)

TEST=Path(
    "test_canary_005_alt_bootstrap.py"
)

MODULE_SOURCE='from __future__ import annotations\n\nimport argparse\nimport time\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt\nfrom qseries_v2.solana_live_execution import qarb_096_sequential_live_micro_executor as q96\n\nEXECUTION_AUTHORITY=False\nTRADE_BROADCAST=False\nDEFAULT_PREFIX="3Dgwn5E7H5"\nMAX_TX_BYTES=1232\n\n\ndef _select_pair(state,prefix):\n    rows=[]\n    for pair in list(state.get("pairs") or []):\n        token=str(pair.token)\n        if token.startswith(str(prefix)):\n            rows.append(pair)\n\n    if len(rows)!=1:\n        raise RuntimeError(\n            "CANARY_ALT_PAIR_PREFIX_MATCH_COUNT:%s:%d"\n            %(prefix,len(rows))\n        )\n\n    return rows[0]\n\n\ndef _ensure_runtime_ready(root,state,user,pair):\n    rt.READY_TOKENS.clear()\n    rt.TEMPLATES.clear()\n    rt.METEORA_TEMPLATES.clear()\n\n    token_warm=rt.install_proven_hot_math(\n        state\n    )\n\n    rt.prebuild_templates(\n        state,\n        user,\n    )\n\n    rt.prebuild_meteora_templates(\n        state,\n        user,\n        token_warm,\n    )\n\n    token=str(pair.token)\n\n    if token not in rt.READY_TOKENS:\n        raise RuntimeError(\n            "CANARY_ALT_PAIR_NOT_RUNTIME_READY:"\n            +token\n        )\n\n    rt.q18.worker().warm(\n        str(pair.pump_pool)\n    )\n\n    return token\n\n\ndef _already_saved(root,token):\n    address=q96._saved_alt(\n        root,\n        token,\n    )\n\n    if not address:\n        return None\n\n    print(\n        "[CANARY_ALT_ALREADY_READY] "\n        "token=%s address=%s"\n        %(token[:10],address),\n        flush=True,\n    )\n\n    return address\n\n\ndef _persist_state(\n    root,\n    token,\n    setup,\n    signature,\n    before,\n    after,\n):\n    state=q96._load_alt_state(\n        root\n    )\n\n    tables=state.get("tables")\n    if not isinstance(tables,dict):\n        tables={}\n        state["tables"]=tables\n\n    tables[token]={\n        "address":\n            setup["lookupTable"],\n        "addresses":\n            setup["addresses"],\n        "recent_slot":\n            setup["recentSlot"],\n        "signature":\n            signature,\n        "wallet_delta_lamports":\n            int(after)-int(before),\n        "created_unix":\n            time.time(),\n    }\n\n    q96._atomic(\n        q96._qarb096_alt_state_path(\n            root\n        ),\n        state,\n    )\n\n\ndef _wait_active(alt,setup_slot,deadline):\n    while time.monotonic()<deadline:\n        try:\n            slot=int(\n                q96._rpc(\n                    "getSlot",\n                    [{\n                        "commitment":\n                            "confirmed"\n                    }],\n                )\n            )\n\n            got=q96._rpc(\n                "getAccountInfo",\n                [\n                    alt,\n                    {\n                        "encoding":"base64",\n                        "commitment":\n                            "confirmed",\n                    },\n                ],\n            )\n\n            value=(\n                got.get("value")\n                if isinstance(got,dict)\n                else None\n            )\n\n            if (\n                slot>int(setup_slot)\n                and isinstance(value,dict)\n                and value.get("data")\n            ):\n                return True\n        except Exception:\n            pass\n\n        time.sleep(0.4)\n\n    return False\n\n\ndef bootstrap_one(\n    root=None,\n    token_prefix=DEFAULT_PREFIX,\n    activation_seconds=30.0,\n):\n    root=Path(\n        root or Path.cwd()\n    )\n\n    state,_=rt.q25.prepare_once(\n        root\n    )\n\n    rt.q25.bind_cached_state(\n        state\n    )\n\n    kp,user=rt.q87.c.sim_identity()\n\n    if kp is None:\n        raise RuntimeError(\n            "QSB_SOLANA_PRIVATE_KEY_MISSING"\n        )\n\n    pair=_select_pair(\n        state,\n        token_prefix,\n    )\n\n    token=_ensure_runtime_ready(\n        root,\n        state,\n        user,\n        pair,\n    )\n\n    existing=_already_saved(\n        root,\n        token,\n    )\n\n    if existing:\n        return {\n            "ok":True,\n            "created":False,\n            "token":token,\n            "address":existing,\n        }\n\n    route=q96.native_live_route(\n        user,\n        pair,\n        q96.MICRO_SOL,\n    )\n\n    addresses=q96._alt_addresses_from_route(\n        route,\n        user,\n    )\n\n    if not addresses:\n        raise RuntimeError(\n            "CANARY_ALT_NO_ADDRESSES"\n        )\n\n    setup=q96._build_alt_setup(\n        user,\n        addresses,\n    )\n\n    bh=q96._rpc(\n        "getLatestBlockhash",\n        [{\n            "commitment":\n                "confirmed"\n        }],\n    )["value"]["blockhash"]\n\n    msg,unsigned=rt.q87.c.compile_v0(\n        user,\n        setup["instructions"],\n        [],\n        bh,\n    )\n\n    raw=rt.q87.c.signed_tx(\n        msg,\n        kp,\n    )\n\n    if len(raw)>MAX_TX_BYTES:\n        raise RuntimeError(\n            "CANARY_ALT_SETUP_TOO_LARGE:"\n            +str(len(raw))\n        )\n\n    sim=q96.signed_simulation(\n        raw\n    )\n\n    if sim.get("err") is not None:\n        raise RuntimeError(\n            "CANARY_ALT_SETUP_SIM_ERROR:"\n            +str(sim.get("err"))\n        )\n\n    before=int(\n        q96._rpc(\n            "getBalance",\n            [\n                str(user),\n                {\n                    "commitment":\n                        "confirmed"\n                },\n            ],\n        )["value"]\n    )\n\n    print(\n        "[CANARY_ALT_SETUP] "\n        "token=%s addresses=%d setup_bytes=%d "\n        "simulation=PASS trade_broadcast=FALSE"\n        %(\n            token[:10],\n            len(setup["addresses"]),\n            len(raw),\n        ),\n        flush=True,\n    )\n\n    signature=q96.send_once(\n        raw\n    )\n\n    deadline=(\n        time.monotonic()\n        +max(\n            10.0,\n            float(activation_seconds),\n        )\n    )\n\n    tx=q96.wait_confirmed(\n        signature,\n        deadline,\n    )\n\n    if tx is None:\n        raise RuntimeError(\n            "CANARY_ALT_CONFIRMATION_UNKNOWN:"\n            +str(signature)\n        )\n\n    err=(\n        tx.get("meta",{})\n        or {}\n    ).get("err")\n\n    if err is not None:\n        raise RuntimeError(\n            "CANARY_ALT_CONFIRMED_ERROR:"\n            +str(err)\n        )\n\n    after=int(\n        q96._rpc(\n            "getBalance",\n            [\n                str(user),\n                {\n                    "commitment":\n                        "confirmed"\n                },\n            ],\n        )["value"]\n    )\n\n    _persist_state(\n        root,\n        token,\n        setup,\n        signature,\n        before,\n        after,\n    )\n\n    alt=str(\n        setup["lookupTable"]\n    )\n\n    active=_wait_active(\n        alt,\n        int(tx.get("slot",0) or 0),\n        deadline,\n    )\n\n    print(\n        "[CANARY_ALT_CONFIRMED] "\n        "token=%s address=%s signature=%s "\n        "wallet_delta_lamports=%d active=%s"\n        %(\n            token[:10],\n            alt,\n            signature,\n            after-before,\n            active,\n        ),\n        flush=True,\n    )\n\n    if not active:\n        print(\n            "[CANARY_ALT_NOTE] "\n            "confirmed table persisted; "\n            "canonical runtime will revalidate "\n            "visibility before use",\n            flush=True,\n        )\n\n    return {\n        "ok":True,\n        "created":True,\n        "token":token,\n        "address":alt,\n        "signature":signature,\n        "wallet_delta_lamports":\n            after-before,\n        "active":active,\n    }\n\n\ndef main():\n    p=argparse.ArgumentParser()\n    p.add_argument(\n        "--token-prefix",\n        default=DEFAULT_PREFIX,\n    )\n    p.add_argument(\n        "--activation-seconds",\n        type=float,\n        default=30.0,\n    )\n    a=p.parse_args()\n\n    result=bootstrap_one(\n        token_prefix=a.token_prefix,\n        activation_seconds=\n            a.activation_seconds,\n    )\n\n    if not result.get("ok"):\n        return 1\n\n    print(\n        "[NEXT] python -m "\n        "qseries_v2.oracle_execution."\n        "solana_atomic_executor.runtime "\n        "--seconds 300",\n        flush=True,\n    )\n\n    return 0\n\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
TEST_SOURCE='from __future__ import annotations\n\nimport inspect\nimport unittest\nfrom unittest.mock import patch\n\nfrom qseries_v2.oracle_execution.solana_atomic_executor import (\n    bootstrap_canary_005_alts as m\n)\n\n\nclass T(unittest.TestCase):\n    def test_scope(self):\n        self.assertFalse(m.EXECUTION_AUTHORITY)\n        self.assertFalse(m.TRADE_BROADCAST)\n\n    def test_default_targets_observed_positive_token(self):\n        self.assertEqual(\n            m.DEFAULT_PREFIX,\n            "3Dgwn5E7H5",\n        )\n\n    def test_pair_prefix_must_be_unique(self):\n        class P:\n            def __init__(self,t):\n                self.token=t\n\n        with self.assertRaises(RuntimeError):\n            m._select_pair(\n                {"pairs":[P("ABC1"),P("ABC2")]},\n                "ABC",\n            )\n\n    def test_existing_alt_short_circuits(self):\n        with patch.object(\n            m.q96,\n            "_saved_alt",\n            return_value="ALT1",\n        ):\n            self.assertEqual(\n                m._already_saved(\n                    ".",\n                    "TOKEN",\n                ),\n                "ALT1",\n            )\n\n    def test_bootstrap_uses_q96_proven_seams(self):\n        s=inspect.getsource(\n            m.bootstrap_one\n        )\n\n        for required in (\n            "native_live_route",\n            "_alt_addresses_from_route",\n            "_build_alt_setup",\n            "signed_simulation",\n            "send_once",\n            "wait_confirmed",\n            "_persist_state",\n            "_wait_active",\n        ):\n            self.assertIn(\n                required,\n                s,\n            )\n\n    def test_trade_send_path_absent(self):\n        src=inspect.getsource(m)\n        self.assertNotIn(\n            "q87.c.send(",\n            src,\n        )\n        self.assertIn(\n            "trade_broadcast=FALSE",\n            src,\n        )\n\n    def test_private_key_not_printed_or_stored(self):\n        src=inspect.getsource(m)\n        self.assertNotIn(\n            "QSB_SOLANA_PRIVATE_KEY=",\n            src,\n        )\n        self.assertNotIn(\n            "str(kp)",\n            src,\n        )\n\n    def test_persists_exact_q96_state_path(self):\n        s=inspect.getsource(\n            m._persist_state\n        )\n        self.assertIn(\n            "_qarb096_alt_state_path",\n            s,\n        )\n        self.assertIn(\n            \'"address"\',\n            s,\n        )\n        self.assertIn(\n            \'"addresses"\',\n            s,\n        )\n\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'


def main():
    ast.parse(
        MODULE_SOURCE
    )

    ast.parse(
        TEST_SOURCE
    )

    required=(
        "bootstrap_one",
        "native_live_route",
        "_build_alt_setup",
        "signed_simulation",
        "send_once",
        "wait_confirmed",
        "_qarb096_alt_state_path",
        "TRADE_BROADCAST=False",
    )

    missing=[
        x for x in required
        if x not in MODULE_SOURCE
    ]

    if missing:
        raise RuntimeError(
            "ALT_BOOTSTRAP_CONTRACT_MISSING:"
            +repr(missing)
        )

    if "q87.c.send(" in MODULE_SOURCE:
        raise RuntimeError(
            "UNEXPECTED_TRADE_SEND_SEAM"
        )

    MOD.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    MOD.write_text(
        MODULE_SOURCE,
        encoding="utf-8",
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    print(
        "[PASS] CANARY-005 one-token ALT bootstrap installed"
    )
    print(
        "[PASS] target token prefix=3Dgwn5E7H5"
    )
    print(
        "[PASS] QARB-096 ALT build/sim/send/confirm/persist seams reused"
    )
    print(
        "[PASS] no trade broadcast path added"
    )
    print(
        "[PASS] canonical scanner/runtime not modified"
    )
    print(
        "[NEXT] python test_canary_005_alt_bootstrap.py"
    )
    print(
        "[NEXT] python -m "
        "qseries_v2.oracle_execution."
        "solana_atomic_executor."
        "bootstrap_canary_005_alts"
    )


if __name__=="__main__":
    main()
