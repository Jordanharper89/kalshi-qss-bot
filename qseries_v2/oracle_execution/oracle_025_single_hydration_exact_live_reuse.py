from __future__ import annotations
import argparse,inspect,json,time
from pathlib import Path

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b2_single_hydration_cached_runner_cutover as q60b2

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

def prepare_once(root):
    state,cap=q60b2.prepare_once(Path(root))
    pairs=list(state.get("pairs") or [])
    if not pairs:
        raise RuntimeError("ORACLE025_NO_EXACT_PAIRS_AFTER_SINGLE_HYDRATION")
    return state,cap

def bind_cached_state(state):
    q60b=q60b2.q60b
    def cached_prepare(_root):
        return state

    q60b.m.prepare=cached_prepare
    try:
        q60b.p.m.prepare=cached_prepare
    except Exception:
        pass

    q19.persistent.m.prepare=cached_prepare
    try:
        q20.q19.persistent.m.prepare=cached_prepare
    except Exception:
        pass

    return cached_prepare

def install_hot_math_and_prewarm(state):
    q23.install_hot_token_net()
    if q18.token_net is not q23.token_net:
        raise RuntimeError("ORACLE025_TOKEN_NET_PATCH_NOT_ACTIVE")

    seen=set()
    rows=[]
    for pair in list(state.get("pairs") or []):
        token=str(pair.token)
        if token in seen:
            continue
        seen.add(token)
        t=time.perf_counter_ns()
        row=None
        last=None
        for attempt in range(1,7):
            try:
                row=q23.worker().warm(token)
                break
            except Exception as exc:
                last=exc
                text=str(exc).lower()
                transient=("429" in text or "too many requests" in text or
                           "fetch failed" in text or "timeout" in text)
                if not transient:
                    raise
                print("[ORACLE025_TOKEN_WARM_RETRY] token=%s attempt=%d reason=%s"%(
                    token[:12],attempt,str(exc)[:180]),flush=True)
                if attempt<6:
                    time.sleep(min(12.0,1.5*(2**(attempt-1))))
        if row is None:
            print("[ORACLE025_TOKEN_WARM_SKIP] token=%s reason=%s"%(
                token[:12],str(last)[:180]),flush=True)
            continue
        ms=(time.perf_counter_ns()-t)/1e6
        rows.append({"token":token,"program":row.get("program"),"warm_ms":ms})
        print("[ORACLE025_TOKEN_WARM] token=%s program=%s warm_ms=%.3f"%(
            token[:12],row.get("program"),ms
        ),flush=True)
    q23.worker().refresh_epoch()
    return rows

def invoke_q20(seconds):
    fn=getattr(q20,"run",None)
    if callable(fn):
        sig=inspect.signature(fn)
        if "seconds" in sig.parameters:
            return fn(seconds=float(seconds))
        if len(sig.parameters)==1:
            return fn(float(seconds))
        if len(sig.parameters)==0:
            return fn()

    main=getattr(q20,"main",None)
    if callable(main):
        try:
            return main(["--seconds",str(float(seconds))])
        except TypeError:
            return main()

    raise RuntimeError("ORACLE020_ENTRYPOINT_NOT_FOUND")

def run(seconds=60.0):
    root=Path.cwd()
    state,cap=prepare_once(root)
    cached_prepare=bind_cached_state(state)
    warmed=install_hot_math_and_prewarm(state)
    from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle146_native_template_preparation as o146
    o146.start(state,warmed)

    q60b=q60b2.q60b
    pair_count=len(state.get("pairs") or [])
    priced_tokens=len(state.get("eps") or {})
    accounts=len(state.get("addresses") or [])

    print("[ORACLE-025] SINGLE-HYDRATION EXACT LIVE REUSE",flush=True)
    print("[CACHE] exact_pairs=%d priced_tokens=%d accounts=%d"%(
        pair_count,priced_tokens,accounts
    ),flush=True)
    print("[BIND] q60b.m.prepare cached=%s"%(
        q60b.m.prepare is cached_prepare
    ),flush=True)
    print("[BIND] q19.persistent.m.prepare cached=%s"%(
        q19.persistent.m.prepare is cached_prepare
    ),flush=True)
    print("[TOKEN_NET] ORACLE-023 persistent worker active",flush=True)
    print("[PRESERVE] ORACLE-020 latest-state/coalescing/stale logic",flush=True)
    print("[PRIVATE_KEY] not required",flush=True)
    print("[BROADCAST] disabled",flush=True)

    report={
        "oracle_build":"ORACLE-025",
        "single_hydration":True,
        "cached_prepare_bound":True,
        "exact_pairs":pair_count,
        "priced_tokens":priced_tokens,
        "accounts":accounts,
        "capability":cap,
        "warmed":warmed,
        "persistent_token_net":True,
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "broadcast":False,
    }
    out=Path("runtime_state/oracle/oracle_live_execution/oracle_025_single_hydration_exact_live_reuse.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True,default=str),encoding="utf-8")
    print("[REPORT] %s"%out,flush=True)

    return invoke_q20(seconds)

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=60.0)
    a=ap.parse_args(argv)
    return run(a.seconds)

if __name__=="__main__":
    raise SystemExit(main())
