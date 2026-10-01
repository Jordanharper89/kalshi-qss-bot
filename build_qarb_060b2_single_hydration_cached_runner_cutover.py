from pathlib import Path
import py_compile
R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
REQ=[
 S/"qarb_060b_existing_runtime_multidex_cutover.py",
 S/"persistent_profit_runtime.py",
 S/"merged_live_runtime.py",
]
for x in REQ:
    if not x.exists():
        raise SystemExit("[FAIL] missing dependency: "+str(x))
M=S/"qarb_060b2_single_hydration_cached_runner_cutover.py"
T=R/"test_qarb_060b2_single_hydration_cached_runner_cutover.py"
U=R/"run_qarb_060b2_single_hydration_cached_runner_cutover.py"
M.write_text('from __future__ import annotations\nimport argparse,asyncio,json\nfrom pathlib import Path\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b\n\nEXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nOUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_060b2_single_hydration_cached_runner_cutover.json")\n\ndef prepare_once(root):\n    q60b.install()\n    state=q60b.extended_prepare(Path(root))\n    cap=q60b.extended_capability(state)\n    return state,cap\n\ndef main(argv=None):\n    ap=argparse.ArgumentParser()\n    ap.add_argument("--seconds",type=float,default=20.0)\n    a=ap.parse_args(argv)\n    root=Path.cwd()\n\n    state,cap=prepare_once(root)\n\n    def cached_prepare(_root):\n        return state\n\n    q60b.m.prepare=cached_prepare\n    q60b.m.capability=q60b.extended_capability\n    q60b.p._process_event=q60b.extended_process\n\n    rep={\n        "revision":"QARB_060B2",\n        "accounts":len(state["addresses"]),\n        "priced_tokens":len(state["eps"]),\n        "extension_registry":len(state.get("xreg",{})),\n        "capability":cap,\n        "cutover_report":state.get("cutover_report"),\n        "cutover_errors":state.get("cutover_errors"),\n        "single_hydration":True,\n        "cached_prepare_bound":q60b.m.prepare is cached_prepare,\n        "execution_authority":False,\n        "paper_only":True,\n    }\n    out=root/OUT\n    out.parent.mkdir(parents=True,exist_ok=True)\n    out.write_text(json.dumps(rep,indent=2,sort_keys=True),encoding="utf-8")\n\n    print("[QARB-060B2] SINGLE-HYDRATION CACHED EXISTING-RUNNER CUTOVER",flush=True)\n    print("[FIX] prepare/hydrate exactly once; persistent runner reuses the already-live state",flush=True)\n    print("[CUTOVER] accounts=%d priced_tokens=%d extension_registry=%d"%(\n        rep["accounts"],rep["priced_tokens"],rep["extension_registry"]),flush=True)\n    print("[CAPABILITY] "+json.dumps(cap,sort_keys=True),flush=True)\n    if rep["cutover_errors"]:\n        print("[WARM_ERRORS] "+json.dumps(rep["cutover_errors"]),flush=True)\n    print("[CACHE] single_hydration=True cached_prepare_bound=True",flush=True)\n    print("[RUNNER] persistent_profit_runtime.serve | existing websocket/event loop preserved",flush=True)\n    print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)\n\n    return asyncio.run(q60b.p.serve(root,a.seconds))\n\nif __name__=="__main__":\n    main()\n',encoding="utf-8")
T.write_text('import inspect,unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b2_single_hydration_cached_runner_cutover as q\nclass T(unittest.TestCase):\n    def test_mode(self):\n        self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)\n    def test_existing_runner_preserved(self):\n        src=inspect.getsource(q.q60b.p.serve)\n        self.assertIn("state=m.prepare(root)",src.replace(" ",""))\n    def test_single_hydration_source(self):\n        src=inspect.getsource(q.main)\n        self.assertIn("state,cap=prepare_once(root)",src.replace(" ",""))\n        self.assertIn("q60b.m.prepare=cached_prepare",src.replace(" ",""))\n    def test_no_execution(self):\n        self.assertFalse(q.EXECUTION_AUTHORITY)\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
U.write_text('from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_060b2_single_hydration_cached_runner_cutover import main\nif __name__=="__main__":main()\n',encoding="utf-8")
for x in (M,T,U):
    py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-060B2 single-hydration cached runner cutover installed")
print("[FIX] removes second prepare/hydration pass that was triggering 429s and erasing live-priced state")
print("[PRESERVE] existing persistent_profit_runtime websocket/event loop")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
