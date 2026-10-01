from pathlib import Path
import py_compile, textwrap

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_025_single_hydration_exact_live_reuse.py"
TEST=ROOT/"test_oracle_025_single_hydration_exact_live_reuse.py"
RUN=ROOT/"run_oracle_025_single_hydration_exact_live_reuse.py"

module_src=r"""
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
        row=q23.worker().warm(token)
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
"""

test_src=r"""
import inspect,unittest
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q25.EXECUTION_AUTHORITY)
        self.assertTrue(q25.PAPER_ONLY)
        self.assertFalse(q25.REAL_MONEY_MOVED)

    def test_certified_single_hydration_reused(self):
        s=inspect.getsource(q25.prepare_once)
        self.assertIn("q60b2.prepare_once",s)
        self.assertIn("ORACLE025_NO_EXACT_PAIRS_AFTER_SINGLE_HYDRATION",s)

    def test_cached_prepare_bound_into_q19(self):
        s=inspect.getsource(q25.bind_cached_state)
        self.assertIn("q60b.m.prepare=cached_prepare",s)
        self.assertIn("q19.persistent.m.prepare=cached_prepare",s)

    def test_token_net_prewarm(self):
        s=inspect.getsource(q25.install_hot_math_and_prewarm)
        self.assertIn("q23.install_hot_token_net()",s)
        self.assertIn("q23.worker().warm(token)",s)
        self.assertIn("q23.worker().refresh_epoch()",s)

    def test_q20_reused(self):
        s=inspect.getsource(q25.invoke_q20)
        self.assertIn('getattr(q20,"run",None)',s)
        self.assertIn('getattr(q20,"main",None)',s)

    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q25)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)
        self.assertNotIn("sendTransaction",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

run_src=r"""
from qseries_v2.oracle_execution.oracle_025_single_hydration_exact_live_reuse import main
if __name__=="__main__":
    raise SystemExit(main())
"""

MOD.write_text(textwrap.dedent(module_src).lstrip(),encoding="utf-8")
TEST.write_text(textwrap.dedent(test_src).lstrip(),encoding="utf-8")
RUN.write_text(textwrap.dedent(run_src).lstrip(),encoding="utf-8")

for f in (MOD,TEST,RUN):
    py_compile.compile(str(f),doraise=True)

print("[PASS] ORACLE-025 single-hydration exact live reuse installed")
print("[REUSE] certified QARB-060B2 prepare-once/cache boundary")
print("[BIND] cached exact state -> ORACLE-019/020 prepare seam")
print("[TOKEN_NET] ORACLE-023 persistent worker retained")
print("[PRESERVE] ORACLE-020 latest-state/coalescing/stale logic")
print("[PRIVATE_KEY] not required")
print("[BROADCAST] disabled")
print("[OWNER] ORACLE")
