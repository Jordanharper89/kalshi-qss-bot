from __future__ import annotations
import argparse,asyncio,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_060b2_single_hydration_cached_runner_cutover.json")

def prepare_once(root):
    q60b.install()
    state=q60b.extended_prepare(Path(root))
    cap=q60b.extended_capability(state)
    return state,cap

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=20.0)
    a=ap.parse_args(argv)
    root=Path.cwd()

    state,cap=prepare_once(root)

    def cached_prepare(_root):
        return state

    q60b.m.prepare=cached_prepare
    q60b.m.capability=q60b.extended_capability
    q60b.p._process_event=q60b.extended_process

    rep={
        "revision":"QARB_060B2",
        "accounts":len(state["addresses"]),
        "priced_tokens":len(state["eps"]),
        "extension_registry":len(state.get("xreg",{})),
        "capability":cap,
        "cutover_report":state.get("cutover_report"),
        "cutover_errors":state.get("cutover_errors"),
        "single_hydration":True,
        "cached_prepare_bound":q60b.m.prepare is cached_prepare,
        "execution_authority":False,
        "paper_only":True,
    }
    out=root/OUT
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(rep,indent=2,sort_keys=True),encoding="utf-8")

    print("[QARB-060B2] SINGLE-HYDRATION CACHED EXISTING-RUNNER CUTOVER",flush=True)
    print("[FIX] prepare/hydrate exactly once; persistent runner reuses the already-live state",flush=True)
    print("[CUTOVER] accounts=%d priced_tokens=%d extension_registry=%d"%(
        rep["accounts"],rep["priced_tokens"],rep["extension_registry"]),flush=True)
    print("[CAPABILITY] "+json.dumps(cap,sort_keys=True),flush=True)
    if rep["cutover_errors"]:
        print("[WARM_ERRORS] "+json.dumps(rep["cutover_errors"]),flush=True)
    print("[CACHE] single_hydration=True cached_prepare_bound=True",flush=True)
    print("[RUNNER] persistent_profit_runtime.serve | existing websocket/event loop preserved",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)

    return asyncio.run(q60b.p.serve(root,a.seconds))

if __name__=="__main__":
    main()
