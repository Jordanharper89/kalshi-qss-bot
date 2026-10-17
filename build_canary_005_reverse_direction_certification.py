from __future__ import annotations

import ast
from pathlib import Path

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

JS=Path(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native/"
    "build_sell_ix.mjs"
)

TEST=Path(
    "test_canary_005_reverse_certification.py"
)

SELL_JS='import fs from "node:fs";\nimport BN from "bn.js";\nimport {Connection,PublicKey} from "@solana/web3.js";\nimport {OnlinePumpAmmSdk,PUMP_AMM_SDK} from "@pump-fun/pump-swap-sdk";\n\nconst req=JSON.parse(fs.readFileSync(0,"utf8"));\nconst connection=new Connection(req.rpc,"processed");\nconst user=new PublicKey(req.user);\nconst pool=new PublicKey(req.pool);\nconst amount=new BN(String(req.baseAmount));\nconst slippage=Number(req.slippagePct ?? 0.2);\n\nfunction encIx(ix){\n  return {\n    programId:ix.programId.toBase58(),\n    accounts:ix.keys.map(k=>({\n      pubkey:k.pubkey.toBase58(),\n      isSigner:!!k.isSigner,\n      isWritable:!!k.isWritable\n    })),\n    data:Buffer.from(ix.data).toString("base64")\n  };\n}\n\ntry{\n  const online=new OnlinePumpAmmSdk(connection);\n  const state=await online.swapSolanaState(pool,user);\n  const ixs=await PUMP_AMM_SDK.sellBaseInput(state,amount,slippage);\n\n  if(!Array.isArray(ixs)||ixs.length===0){\n    throw new Error("PUMP_SELL_INSTRUCTIONS_EMPTY");\n  }\n\n  const pumpIxs=ixs.filter(ix=>ix.programId.toBase58()===req.pumpProgram);\n\n  if(pumpIxs.length!==1){\n    throw new Error("PUMP_SELL_IX_COUNT:"+pumpIxs.length);\n  }\n\n  const raw=Buffer.from(pumpIxs[0].data);\n\n  if(raw.length<24){\n    throw new Error("PUMP_SELL_DATA_TOO_SHORT:"+raw.length);\n  }\n\n  console.log(JSON.stringify({\n    ok:true,\n    baseIn:raw.readBigUInt64LE(8).toString(),\n    minQuoteOut:raw.readBigUInt64LE(16).toString(),\n    instructions:ixs.map(encIx)\n  }));\n}catch(e){\n  console.log(JSON.stringify({\n    ok:false,\n    reason:e?.stack ?? e?.message ?? String(e)\n  }));\n}\n'
REVERSE_CODE='SELL_TEMPLATES={}\n\n\ndef _pump_sell_template_live(user,pump_pool,base_amount):\n    import json\n    import os\n    import shutil\n    import subprocess\n\n    node=shutil.which("node")\n\n    if node is None:\n        raise RuntimeError("REVERSE_PUMP_SELL_NODE_MISSING")\n\n    helper=(\n        Path.cwd()\n        /"qseries_v2/oracle_strategy_intelligence/"\n        "solana_money/qsb059d_pump_native/"\n        "build_sell_ix.mjs"\n    )\n\n    if not helper.is_file():\n        raise RuntimeError("REVERSE_PUMP_SELL_HELPER_MISSING")\n\n    req={\n        "rpc":os.getenv(\n            "SOLANA_RPC_URL",\n            "https://api.mainnet-beta.solana.com",\n        ),\n        "user":str(user),\n        "pool":str(pump_pool),\n        "baseAmount":int(base_amount),\n        "slippagePct":0.20,\n        "pumpProgram":q87.c.PUMP,\n    }\n\n    p=subprocess.run(\n        [node,helper.name],\n        cwd=str(helper.parent),\n        input=json.dumps(req),\n        stdout=subprocess.PIPE,\n        stderr=subprocess.PIPE,\n        text=True,\n        timeout=45,\n    )\n\n    if p.returncode!=0:\n        raise RuntimeError(\n            "REVERSE_PUMP_SELL_NODE_FAILED:"\n            +p.stderr[-1200:]\n        )\n\n    try:\n        row=json.loads(p.stdout.strip().splitlines()[-1])\n    except Exception as exc:\n        raise RuntimeError(\n            "REVERSE_PUMP_SELL_BAD_JSON:"\n            +p.stdout[-1200:]\n        ) from exc\n\n    if not row.get("ok"):\n        raise RuntimeError(\n            "REVERSE_PUMP_SELL_BUILD_FAILED:"\n            +str(row.get("reason"))\n        )\n\n    ixs=list(row.get("instructions") or [])\n    pos=pump_ix_position(ixs)\n\n    return {\n        "pump_pool":str(pump_pool),\n        "instructions":ixs,\n        "pump_index":int(pos),\n    }\n\n\ndef prebuild_sell_templates(state,user):\n    SELL_TEMPLATES.clear()\n\n    for pair in list(state.get("pairs") or []):\n        token=str(pair.token)\n\n        if token not in READY_TOKENS:\n            continue\n\n        try:\n            snap=immutable_snapshot(pair)\n\n            rows=q18.exact_snapshot_opportunities(\n                snap,\n                0.005,\n            )\n\n            reverse=next(\n                x for x in rows\n                if x.get("direction")=="METEORA_TO_PUMP"\n            )\n\n            amount=int(reverse["net_token"])\n\n            if amount<=0:\n                raise RuntimeError("REVERSE_TEMPLATE_AMOUNT_ZERO")\n\n            SELL_TEMPLATES[token]=_pump_sell_template_live(\n                user,\n                pair.pump_pool,\n                amount,\n            )\n\n            print(\n                "[REVERSE_005_SELL_TEMPLATE_READY] "\n                "token=%s pump=%s"\n                %(token[:10],str(pair.pump_pool)[:12]),\n                flush=True,\n            )\n\n        except Exception as exc:\n            print(\n                "[REVERSE_005_SELL_TEMPLATE_HOLD] "\n                "token=%s %s:%s"\n                %(token[:10],type(exc).__name__,str(exc)[:220]),\n                flush=True,\n            )\n\n    return len(SELL_TEMPLATES)\n\n\ndef rewrite_pump_sell_bounds(ix,base_in,min_quote_out):\n    out=copy.deepcopy(ix)\n\n    raw=bytearray(\n        base64.b64decode(out.get("data") or "")\n    )\n\n    if len(raw)<24:\n        raise RuntimeError(\n            "REVERSE_PUMP_SELL_DATA_TOO_SHORT:"+str(len(raw))\n        )\n\n    raw[8:16]=struct.pack("<Q",int(base_in))\n    raw[16:24]=struct.pack("<Q",int(min_quote_out))\n\n    out["data"]=base64.b64encode(bytes(raw)).decode()\n\n    return out\n\n\ndef build_meteora_buy_ix_hot(token,input_lamports,quote_result):\n    template=METEORA_TEMPLATES.get(str(token))\n\n    if template is None:\n        raise RuntimeError(\n            "REVERSE_METEORA_TEMPLATE_MISSING:"+str(token)\n        )\n\n    swap_for_y=bool(quote_result.get("swap_for_y"))\n\n    if swap_for_y==bool(template["swap_for_y"]):\n        raise RuntimeError("REVERSE_DLMM_DIRECTION_NOT_OPPOSITE")\n\n    arrays=list(template["arrays"])\n    crossed=max(1,int(quote_result.get("bins_crossed") or 1))\n    n=min(len(arrays),max(1,(crossed+69)//70))\n\n    chosen=(\n        arrays[:n]\n        if swap_for_y\n        else list(reversed(arrays))[:n]\n    )\n\n    accounts=[tuple(x) for x in template["fixed_accounts"]]\n\n    if len(accounts)<6:\n        raise RuntimeError("REVERSE_METEORA_FIXED_ACCOUNTS_SHORT")\n\n    accounts[4],accounts[5]=accounts[5],accounts[4]\n\n    accounts.extend(\n        (address,False,True)\n        for _,address in chosen\n    )\n\n    min_out=(\n        int(quote_result["raw_out"])\n        *(10000-q87.las.q59.SLIPPAGE_BPS)\n        //10000\n    )\n\n    data=(\n        bytes([248,198,158,145,225,117,135,200])\n        +struct.pack("<QQ",int(input_lamports),int(min_out))\n    )\n\n    return {\n        "programId":q87.c.DLMM,\n        "accounts":[\n            {\n                "pubkey":p,\n                "isSigner":s,\n                "isWritable":w,\n            }\n            for p,s,w in accounts\n        ],\n        "data":base64.b64encode(data).decode(),\n    }\n\n\ndef _reverse_instruction_sets(sell_ixs,pump_index,meteora_ix):\n    pre=list(sell_ixs[:pump_index])\n    pump=sell_ixs[pump_index]\n    post=list(sell_ixs[pump_index+1:])\n\n    full=pre+[meteora_ix,pump]+post\n\n    compact=[\n        x for x in pre\n        if (\n            x.get("programId") not in q87.las.q59.MEMO_PROGRAMS\n            and x.get("programId")!=q87.las.q59.COMPUTE_BUDGET\n        )\n    ]\n\n    compact += [meteora_ix,pump]\n\n    compact += [\n        x for x in post\n        if (\n            x.get("programId") not in q87.las.q59.MEMO_PROGRAMS\n            and x.get("programId")!=q87.las.q59.COMPUTE_BUDGET\n        )\n    ]\n\n    return [\n        ("REVERSE_FULL",full),\n        ("REVERSE_NO_COMPUTE_MEMO",compact),\n    ]\n\n\ndef same_snapshot_reverse_route(user,snap,opportunity):\n    token=str(snap["token"])\n    template=SELL_TEMPLATES.get(token)\n\n    if template is None:\n        raise RuntimeError(\n            "REVERSE_SELL_TEMPLATE_MISSING:"+token\n        )\n\n    if template["pump_pool"]!=snap["pump_pool"]:\n        raise RuntimeError("REVERSE_PUMP_TEMPLATE_BINDING_DRIFT")\n\n    start=int(opportunity["start"])\n    base_in=int(opportunity["net_token"])\n    min_quote=int(opportunity["local_min_end"])\n\n    if start!=5_000_000 or base_in<=0 or min_quote<=0:\n        raise RuntimeError("REVERSE_005_BAD_EXECUTION_BOUND")\n\n    sell_ixs=[\n        copy.deepcopy(x)\n        for x in template["instructions"]\n    ]\n\n    pump_index=int(template["pump_index"])\n\n    sell_ixs[pump_index]=rewrite_pump_sell_bounds(\n        sell_ixs[pump_index],\n        base_in,\n        min_quote,\n    )\n\n    pump_ix=sell_ixs[pump_index]\n\n    if not any(\n        a.get("pubkey")==snap["pump_pool"]\n        for a in (pump_ix.get("accounts") or [])\n    ):\n        raise RuntimeError("REVERSE_PUMP_POOL_ACCOUNT_DRIFT")\n\n    meteora_ix=build_meteora_buy_ix_hot(\n        token,\n        start,\n        dict(opportunity["mq"]),\n    )\n\n    return {\n        "token":token,\n        "direction":"METEORA_TO_PUMP",\n        "start_lamports":start,\n        "pre_sim_net_lamports":int(opportunity["local_net"]),\n        "pre_sim_min_net_lamports":int(opportunity["local_min_net"]),\n        "pre_sim_bps":float(opportunity["local_bps"]),\n        "pump_ixs":sell_ixs,\n        "pump_index":pump_index,\n        "pump_ix":pump_ix,\n        "meteora_ix":meteora_ix,\n        "base_alts":[],\n        "original_candidates":_reverse_instruction_sets(\n            sell_ixs,\n            pump_index,\n            meteora_ix,\n        ),\n    }\n\n\ndef attack_reverse(\n    lane,\n    token,\n    snap,\n    opportunity,\n    slot,\n    received_ns,\n    generation,\n):\n    if lane.newer_waiting(token,generation):\n        return\n\n    if token not in SELL_TEMPLATES:\n        print(\n            "[REVERSE_005_HOLD] token=%s reason=NO_SELL_TEMPLATE"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    try:\n        result=_execute_route_once(USER,snap,opportunity)\n    except Exception as exc:\n        print(\n            "[REVERSE_005_REJECT] token=%s phase=build error=%s:%s"\n            %(token[:10],type(exc).__name__,str(exc)[:220]),\n            flush=True,\n        )\n        return\n\n    if not result.get("ok"):\n        print(\n            "[REVERSE_005_REJECT] token=%s phase=compile reason=%s"\n            %(\n                token[:10],\n                result.get("compiled",{}).get("reason","UNKNOWN"),\n            ),\n            flush=True,\n        )\n        return\n\n    compiled=result["compiled"]\n    fee=int(compiled.get("fee_lamports") or 0)\n    min_net=int(opportunity["local_min_net"])\n    after_fee_min=min_net-fee\n\n    print(\n        "[REVERSE_005_FEE] token=%s fee=%d quote_net=%+d "\n        "min_net=%+d after_fee_min=%+d"\n        %(\n            token[:10],\n            fee,\n            int(opportunity["local_net"]),\n            min_net,\n            after_fee_min,\n        ),\n        flush=True,\n    )\n\n    if after_fee_min<=0:\n        print(\n            "[REVERSE_005_HOLD] token=%s reason=AFTER_FEE_MIN_NONPOSITIVE"\n            %token[:10],\n            flush=True,\n        )\n        return\n\n    sim=result["sim"]\n\n    if sim.get("err") is not None:\n        print(\n            "[REVERSE_005_SIM_REJECT] token=%s err=%s"\n            %(token[:10],str(sim.get("err"))),\n            flush=True,\n        )\n        _canonical_sim_logs(sim)\n        return\n\n    total_ms=(time.perf_counter_ns()-received_ns)/1e6\n\n    print(\n        "[REVERSE_005_CERTIFIED] token=%s slot=%s size=0.005 "\n        "quote_bps=%+.2f after_fee_min=%+d candidate=%s "\n        "bytes=%d units=%s event_to_sim_ms=%.3f broadcast=FALSE"\n        %(\n            token[:10],\n            slot,\n            float(opportunity["local_bps"]),\n            after_fee_min,\n            compiled["candidate"],\n            compiled["bytes"],\n            str(sim.get("units")),\n            total_ms,\n        ),\n        flush=True,\n    )'
TEST_SOURCE='from __future__ import annotations\nimport ast\nfrom pathlib import Path\nimport unittest\n\nRT=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor/runtime.py"\n)\n\nJS=Path(\n    "qseries_v2/oracle_strategy_intelligence/"\n    "solana_money/qsb059d_pump_native/"\n    "build_sell_ix.mjs"\n)\n\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.src=RT.read_text(encoding="utf-8")\n        cls.tree=ast.parse(cls.src)\n\n    def fn(self,name):\n        rows=[\n            n for n in self.tree.body\n            if isinstance(\n                n,\n                (ast.FunctionDef,ast.AsyncFunctionDef),\n            )\n            and n.name==name\n        ]\n        self.assertEqual(len(rows),1,name)\n        return ast.get_source_segment(self.src,rows[0]) or ""\n\n    def test_sell_helper_exists(self):\n        self.assertTrue(JS.is_file())\n        s=JS.read_text(encoding="utf-8")\n        self.assertIn("sellBaseInput",s)\n        self.assertIn("instructions:ixs.map(encIx)",s)\n\n    def test_reverse_is_exact_005(self):\n        s=self.fn("same_snapshot_reverse_route")\n        self.assertIn("5_000_000",s)\n        self.assertIn(\'"METEORA_TO_PUMP"\',s)\n\n    def test_reverse_order(self):\n        s=self.fn("_reverse_instruction_sets")\n        self.assertIn("[meteora_ix,pump]",s)\n\n    def test_reverse_min_bound(self):\n        s=self.fn("same_snapshot_reverse_route")\n        self.assertIn(\'"local_min_end"\',s)\n        self.assertIn("rewrite_pump_sell_bounds",s)\n\n    def test_reverse_fee_gate(self):\n        s=self.fn("attack_reverse")\n        self.assertIn("after_fee_min",s)\n        self.assertIn("AFTER_FEE_MIN_NONPOSITIVE",s)\n\n    def test_reverse_signed_sim_path(self):\n        s=self.fn("attack_reverse")\n        self.assertIn("_execute_route_once",s)\n        self.assertIn("REVERSE_005_CERTIFIED",s)\n\n    def test_forward_attack_preserved(self):\n        s=self.fn("attack")\n        self.assertIn("pump_6040_actual_base_out",s)\n\n    def test_no_broadcast(self):\n        self.assertIn(\'"[BROADCAST] disabled"\',self.src)\n        self.assertNotIn("q87.c.send(",self.src)\n\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'
DIRECTION_GATE='    if opportunity.get(\n        "direction"\n    )!="PUMP_TO_METEORA":\n\n        raise RuntimeError(\n            "DIRECTION_NOT_CERTIFIED:"\n            +str(\n                opportunity.get(\n                    "direction"\n                )\n            )\n        )\n'
DIRECTION_REPLACEMENT='    direction=opportunity.get(\n        "direction"\n    )\n\n    if direction=="METEORA_TO_PUMP":\n        return same_snapshot_reverse_route(\n            user,\n            snap,\n            opportunity,\n        )\n\n    if direction!="PUMP_TO_METEORA":\n        raise RuntimeError(\n            "DIRECTION_NOT_CERTIFIED:"\n            +str(direction)\n        )\n'
REVERSE_HOLD='    if best[\n        "direction"\n    ]!="PUMP_TO_METEORA":\n\n        print(\n            "[CANONICAL_POSITIVE_HOLD] "\n            "token=%s dir=%s"\n            %(\n                token[:10],\n                best[\n                    "direction"\n                ],\n            ),\n            flush=True,\n        )\n\n        return\n'
REVERSE_ROUTE='    if best[\n        "direction"\n    ]=="METEORA_TO_PUMP":\n\n        attack_reverse(\n            self,\n            token,\n            snap,\n            best,\n            slot,\n            received_ns,\n            generation,\n        )\n\n        return\n\n    if best[\n        "direction"\n    ]!="PUMP_TO_METEORA":\n\n        print(\n            "[CANONICAL_POSITIVE_HOLD] "\n            "token=%s dir=%s"\n            %(\n                token[:10],\n                best["direction"],\n            ),\n            flush=True,\n        )\n\n        return\n'
RUN_SEAM='    meteora_template_count=(\n        prebuild_meteora_templates(\n            state,\n            USER,\n            token_warm\n        )\n    )\n'
RUN_INJECT='    meteora_template_count=(\n        prebuild_meteora_templates(\n            state,\n            USER,\n            token_warm\n        )\n    )\n\n    reverse_sell_template_count=(\n        prebuild_sell_templates(\n            state,\n            USER,\n        )\n    )\n\n    print(\n        "[REVERSE_005_PRELOAD] "\n        "sell_templates=%d broadcast=FALSE"\n        %reverse_sell_template_count,\n        flush=True,\n    )\n'


def parse(src,label):
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise RuntimeError(
            f"{label}_SYNTAX_ERROR:{exc}"
        ) from exc


def function_rows(src,name):
    tree=parse(src,"TARGET")
    return [
        n for n in tree.body
        if isinstance(
            n,
            (ast.FunctionDef,ast.AsyncFunctionDef),
        )
        and n.name==name
    ]


def fn_source(src,name):
    rows=function_rows(src,name)

    if len(rows)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(rows)}"
        )

    return ast.get_source_segment(src,rows[0]) or ""


def replace_function(src,name,new_src):
    rows=function_rows(src,name)

    if len(rows)!=1:
        raise RuntimeError(
            f"{name}_SEAM_COUNT:{len(rows)}"
        )

    node=rows[0]
    lines=src.splitlines(keepends=True)

    start=sum(len(x) for x in lines[:node.lineno-1])
    end=sum(len(x) for x in lines[:node.end_lineno])

    return src[:start]+new_src.rstrip()+"\n\n"+src[end:]


def remove_existing_reverse_block(src):
    marker="SELL_TEMPLATES={}"

    if marker not in src:
        return src

    start=src.index(marker)
    stop=src.index(
        "\ndef same_snapshot_route",
        start,
    )

    return src[:start]+src[stop+1:]


def main():
    if not RT.is_file():
        raise RuntimeError("CANONICAL_RUNTIME_MISSING")

    src=RT.read_text(encoding="utf-8")
    parse(src,"BEFORE")

    required=(
        "def same_snapshot_route",
        "def canonical_price",
        "def run(",
        "PRELOADED_SHARED_ALTS",
        "getFeeForMessage",
        '"[BROADCAST] disabled"',
    )

    missing=[x for x in required if x not in src]

    if missing:
        raise RuntimeError(
            "REVERSE_CERT_EXPECTED_SEAM_MISSING:"
            +repr(missing)
        )

    src=remove_existing_reverse_block(src)

    insert_at=src.index("\ndef same_snapshot_route")

    src=(
        src[:insert_at]
        +"\n\n"
        +REVERSE_CODE
        +"\n\n"
        +src[insert_at:]
    )

    route_src=fn_source(src,"same_snapshot_route")

    if DIRECTION_GATE not in route_src:
        raise RuntimeError("DIRECTION_GATE_SEAM_NOT_FOUND")

    route_src=route_src.replace(
        DIRECTION_GATE,
        DIRECTION_REPLACEMENT,
        1,
    )

    src=replace_function(
        src,
        "same_snapshot_route",
        route_src,
    )

    cp=fn_source(src,"canonical_price")

    if REVERSE_HOLD not in cp:
        raise RuntimeError("CANONICAL_REVERSE_HOLD_SEAM_NOT_FOUND")

    cp=cp.replace(
        REVERSE_HOLD,
        REVERSE_ROUTE,
        1,
    )

    src=replace_function(
        src,
        "canonical_price",
        cp,
    )

    run_src=fn_source(src,"run")

    if RUN_SEAM not in run_src:
        raise RuntimeError("REVERSE_PREBUILD_RUN_SEAM_NOT_FOUND")

    run_src=run_src.replace(
        RUN_SEAM,
        RUN_INJECT,
        1,
    )

    src=replace_function(
        src,
        "run",
        run_src,
    )

    parse(src,"AFTER")
    parse(TEST_SOURCE,"TEST")

    if "q87.c.send(" in src:
        raise RuntimeError("REVERSE_CERT_BROADCAST_FORBIDDEN")

    RT.write_text(src,encoding="utf-8")
    JS.write_text(SELL_JS,encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")

    print("[PASS] CANARY-005 reverse certification installed")
    print("[PASS] Meteora->Pump exact 0.005 route enabled for certification")
    print("[PASS] Pump sell template uses official PumpSwap sellBaseInput")
    print("[PASS] shared ALT / real fee / signed simulation path reused")
    print("[PASS] forward Pump->Meteora attack path preserved")
    print("[PASS] broadcast remains disabled; real_money_moved=FALSE")


if __name__=="__main__":
    main()
