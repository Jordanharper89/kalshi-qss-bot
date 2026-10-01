from pathlib import Path
import py_compile, textwrap

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_028_exact_immutable_atomic_shadow_handoff.py"
TEST=ROOT/"test_oracle_028_exact_immutable_atomic_shadow_handoff.py"
RUN=ROOT/"run_oracle_028_exact_immutable_atomic_shadow_handoff.py"

module_src=r"""
from __future__ import annotations
import argparse,json,queue,threading,time
from pathlib import Path

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_execution import oracle_027_immutable_snapshot_generation_guard as q27
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as atomic

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

class AtomicShadow:
    def __init__(self):
        self.q=queue.Queue(maxsize=32)
        self.stop=False
        self.thread=threading.Thread(target=self._loop,name="oracle028-atomic-shadow",daemon=True)
        self.attempts=0
        self.composed=0
        self.compiled=0
        self.simulated=0
        self.profitable=0
        self.rejected=0
        self.rows=[]
        self.thread.start()

    def submit(self,best):
        if best.get("direction")!="PUMP_TO_METEORA":
            return
        row=dict(best)
        try:
            self.q.put_nowait(row)
        except queue.Full:
            try:self.q.get_nowait()
            except queue.Empty:pass
            self.q.put_nowait(row)

    def _loop(self):
        while not self.stop or not self.q.empty():
            try:
                best=self.q.get(timeout=.2)
            except queue.Empty:
                continue
            self.attempts+=1
            token=str(best["token"])
            pump=str(best["pump_pool"])
            meteora=str(best["meteora"]["address"])
            size=float(best["size_sol"])
            try:
                kp,user=atomic.c.sim_identity()
                route=atomic.compose_reverse_candidates(user,token,pump,meteora,size)
                self.composed+=1
                bh=atomic.c.rpc("getLatestBlockhash",[{"commitment":"processed"}])["value"]["blockhash"]
                winner,rows=atomic.attempt_candidate_simulations(user,kp,route,bh)
                compiled=sum(1 for x in rows if x.get("compiled"))
                self.compiled+=compiled
                self.simulated+=compiled
                if winner:
                    self.profitable+=1
                else:
                    self.rejected+=1
                out={
                    "token":token,"pump_pool":pump,"meteora_pool":meteora,
                    "direction":"PUMP_TO_METEORA","size_sol":size,
                    "exact_local_net":int(best["local_net"]),
                    "exact_local_bps":float(best["local_bps"]),
                    "attempts":rows,"winner":winner,
                }
                self.rows.append(out)
                print("[ORACLE028_ATOMIC_SHADOW] token=%s size=%.3f exact_bps=%+.2f compiled=%d profitable=%s"%(
                    token[:10],size,float(best["local_bps"]),compiled,bool(winner)
                ),flush=True)
            except Exception as exc:
                self.rejected+=1
                self.rows.append({
                    "token":token,"pump_pool":pump,"meteora_pool":meteora,
                    "direction":"PUMP_TO_METEORA","size_sol":size,
                    "exact_local_net":int(best["local_net"]),
                    "exact_local_bps":float(best["local_bps"]),
                    "error":"%s:%s"%(type(exc).__name__,str(exc)[:500]),
                })
                print("[ORACLE028_ATOMIC_REJECT] token=%s size=%.3f reason=%s:%s"%(
                    token[:10],size,type(exc).__name__,str(exc)[:220]
                ),flush=True)

    def close(self):
        self.stop=True
        self.thread.join(timeout=30)

class ShadowLane(q27.ImmutableLatestStateLane):
    def __init__(self,shadow):
        super().__init__()
        self.shadow=shadow

    def _price(self,token,row):
        before_positive=self.positive
        super()._price(token,row)
        if self.positive<=before_positive:
            return
        best=self.best
        if not best or int(best.get("local_net",0))<=0:
            return
        # Only hand off the positive result if no newer event arrived after q27's end guard.
        generation=row[3]
        if self.superseded(token,generation):
            return
        self.shadow.submit(best)

def install(shadow):
    q23.install_hot_token_net()
    q20._pair_snapshot=q27.patched_pair_snapshot
    q20.LatestStateLane=lambda: ShadowLane(shadow)
    return True

def run(seconds=60.0):
    root=Path.cwd()
    state,cap=q25.prepare_once(root)
    q25.bind_cached_state(state)
    q25.install_hot_math_and_prewarm(state)
    shadow=AtomicShadow()
    install(shadow)

    print("[ORACLE-028] EXACT IMMUTABLE -> REAL ATOMIC SHADOW",flush=True)
    print("[SOURCE] qsb059_gav_reverse_atomic.compose_reverse_candidates",flush=True)
    print("[SIM] qsb059_gav_reverse_atomic.attempt_candidate_simulations",flush=True)
    print("[CANDIDATES] FULL -> NO_COMPUTE_MEMO -> WRAP_SWAP_CLOSE -> PUMP_METEORA_ONLY",flush=True)
    print("[INPUT] ORACLE-027 immutable positive PUMP_TO_METEORA only",flush=True)
    print("[LEGACY_HOT_SIGNAL_AUTHORITY] disabled",flush=True)
    print("[PRIVATE_KEY] optional simulation identity only",flush=True)
    print("[BROADCAST] disabled",flush=True)

    try:
        rc=q20.run(float(seconds))
    finally:
        shadow.close()

    payload={
        "oracle_build":"ORACLE-028",
        "shadow_attempts":shadow.attempts,
        "composed":shadow.composed,
        "compiled_candidates":shadow.compiled,
        "simulated_candidates":shadow.simulated,
        "profitable_simulations":shadow.profitable,
        "rejected":shadow.rejected,
        "rows":shadow.rows[-50:],
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "broadcast":False,
    }
    out=Path("runtime_state/oracle/oracle_live_execution/oracle_028_exact_immutable_atomic_shadow_handoff.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str),encoding="utf-8")
    print("[ORACLE028_COMPLETE] attempts=%d composed=%d compiled=%d simulated=%d profitable=%d rejected=%d"%(
        shadow.attempts,shadow.composed,shadow.compiled,shadow.simulated,shadow.profitable,shadow.rejected
    ),flush=True)
    print("[REPORT] %s"%out,flush=True)
    print("[BROADCAST] disabled",flush=True)
    return rc

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
from qseries_v2.oracle_execution import oracle_028_exact_immutable_atomic_shadow_handoff as q28

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q28.EXECUTION_AUTHORITY)
        self.assertTrue(q28.PAPER_ONLY)
        self.assertFalse(q28.REAL_MONEY_MOVED)

    def test_exact_atomic_api(self):
        s=inspect.getsource(q28.AtomicShadow._loop)
        self.assertIn("atomic.compose_reverse_candidates",s)
        self.assertIn("atomic.attempt_candidate_simulations",s)

    def test_only_exact_positive_handoff(self):
        s=inspect.getsource(q28.ShadowLane._price)
        self.assertIn("super()._price(token,row)",s)
        self.assertIn("self.positive<=before_positive",s)
        self.assertIn("self.superseded(token,generation)",s)

    def test_candidate_direction_gate(self):
        s=inspect.getsource(q28.AtomicShadow.submit)
        self.assertIn('PUMP_TO_METEORA',s)

    def test_no_send(self):
        s=inspect.getsource(q28)
        self.assertNotIn("sendTransaction",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

run_src=r"""
from qseries_v2.oracle_execution.oracle_028_exact_immutable_atomic_shadow_handoff import main
if __name__=="__main__":
    raise SystemExit(main())
"""

MOD.write_text(textwrap.dedent(module_src).lstrip(),encoding="utf-8")
TEST.write_text(textwrap.dedent(test_src).lstrip(),encoding="utf-8")
RUN.write_text(textwrap.dedent(run_src).lstrip(),encoding="utf-8")

for f in (MOD,TEST,RUN):
    py_compile.compile(str(f),doraise=True)

print("[PASS] ORACLE-028 exact immutable atomic shadow handoff installed")
print("[SOURCE] existing qsb059_gav_reverse_atomic real atomic composer/simulator")
print("[INPUT] only ORACLE-027 immutable positive PUMP_TO_METEORA results")
print("[LEGACY_HOT_SIGNAL_AUTHORITY] disabled")
print("[BROADCAST] disabled")
print("[OWNER] ORACLE")
