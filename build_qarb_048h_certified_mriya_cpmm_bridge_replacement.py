from pathlib import Path
import py_compile,shutil

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
D=S/"dex"
MERGED=S/"merged_live_runtime.py"
BASE=D/"raydium_cpmm_live.py"
CAP=S/"qarb_030_mriya_dex_instruction_account_capture.py"

for p in (MERGED,BASE,CAP):
    if not p.is_file():
        raise SystemExit("[FAIL] dependency missing: "+str(p))

BRIDGE=D/"raydium_cpmm_mriya_bridge.py"
TEST=R/"test_qarb_048h_certified_mriya_cpmm_bridge_replacement.py"
CERT=S/"qarb_048h_cpmm_bridge_certification.py"
RUN=R/"run_qarb_048h_certified_mriya_cpmm_bridge_replacement.py"

BRIDGE.write_text('from __future__ import annotations\nimport json\nfrom pathlib import Path\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_live as base\n\nEXECUTION_AUTHORITY=False\nREAD_ONLY=True\nCPMM_PROGRAM="CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"\nMRIYA_CAPTURE=Path("runtime_state/qseries/qarb_clean_bot/mriya_dex_instruction_accounts.json")\n\n# Certified Raydium CPMM SWAP_BASE_INPUT layout reused from upstream decoder:\n# 3 pool, 4 user source, 5 user destination, 6/7 pool vaults, 10/11 pool mints.\nPOOL_I=3\nVAULT_A_I=6\nVAULT_B_I=7\nMINT_A_I=10\nMINT_B_I=11\n\nLivePool=base.LivePool\nPoolState=base.PoolState\nhydrate=base.hydrate\nupdate=base.update\nquote=base.quote\ntoken_amount=base.token_amount\n\ndef _walk(x):\n    if isinstance(x,dict):\n        yield x\n        for v in x.values():\n            yield from _walk(v)\n    elif isinstance(x,list):\n        for v in x:\n            yield from _walk(v)\n\ndef _pk(x):\n    if isinstance(x,str): return x\n    if isinstance(x,dict):\n        return x.get("pubkey") or x.get("address") or x.get("key")\n    return None\n\ndef _from_mriya_capture(root):\n    p=Path(root)/MRIYA_CAPTURE\n    if not p.is_file():\n        return []\n    try:\n        obj=json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return []\n    found={}\n    for r in _walk(obj):\n        venue=str(r.get("venue") or r.get("family") or "").upper()\n        pid=str(r.get("program_id") or "")\n        if venue!="RAYDIUM_CPMM" and pid!=CPMM_PROGRAM:\n            continue\n        acc=[_pk(x) for x in (r.get("accounts") or [])]\n        if len(acc)<=MINT_B_I:\n            continue\n        pool,va,vb,ma,mb=acc[POOL_I],acc[VAULT_A_I],acc[VAULT_B_I],acc[MINT_A_I],acc[MINT_B_I]\n        if not all((pool,va,vb,ma,mb)):\n            continue\n        if len({pool,va,vb,ma,mb})<5:\n            continue\n        found[pool]=LivePool(pool,ma,mb,va,vb,25,10000)\n    return list(found.values())\n\ndef discover(root):\n    # Preserve the already-certified QARB-011 path first.\n    found={x.pool:x for x in base.discover(root)}\n    # Add exact current Mriya CPMM instruction identities from QARB-030.\n    for x in _from_mriya_capture(root):\n        found[x.pool]=x\n    return list(found.values())\n\ndef evidence(root):\n    rows=discover(root)\n    return {\n      "descriptors":len(rows),\n      "wsol_pairs":sum(base.c.WSOL in (x.token_a,x.token_b) for x in rows) if hasattr(base,"c") else None,\n      "pools":[{"pool":x.pool,"token_a":x.token_a,"token_b":x.token_b,\n                "vault_a":x.vault_a,"vault_b":x.vault_b} for x in rows],\n      "execution_authority":False\n    }\n',encoding="utf-8")
TEST.write_text('import tempfile,json,unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_mriya_bridge as q\n\nclass T(unittest.TestCase):\n    def test_exact_mriya_layout(self):\n        with tempfile.TemporaryDirectory() as td:\n            root=Path(td);p=root/q.MRIYA_CAPTURE;p.parent.mkdir(parents=True)\n            acc=["AUTH","CONFIG","OBS","POOL","US","UD","VA","VB","TPA","TPB","MA","MB","OBS2"]\n            p.write_text(json.dumps({"rows":[{"venue":"RAYDIUM_CPMM","program_id":q.CPMM_PROGRAM,"accounts":acc}]}))\n            rows=q._from_mriya_capture(root)\n            self.assertEqual(len(rows),1)\n            self.assertEqual((rows[0].pool,rows[0].vault_a,rows[0].vault_b),("POOL","VA","VB"))\n            self.assertEqual((rows[0].token_a,rows[0].token_b),("MA","MB"))\n    def test_short_layout_fails_closed(self):\n        with tempfile.TemporaryDirectory() as td:\n            root=Path(td);p=root/q.MRIYA_CAPTURE;p.parent.mkdir(parents=True)\n            p.write_text(json.dumps({"venue":"RAYDIUM_CPMM","accounts":["x"]}))\n            self.assertEqual(q._from_mriya_capture(root),[])\n    def test_reuses_base_live_math(self):\n        self.assertIs(q.hydrate,q.base.hydrate)\n        self.assertIs(q.update,q.base.update)\n        self.assertIs(q.quote,q.base.quote)\n    def test_no_execution(self):\n        self.assertTrue(q.READ_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)\n\nif __name__=="__main__":unittest.main(verbosity=2)\n',encoding="utf-8")
CERT.write_text('from __future__ import annotations\nimport json,subprocess,sys\nfrom pathlib import Path\n\ndef main():\n    root=Path.cwd()\n    capture=root/"run_qarb_030_mriya_dex_instruction_account_capture.py"\n    if capture.is_file():\n        print("[REFRESH] running certified QARB-030 Mriya exact instruction capture",flush=True)\n        rc=subprocess.call([sys.executable,str(capture)])\n        if rc!=0:\n            raise SystemExit("[FAIL] QARB-030 refresh failed rc=%d"%rc)\n\n    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m\n    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_mriya_bridge as b\n\n    desc=b.discover(root)\n    print("[CPMM_DESCRIPTOR_COUNT]",len(desc))\n    for x in desc[:20]:\n        print("[CPMM_DESCRIPTOR] pool=%s token_a=%s token_b=%s vault_a=%s vault_b=%s"%(\n            x.pool[:12],x.token_a[:12],x.token_b[:12],x.vault_a[:12],x.vault_b[:12]))\n\n    state=m.prepare(root)\n    cap=m.capability(state)\n    cpmm_eps=[]\n    for token,eps in state.get("eps",{}).items():\n        for ep in eps:\n            if getattr(ep,"venue",None)=="RAYDIUM_CPMM":\n                cpmm_eps.append((token,ep))\n    print("[CAPABILITY]",json.dumps(cap,sort_keys=True))\n    print("[CPMM_HYDRATED_STATES]",len(state.get("cstates",[])))\n    print("[CPMM_ENDPOINT_COUNT]",len(cpmm_eps))\n    for token,ep in cpmm_eps:\n        print("[CPMM_ENDPOINT] token=%s pool=%s"%(token[:12],ep.pool[:12]))\n    print("[ADDRESSES]",len(state.get("addresses",[])))\n    print("[MODE] READ_ONLY=True execution_authority=FALSE")\n    if not desc:\n        raise SystemExit("[HOLD] no exact Mriya CPMM descriptors")\n    if not state.get("cstates"):\n        raise SystemExit("[HOLD] descriptors found but no CPMM state hydrated")\n    if not cpmm_eps:\n        raise SystemExit("[HOLD] CPMM hydrated but no WSOL-priced CPMM endpoint; next boundary is multi-base route graph")\n    print("[PASS] RAYDIUM_CPMM physically entered merged live pricing graph")\n\nif __name__=="__main__":main()\n',encoding="utf-8")
RUN.write_text('from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_048h_cpmm_bridge_certification import main\nif __name__=="__main__":main()\n',encoding="utf-8")

src=MERGED.read_text(encoding="utf-8")
if "raydium_cpmm_mriya_bridge" not in src:
    if "raydium_cpmm_live" not in src:
        raise SystemExit("[FAIL] merged runtime CPMM import not found")
    backup=MERGED.with_suffix(".py.qarb048h_backup")
    if not backup.exists():
        shutil.copy2(MERGED,backup)
    src=src.replace("raydium_cpmm_live","raydium_cpmm_mriya_bridge",1)
    MERGED.write_text(src,encoding="utf-8")
    print("[PASS] merged runtime CPMM import cut over to certified Mriya bridge")
else:
    print("[PASS] merged runtime already uses certified Mriya bridge")

for p in (BRIDGE,TEST,CERT,RUN,MERGED):
    py_compile.compile(str(p),doraise=True)

print("[PASS] QARB-048H certified Mriya CPMM bridge replacement installed")
print("[REUSE] QARB-011 hydrate/update/local quote preserved")
print("[REUSE] QARB-030 exact current Mriya CPMM instruction accounts feed discovery")
print("[NO_GUESS] official certified CPMM account roles 3/6/7/10/11 reused")
print("[MODE] READ_ONLY=True execution_authority=FALSE")
