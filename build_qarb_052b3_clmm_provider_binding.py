from pathlib import Path
import py_compile
R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
for d in (
    S/"native_provider_resolver.py",
    S/"certified_roles.py",
):
    if not d.is_file(): raise SystemExit("[FAIL] dependency missing: "+str(d))
M=S/"qarb_052b3_clmm_provider_binding.py"
T=R/"test_qarb_052b3_clmm_provider_binding.py"
U=R/"run_qarb_052b3_clmm_provider_binding.py"
M.write_text('from __future__ import annotations\nimport inspect,json\nfrom pathlib import Path\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import native_provider_resolver as resolver\n\nEXECUTION_AUTHORITY=False\nPAPER_ONLY=True\n\ndef invoke(fn,root,venue):\n    sig=inspect.signature(fn);kw={}\n    for n,p in sig.parameters.items():\n        low=n.lower()\n        if low in ("root","repo","repo_root","path"): kw[n]=Path(root)\n        elif low in ("venue","family","dex"): kw[n]=venue\n        elif p.default is inspect._empty: raise RuntimeError("UNSUPPORTED_REQUIRED_PARAM:"+n)\n    return fn(**kw)\n\ndef cand_dict(x):\n    if x is None:return None\n    if hasattr(x,"__dict__"): return {k:str(v) for k,v in vars(x).items()}\n    return {"repr":repr(x)}\n\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_clmm_live as live\nVENUE="RAYDIUM_CLMM"\nOUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052b3_clmm_provider_binding.json")\ndef run(root):\n    root=Path(root); scan=None; best=None; errors=[]\n    try: scan=invoke(resolver.scan,root,VENUE)\n    except Exception as e: errors.append("scan:"+type(e).__name__+":"+str(e))\n    try: best=invoke(resolver.best,root,VENUE)\n    except Exception as e: errors.append("best:"+type(e).__name__+":"+str(e))\n    loaded=None\n    try: loaded=live.load_provider()\n    except Exception as e: errors.append("load_provider:"+type(e).__name__+":"+str(e))\n    payload={"venue":VENUE,"scan_count":len(scan) if isinstance(scan,(list,tuple)) else None,\n             "best":cand_dict(best),"load_provider_type":None if loaded is None else type(loaded).__name__,\n             "provider_available":loaded is not None or best is not None,"errors":errors,"execution_authority":False}\n    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2),encoding="utf-8")\n    return payload\ndef main():\n    p=run(Path.cwd())\n    print("[QARB-052B3] RAYDIUM CLMM PROVIDER BINDING")\n    print("[RESOLVER_SCAN_COUNT]",p["scan_count"])\n    print("[RESOLVER_BEST]",p["best"])\n    print("[LOAD_PROVIDER_TYPE]",p["load_provider_type"])\n    print("[PROVIDER_AVAILABLE]",p["provider_available"])\n    if not p["provider_available"]: print("[HOLD] no actual native CLMM provider resolved; remains fail-closed")\n    print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")\n',encoding="utf-8")
T.write_text('import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052b3_clmm_provider_binding as q\nclass T(unittest.TestCase):\n    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)\n    def test_venue(self): self.assertEqual(q.VENUE,"RAYDIUM_CLMM")\nif __name__=="__main__":unittest.main(verbosity=2)\n',encoding="utf-8")
U.write_text('from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_052b3_clmm_provider_binding import main\nif __name__=="__main__":main()\n',encoding="utf-8")
for x in (M,T,U): py_compile.compile(str(x),doraise=True)
print('[PASS] QARB-052B3 Raydium CLMM provider binding installed')
print('[REUSE] native_provider_resolver + raydium_clmm_live.load_provider')
print('[FAIL_CLOSED] no provider means no CLMM pricing')
print('[MODE] PAPER_ONLY=True execution_authority=FALSE')
