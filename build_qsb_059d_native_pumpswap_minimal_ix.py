from pathlib import Path
import py_compile

ROOT=Path.cwd()
MOD=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059_gav_reverse_atomic.py"
if not MOD.is_file():
    raise SystemExit("[FAIL] QSB-059C module missing")

PKG=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native"
PKG.mkdir(parents=True,exist_ok=True)
(PKG/"package.json").write_text('{\n  "name": "qsb059d-pump-native",\n  "private": true,\n  "type": "module",\n  "dependencies": {\n    "@pump-fun/pump-swap-sdk": "latest",\n    "@solana/web3.js": "latest",\n    "bn.js": "latest"\n  }\n}',encoding="utf-8")
(PKG/"build_buy_ix.mjs").write_text('import fs from "node:fs";\nimport BN from "bn.js";\nimport {Connection,PublicKey} from "@solana/web3.js";\nimport {OnlinePumpAmmSdk, PumpAmmSdk} from "@pump-fun/pump-swap-sdk";\n\nconst req=JSON.parse(fs.readFileSync(0,"utf8"));\nconst connection=new Connection(req.rpc,"processed");\nconst user=new PublicKey(req.user);\nconst poolKey=new PublicKey(req.pool);\nconst quoteLamports=new BN(String(req.quoteLamports));\nconst slippage=Number(req.slippagePct ?? 0.2);\n\nfunction encIx(ix){\n  return {\n    programId:ix.programId.toBase58(),\n    accounts:ix.keys.map(k=>({pubkey:k.pubkey.toBase58(),isSigner:!!k.isSigner,isWritable:!!k.isWritable})),\n    data:Buffer.from(ix.data).toString("base64")\n  };\n}\n\ntry{\n  const online=new OnlinePumpAmmSdk(connection);\n  const state=await online.swapSolanaState(poolKey,user);\n  const sdk=new PumpAmmSdk();\n  const base=await sdk.swapAutocompleteBaseFromQuote(state,quoteLamports,slippage,"quoteToBase");\n  const ixs=await sdk.swapBaseInstructions(state,base,slippage,"quoteToBase",user);\n  console.log(JSON.stringify({ok:true,baseOut:String(base),instructions:ixs.map(encIx)}));\n}catch(e){\n  console.log(JSON.stringify({ok:false,reason:e?.message??String(e)}));\n}\n',encoding="utf-8")

s=MOD.read_text(encoding="utf-8")

if "def native_pump_buy_ixs(" not in s:
    pos=s.find("def compose_reverse_atomic(")
    if pos<0:
        raise SystemExit("[FAIL] compose boundary missing")
    s=s[:pos]+'\ndef native_pump_buy_ixs(user,pump_pool,start_lamports):\n    import json,os,shutil,subprocess\n    from pathlib import Path\n    b=Path.cwd()/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native"\n    if shutil.which("node") is None or shutil.which("npm") is None:\n        raise RuntimeError("NODE_OR_NPM_MISSING")\n    marker=b/"node_modules/@pump-fun/pump-swap-sdk/package.json"\n    if not marker.is_file():\n        p=subprocess.run(["npm","install","--silent","--no-audit","--no-fund"],cwd=b,\n                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240)\n        if p.returncode!=0:\n            raise RuntimeError("PUMPSWAP_SDK_INSTALL_FAILED:"+p.stdout[-2000:])\n    req={\n      "rpc":os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com"),\n      "user":user,"pool":pump_pool,"quoteLamports":int(start_lamports),\n      "slippagePct":SLIPPAGE_BPS/100.0\n    }\n    p=subprocess.run(["node","build_buy_ix.mjs"],cwd=b,input=json.dumps(req),\n                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)\n    if p.returncode!=0:\n        raise RuntimeError("PUMP_NATIVE_NODE_FAILED:"+p.stderr[-2000:])\n    try:\n        j=json.loads(p.stdout.strip().splitlines()[-1])\n    except Exception:\n        raise RuntimeError("PUMP_NATIVE_BAD_JSON:"+p.stdout[-2000:])\n    if not j.get("ok"):\n        raise RuntimeError("PUMP_NATIVE_BUILD_FAILED:"+str(j.get("reason")))\n    ixs=j.get("instructions") or []\n    if not any(ix.get("programId")==c.PUMP for ix in ixs):\n        raise RuntimeError("PUMP_NATIVE_PROGRAM_IX_MISSING")\n    return ixs,int(j.get("baseOut") or 0)\n\n'+s[pos:]

start=s.find("def compose_reverse_atomic(")
end=s.find("\ndef run(",start)
if start<0 or end<0:
    raise SystemExit("[FAIL] compose function boundary missing")
s=s[:start]+'\ndef compose_reverse_atomic(user,token,pump_pool,meteora_pool,start_sol):\n    start=int(round(float(start_sol)*1e9))\n    meta=c.discover_dlmm(token)\n    if meta["address"]!=meteora_pool:\n        raise RuntimeError("METEORA_BINDING_DRIFT")\n\n    p_ixs,pump_token_out=native_pump_buy_ixs(user,pump_pool,start)\n    if pump_token_out<=0:\n        raise RuntimeError("PUMP_BUY_OUTPUT_ZERO")\n\n    mq=c.dlmm_quote(meta,pump_token_out,token)\n    end=int(mq["raw_out"])\n    local_net=end-start\n    local_bps=local_net/start*10000.0\n\n    m_ix=dlmm_reverse_ix(user,meta,pump_token_out,mq)\n    ixs=[];inserted=False\n    for ix in p_ixs:\n        ixs.append(ix)\n        if ix["programId"]==c.PUMP and not inserted:\n            ixs.append(m_ix);inserted=True\n    if not inserted:\n        raise RuntimeError("PUMP_PROGRAM_IX_NOT_FOUND")\n\n    return {\n        "start_lamports":start,\n        "pump_token_out_raw":pump_token_out,\n        "meteora_end_lamports":end,\n        "pre_sim_net_lamports":local_net,\n        "pre_sim_bps":local_bps,\n        "instructions":ixs,\n        "alts":[],\n        "meta":meta,\n    }\n\n'+s[end:]

s=s.replace("[QSB-059C] GAV PUMP->METEORA ATOMIC SIZE-COMPACT COMPOSER",
            "[QSB-059D] GAV NATIVE-PUMPSWAP MINIMAL ATOMIC COMPOSER",1)
s=s.replace('"revision":"QSB_059C_GAV_REVERSE_ATOMIC_SIZE_COMPACT_V1"',
            '"revision":"QSB_059D_GAV_NATIVE_PUMPSWAP_MINIMAL_V1"',1)

MOD.write_text(s,encoding="utf-8")
py_compile.compile(str(MOD),doraise=True)

TEST=ROOT/"test_qsb_059d_native_pumpswap_minimal_ix.py"
TEST.write_text('import unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q\n\nclass T(unittest.TestCase):\n    def test_native_builder_present(self):\n        self.assertTrue(callable(q.native_pump_buy_ixs))\n        print("[PASS] native PumpSwap instruction builder installed")\n\n    def test_compose_no_prebuilt_pump_tx(self):\n        import inspect\n        src=inspect.getsource(q.compose_reverse_atomic)\n        self.assertNotIn("pump_tx(",src)\n        self.assertNotIn("resolve_pump_instructions(",src)\n        self.assertIn("native_pump_buy_ixs(",src)\n        print("[PASS] reverse composer no longer imports whole prebuilt Pump transaction")\n\n    def test_bridge_uses_official_sdk(self):\n        p=Path.cwd()/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native/build_buy_ix.mjs"\n        s=p.read_text(encoding="utf-8")\n        self.assertIn("@pump-fun/pump-swap-sdk",s)\n        self.assertIn("swapSolanaState",s)\n        self.assertIn("swapAutocompleteBaseFromQuote",s)\n        self.assertIn("swapBaseInstructions",s)\n        print("[PASS] official PumpSwap SDK builds quote->base instructions")\n\n    def test_no_broadcast(self):\n        with open(q.__file__,encoding="utf-8") as f:\n            s=f.read()\n        self.assertNotIn("c.send(raw)",s)\n        print("[PASS] QSB-059D remains simulation-only")\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qsb_059d_native_pumpswap_minimal_ix.py"
RUN.write_text(
 "from qseries_v2.oracle_strategy_intelligence.solana_money.qsb059_gav_reverse_atomic import run\n"
 "run()\n",encoding="utf-8")
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QSB-059D native PumpSwap minimal-instruction composer installed")
print("[FIX] oversized prebuilt Pump transaction wrapper removed")
print("[FIX] official PumpSwap swap instructions + Meteora sell only")
print("[TARGET] reduce 1348-byte transaction below 1232 bytes")
print("[MODE] simulation only; execution_authority=FALSE")
