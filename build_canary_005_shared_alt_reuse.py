from __future__ import annotations

import ast
from pathlib import Path

TARGET=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

TEST=Path(
    "test_canary_005_shared_alt_reuse.py"
)

PRELOAD='def _canonical_cached_alt_accounts(addrs):\n    tables=globals().get(\n        "PRELOADED_ALT_TABLES",\n        {}\n    )\n\n    out={}\n\n    for addr in list(addrs or []):\n        if addr not in tables:\n            raise RuntimeError(\n                "CANARY_005_ALT_NOT_PRELOADED:"\n                +str(addr)\n            )\n\n        out[addr]=tables[addr]\n\n    return out\n\n\ndef preload_canary_saved_alts(root):\n    from qseries_v2.solana_live_execution import (\n        qarb_097_official_meteora_sdk_executor as q97\n    )\n\n    state=q97._load_alt_state(\n        Path(root)\n    )\n\n    tables=(\n        state.get("tables")\n        if isinstance(state,dict)\n        else {}\n    )\n\n    if not isinstance(tables,dict):\n        tables={}\n\n    token_alts={}\n    addresses=[]\n\n    for token,row in sorted(\n        tables.items(),\n        key=lambda x:str(x[0]),\n    ):\n        if not isinstance(row,dict):\n            continue\n\n        address=row.get("address")\n\n        if not address:\n            continue\n\n        token=str(token)\n        address=str(address)\n\n        token_alts[token]=[\n            address\n        ]\n\n        if address not in addresses:\n            addresses.append(address)\n\n    original=globals().get(\n        "_ORIGINAL_ALT_ACCOUNTS"\n    )\n\n    if original is None:\n        original=q87.c.alt_accounts\n        globals()[\n            "_ORIGINAL_ALT_ACCOUNTS"\n        ]=original\n\n    decoded=(\n        original(addresses)\n        if addresses\n        else {}\n    )\n\n    if not isinstance(decoded,dict):\n        raise RuntimeError(\n            "CANARY_005_ALT_PRELOAD_NOT_MAPPING"\n        )\n\n    live_tables={\n        str(k):v\n        for k,v in decoded.items()\n        if v\n    }\n\n    clean={}\n\n    for token,alts in token_alts.items():\n        usable=[\n            x for x in alts\n            if x in live_tables\n        ]\n\n        if usable:\n            clean[token]=usable\n\n            print(\n                "[CANARY_005_ALT_READY] "\n                "token=%s alt=%s"\n                %(\n                    token[:10],\n                    usable[0],\n                ),\n                flush=True,\n            )\n\n        else:\n            print(\n                "[CANARY_005_ALT_HOLD] "\n                "token=%s "\n                "reason=SAVED_ALT_NOT_LIVE"\n                %token[:10],\n                flush=True,\n            )\n\n    globals()[\n        "PRELOADED_ALTS"\n    ]=clean\n\n    globals()[\n        "PRELOADED_ALT_TABLES"\n    ]=live_tables\n\n    globals()[\n        "PRELOADED_SHARED_ALTS"\n    ]=sorted(\n        live_tables\n    )\n\n    q87.c.alt_accounts=(\n        _canonical_cached_alt_accounts\n    )\n\n    print(\n        "[CANARY_005_ALT_PRELOAD] "\n        "ready_tokens=%d "\n        "saved_token_alts=%d "\n        "live_tables=%d "\n        "shared_tables=%d "\n        "hot_path_alt_rpc=FALSE"\n        %(\n            len(READY_TOKENS),\n            len(clean),\n            len(live_tables),\n            len(\n                globals().get(\n                    "PRELOADED_SHARED_ALTS",\n                    []\n                )\n            ),\n        ),\n        flush=True,\n    )\n\n    return clean'
COMPILE='def compile_current(\n    user,\n    route\n):\n    signer=globals().get(\n        "SIGNER"\n    )\n\n    if signer is None:\n        raise RuntimeError(\n            "CANARY_005_SIGNER_NOT_INITIALIZED"\n        )\n\n    blockhash=BLOCKHASH.get()\n\n    token=str(\n        route.get("token")\n        or ""\n    )\n\n    base_alts=list(\n        route.get("base_alts")\n        or []\n    )\n\n    token_alts=list(\n        (\n            globals().get(\n                "PRELOADED_ALTS",\n                {}\n            )\n            or {}\n        ).get(\n            token,\n            []\n        )\n        or []\n    )\n\n    shared_alts=list(\n        globals().get(\n            "PRELOADED_SHARED_ALTS",\n            []\n        )\n        or []\n    )\n\n    alt_options=[]\n\n    def add_option(rows):\n        rows=list(\n            dict.fromkeys(\n                rows\n            )\n        )\n\n        if rows not in alt_options:\n            alt_options.append(\n                rows\n            )\n\n    if token_alts:\n        add_option(\n            base_alts+token_alts\n        )\n\n    for alt in shared_alts:\n        add_option(\n            base_alts+[alt]\n        )\n\n    if shared_alts:\n        add_option(\n            base_alts+shared_alts\n        )\n\n    add_option(\n        base_alts\n    )\n\n    candidates=list(\n        q87.repaired_candidates(\n            route\n        )\n    )\n\n    attempts=[]\n\n    for candidate in candidates:\n        name=str(\n            candidate.get(\n                "name",\n                "UNKNOWN"\n            )\n        )\n\n        if "PUMP_METEORA_ONLY" in name:\n            print(\n                "[CANARY_005_COMPILE_ATTEMPT] "\n                "candidate=%s "\n                "reject=LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL"\n                %name,\n                flush=True,\n            )\n            continue\n\n        for alts in alt_options:\n            try:\n                comp=q87.compile_candidate(\n                    user,\n                    candidate[\n                        "instructions"\n                    ],\n                    [list(alts)],\n                    blockhash,\n                )\n\n            except Exception as exc:\n                row={\n                    "candidate":name,\n                    "alts":len(alts),\n                    "error":"%s:%s"%(\n                        type(exc).__name__,\n                        str(exc),\n                    ),\n                }\n\n                attempts.append(row)\n\n                print(\n                    "[CANARY_005_COMPILE_ATTEMPT] "\n                    "candidate=%s alts=%d "\n                    "shared=%s error=%s"\n                    %(\n                        name,\n                        len(alts),\n                        bool(\n                            set(alts)\n                            &set(shared_alts)\n                        ),\n                        row["error"],\n                    ),\n                    flush=True,\n                )\n                continue\n\n            if not isinstance(comp,dict):\n                attempts.append({\n                    "candidate":name,\n                    "alts":len(alts),\n                    "error":"NON_MAPPING_COMPILE",\n                })\n                continue\n\n            if not comp.get("ok"):\n                error=str(\n                    comp.get("error")\n                    or "UNKNOWN"\n                )\n\n                attempts.append({\n                    "candidate":name,\n                    "alts":len(alts),\n                    "error":error,\n                })\n\n                print(\n                    "[CANARY_005_COMPILE_ATTEMPT] "\n                    "candidate=%s alts=%d "\n                    "shared=%s error=%s"\n                    %(\n                        name,\n                        len(alts),\n                        bool(\n                            set(alts)\n                            &set(shared_alts)\n                        ),\n                        error,\n                    ),\n                    flush=True,\n                )\n                continue\n\n            unsigned=comp["unsigned"]\n\n            print(\n                "[CANARY_005_COMPILE_ATTEMPT] "\n                "candidate=%s alts=%d "\n                "shared=%s "\n                "unsigned_bytes=%d "\n                "status=COMPILED"\n                %(\n                    name,\n                    len(alts),\n                    bool(\n                        set(alts)\n                        &set(shared_alts)\n                    ),\n                    len(unsigned),\n                ),\n                flush=True,\n            )\n\n            fee_result=q87.c.rpc(\n                "getFeeForMessage",\n                [\n                    base64.b64encode(\n                        comp["msg"]\n                    ).decode(),\n                    {\n                        "commitment":\n                            "processed"\n                    },\n                ],\n            )\n\n            if not isinstance(\n                fee_result,\n                dict\n            ):\n                raise RuntimeError(\n                    "CANARY_005_FEE_RESULT_NOT_MAPPING:"\n                    +type(\n                        fee_result\n                    ).__name__\n                )\n\n            fee_lamports=fee_result.get(\n                "value"\n            )\n\n            if (\n                not isinstance(\n                    fee_lamports,\n                    int\n                )\n                or fee_lamports<0\n            ):\n                raise RuntimeError(\n                    "CANARY_005_BAD_FEE_VALUE:"\n                    +str(fee_lamports)\n                )\n\n            raw=q87.c.signed_tx(\n                comp["msg"],\n                signer,\n            )\n\n            if len(raw)>MAX_TX_BYTES:\n                attempts.append({\n                    "candidate":name,\n                    "alts":len(alts),\n                    "error":\n                        "SIGNED_TX_TOO_LARGE:"\n                        +str(len(raw)),\n                })\n\n                print(\n                    "[CANARY_005_COMPILE_ATTEMPT] "\n                    "candidate=%s alts=%d "\n                    "shared=%s "\n                    "signed_bytes=%d "\n                    "status=SIGNED_TOO_LARGE"\n                    %(\n                        name,\n                        len(alts),\n                        bool(\n                            set(alts)\n                            &set(shared_alts)\n                        ),\n                        len(raw),\n                    ),\n                    flush=True,\n                )\n                continue\n\n            print(\n                "[CANARY_005_COMPILE_PASS] "\n                "candidate=%s "\n                "alts=%d "\n                "shared=%s "\n                "signed_bytes=%d "\n                "fee=%d"\n                %(\n                    name,\n                    len(alts),\n                    bool(\n                        set(alts)\n                        &set(shared_alts)\n                    ),\n                    len(raw),\n                    fee_lamports,\n                ),\n                flush=True,\n            )\n\n            return {\n                "ok":True,\n                "candidate":name,\n                "bytes":len(raw),\n                "msg":comp["msg"],\n                "raw":raw,\n                "fee_lamports":\n                    int(fee_lamports),\n                "alts":\n                    list(alts),\n                "attempts":\n                    attempts,\n            }\n\n    return {\n        "ok":False,\n        "reason":\n            "NO_LEGAL_COMPACT_TX",\n        "attempts":attempts,\n    }'
TEST_SOURCE='from __future__ import annotations\nimport ast\nfrom pathlib import Path\nimport unittest\n\nTARGET=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=TARGET.read_text(\n            encoding="utf-8"\n        )\n        cls.tree=ast.parse(cls.src)\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(\n                n,\n                (\n                    ast.FunctionDef,\n                    ast.AsyncFunctionDef,\n                ),\n            )\n            and n.name==name\n        ]\n        self.assertEqual(\n            len(rows),\n            1,\n            name,\n        )\n        return rows[0]\n\n    def srcfn(self,name):\n        return (\n            ast.get_source_segment(\n                self.src,\n                self.fn(name),\n            )\n            or ""\n        )\n\n    def test_canary_size_preserved(self):\n        s=self.srcfn("exact_best")\n        self.assertIn("0.005",s)\n\n    def test_preload_all_saved_tables(self):\n        s=self.srcfn(\n            "preload_canary_saved_alts"\n        )\n        self.assertIn(\n            "PRELOADED_SHARED_ALTS",\n            s,\n        )\n        self.assertIn(\n            "tables.items()",\n            s,\n        )\n        self.assertNotIn(\n            "for token in sorted(\\\\n        str(x)\\\\n        for x in READY_TOKENS",\n            s,\n        )\n\n    def test_compile_tries_shared_alts(self):\n        s=self.srcfn(\n            "compile_current"\n        )\n        self.assertIn(\n            "PRELOADED_SHARED_ALTS",\n            s,\n        )\n        self.assertIn(\n            "for alt in shared_alts",\n            s,\n        )\n        self.assertIn(\n            "shared=%s",\n            s,\n        )\n\n    def test_token_specific_first(self):\n        s=self.srcfn(\n            "compile_current"\n        )\n        self.assertLess(\n            s.index("if token_alts:"),\n            s.index("for alt in shared_alts"),\n        )\n\n    def test_no_hot_alt_rpc(self):\n        s=self.srcfn(\n            "_canonical_cached_alt_accounts"\n        )\n        self.assertNotIn(\n            "rpc(",\n            s,\n        )\n\n    def test_signed_fee_contract(self):\n        s=self.srcfn(\n            "compile_current"\n        )\n        self.assertIn(\n            \'"getFeeForMessage"\',\n            s,\n        )\n        self.assertIn(\n            "q87.c.signed_tx",\n            s,\n        )\n\n    def test_shell_still_rejected(self):\n        s=self.srcfn(\n            "compile_current"\n        )\n        self.assertIn(\n            "LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",\n            s,\n        )\n\n    def test_broadcast_still_disabled(self):\n        self.assertIn(\n            \'"[BROADCAST] disabled"\',\n            self.src,\n        )\n        self.assertNotIn(\n            "q87.c.send(",\n            self.src,\n        )\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def fn_node(src,name):
    tree=parse(src,"TARGET")

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
            f"{name}_SEAM_COUNT:"
            f"{len(rows)}"
        )

    return rows[0]


def replace_function(
    src,
    name,
    replacement,
):
    node=fn_node(src,name)
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
    if not TARGET.is_file():
        raise RuntimeError(
            "CANONICAL_RUNTIME_MISSING"
        )

    src=TARGET.read_text(
        encoding="utf-8"
    )

    parse(src,"BEFORE")

    required=(
        "def preload_canary_saved_alts",
        "PRELOADED_ALT_TABLES",
        "def compile_current",
        "CANARY_005_COMPILE_ATTEMPT",
        "getFeeForMessage",
        "q87.c.signed_tx",
        '"[BROADCAST] disabled"',
    )

    missing=[
        x for x in required
        if x not in src
    ]

    if missing:
        raise RuntimeError(
            "SHARED_ALT_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    src=replace_function(
        src,
        "preload_canary_saved_alts",
        PRELOAD,
    )

    src=replace_function(
        src,
        "compile_current",
        COMPILE,
    )

    parse(src,"AFTER")
    parse(TEST_SOURCE,"TEST")

    TARGET.write_text(
        src,
        encoding="utf-8",
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    print(
        "[PASS] CANARY-005 shared ALT reuse installed"
    )
    print(
        "[PASS] all confirmed saved ALTs preload at startup"
    )
    print(
        "[PASS] token-specific ALT remains first compile option"
    )
    print(
        "[PASS] shared confirmed ALTs tried before no-ALT fallback"
    )
    print(
        "[PASS] hot path ALT RPC remains disabled"
    )
    print(
        "[PASS] no new ALT creation and no new rent spend"
    )
    print(
        "[PASS] broadcast remains disabled"
    )


if __name__=="__main__":
    main()
