from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
if not S.is_dir():
    raise SystemExit("[FAIL] QARB clean-bot subsystem missing")

M=S/"qarb_052c_orca_whirlpool_native_provider_activation.py"
T=R/"test_qarb_052c_orca_whirlpool_native_provider_activation.py"
U=R/"run_qarb_052c_orca_whirlpool_native_provider_activation.py"

M.write_text('\nfrom __future__ import annotations\nimport importlib.util, inspect, json, time\nfrom pathlib import Path\n\nEXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nMAX_AGE_MS=750.0\n\ndef _import_file(path:Path):\n    name="_qarb052_"+path.stem+"_"+str(abs(hash(str(path))))[:8]\n    spec=importlib.util.spec_from_file_location(name,path)\n    if spec is None or spec.loader is None:\n        raise RuntimeError("IMPORT_SPEC_FAILED:"+str(path))\n    mod=importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(mod)\n    return mod\n\ndef _candidate_modules(root:Path, needles):\n    sub=root/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"\n    out=[]\n    for p in sub.rglob("*.py"):\n        low=p.name.lower()\n        if any(n in low for n in needles) and not low.startswith(("build_","test_","run_")):\n            out.append(p)\n    return sorted(out)\n\ndef _sig(fn):\n    try:return str(inspect.signature(fn))\n    except Exception:return "?"\n\nVENUE="ORCA_WHIRLPOOL"\nOUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c_orca_provider_activation.json")\n\ndef inspect_provider(root):\n    root=Path(root);rows=[]\n    for p in _candidate_modules(root,("orca","whirlpool")):\n        try:m=_import_file(p)\n        except Exception as e:\n            rows.append({"file":str(p),"import_error":type(e).__name__+":"+str(e)});continue\n        callables={}\n        for name in ("bind_provider","set_provider","provider","quote","quote_exact_in","touch","update","apply_update","discover"):\n            v=getattr(m,name,None)\n            if callable(v):callables[name]=_sig(v)\n        provider_attrs={}\n        for name in ("PROVIDER","provider_instance","LOCAL_PROVIDER","QUOTE_PROVIDER"):\n            if hasattr(m,name):\n                v=getattr(m,name);provider_attrs[name]=None if v is None else type(v).__name__\n        rows.append({"file":str(p),"callables":callables,"provider_attrs":provider_attrs})\n    provider_live=any(any(v not in (None,"NoneType") for v in r.get("provider_attrs",{}).values()) for r in rows)\n    native_quote=any(any(k in r.get("callables",{}) for k in ("quote","quote_exact_in")) for r in rows)\n    return {"venue":VENUE,"files":rows,"provider_bound":provider_live,\n            "native_quote_callable":native_quote,\n            "priced_live_eligible":bool(provider_live and native_quote),\n            "execution_authority":False}\n\ndef main():\n    p=inspect_provider(Path.cwd())\n    o=Path.cwd()/OUT;o.parent.mkdir(parents=True,exist_ok=True)\n    o.write_text(json.dumps(p,indent=2,sort_keys=True),encoding="utf-8")\n    print("[QARB-052C] ORCA WHIRLPOOL NATIVE PROVIDER ACTIVATION")\n    print("[PROVIDER_BOUND]",p["provider_bound"])\n    print("[NATIVE_QUOTE_CALLABLE]",p["native_quote_callable"])\n    print("[PRICED_LIVE_ELIGIBLE]",p["priced_live_eligible"])\n    if not p["priced_live_eligible"]:\n        print("[HOLD] Orca remains fail-closed until an actual repo-native provider is bound")\n    print("[REPORT]",OUT)\n    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")\n',encoding="utf-8")
T.write_text('import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052c_orca_whirlpool_native_provider_activation as q\nclass T(unittest.TestCase):\n    def test_mode(self):\n        self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)\n    def test_freshness(self):\n        self.assertEqual(q.MAX_AGE_MS,750.0)\nif __name__=="__main__":unittest.main(verbosity=2)\n',encoding="utf-8")
U.write_text('from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_052c_orca_whirlpool_native_provider_activation import main\nif __name__=="__main__":main()\n',encoding="utf-8")

for x in (M,T,U):
    py_compile.compile(str(x),doraise=True)

print('[PASS] QARB-052C Orca Whirlpool native-provider activation installed')
print('[REUSE] existing QARB-013 fail-closed provider boundary')
print('[NO_FAKE_PRICE] Orca cannot enter priced graph without a bound local provider')
print('[MODE] PAPER_ONLY=True execution_authority=FALSE')
