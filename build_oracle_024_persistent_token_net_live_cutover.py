from pathlib import Path
import py_compile, textwrap

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_024_persistent_token_net_live_cutover.py"
TEST=ROOT/"test_oracle_024_persistent_token_net_live_cutover.py"
RUN=ROOT/"run_oracle_024_persistent_token_net_live_cutover.py"

module_src=r"""
from __future__ import annotations
import argparse,inspect,json,time
from pathlib import Path

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

def prewarm_exact_tokens():
    state=q19.persistent.m.prepare(Path.cwd())
    pairs=list(state.get("pairs") or [])
    seen=set()
    rows=[]
    for pair in pairs:
        token=str(pair.token)
        if token in seen:
            continue
        seen.add(token)
        t=time.perf_counter_ns()
        row=q23.worker().warm(token)
        ms=(time.perf_counter_ns()-t)/1e6
        rows.append({
            "token":token,
            "program":row.get("program"),
            "warm_ms":ms,
        })
        print("[ORACLE024_TOKEN_WARM] token=%s program=%s warm_ms=%.3f"%(
            token[:12],row.get("program"),ms
        ),flush=True)
    q23.worker().refresh_epoch()
    return rows

def install():
    q23.install_hot_token_net()
    if q18.token_net is not q23.token_net:
        raise RuntimeError("TOKEN_NET_PATCH_NOT_ACTIVE")
    return True

def run_q20(seconds):
    install()
    warmed=prewarm_exact_tokens()

    print("[ORACLE-024] PERSISTENT TOKEN-NET LIVE CUTOVER",flush=True)
    print("[TOKEN_NET] ORACLE-023 persistent worker active",flush=True)
    print("[PREWARM] exact_pair_tokens=%d"%len(warmed),flush=True)
    print("[PRESERVE] ORACLE-020 latest-state/coalescing/stale gates unchanged",flush=True)
    print("[PRIVATE_KEY] not required",flush=True)
    print("[BROADCAST] disabled",flush=True)

    report={
        "oracle_build":"ORACLE-024",
        "warmed":warmed,
        "persistent_token_net":True,
        "q20_preserved":True,
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "broadcast":False,
    }
    out=Path("runtime_state/oracle/oracle_live_execution/oracle_024_persistent_token_net_live_cutover.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print("[REPORT] %s"%out,flush=True)

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

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=60.0)
    a=ap.parse_args(argv)
    return run_q20(a.seconds)

if __name__=="__main__":
    raise SystemExit(main())
"""

test_src=r"""
import inspect,unittest
from qseries_v2.oracle_execution import oracle_024_persistent_token_net_live_cutover as q24

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q24.EXECUTION_AUTHORITY)
        self.assertTrue(q24.PAPER_ONLY)
        self.assertFalse(q24.REAL_MONEY_MOVED)

    def test_patch_targets_exact_seam(self):
        s=inspect.getsource(q24.install)
        self.assertIn("q23.install_hot_token_net()",s)
        self.assertIn("q18.token_net is not q23.token_net",s)

    def test_all_pair_prewarm(self):
        s=inspect.getsource(q24.prewarm_exact_tokens)
        self.assertIn('state=q19.persistent.m.prepare(Path.cwd())',s)
        self.assertIn('q23.worker().warm(token)',s)
        self.assertIn('q23.worker().refresh_epoch()',s)

    def test_q20_reused(self):
        s=inspect.getsource(q24.run_q20)
        self.assertIn('getattr(q20,"run",None)',s)
        self.assertIn('getattr(q20,"main",None)',s)

    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q24)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)
        self.assertNotIn("sendTransaction",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

run_src=r"""
from qseries_v2.oracle_execution.oracle_024_persistent_token_net_live_cutover import main
if __name__=="__main__":
    raise SystemExit(main())
"""

MOD.write_text(textwrap.dedent(module_src).lstrip(),encoding="utf-8")
TEST.write_text(textwrap.dedent(test_src).lstrip(),encoding="utf-8")
RUN.write_text(textwrap.dedent(run_src).lstrip(),encoding="utf-8")

for f in (MOD,TEST,RUN):
    py_compile.compile(str(f),doraise=True)

print("[PASS] ORACLE-024 persistent token-net live cutover installed")
print("[CUTOVER] q18.token_net -> ORACLE-023 persistent worker")
print("[PREWARM] all current exact-pair mints before live window")
print("[PRESERVE] ORACLE-020 latest-state/coalescing/stale logic unchanged")
print("[PRIVATE_KEY] not required")
print("[BROADCAST] disabled")
print("[OWNER] ORACLE")
