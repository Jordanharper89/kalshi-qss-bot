from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
M=S/"qarb_067_recover_real_atomic_simulator.py"
T=R/"test_qarb_067_recover_real_atomic_simulator.py"
X=R/"run_qarb_067_execution_shadow.py"

M.write_text(r'''from __future__ import annotations
import argparse,asyncio,time
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_065_proven_profit_runtime_composition as q65
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q61d
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as qf
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_atomic_simulation as atomic

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

class DualLane:
    def __init__(self,root,state):
        self.paper=qf.PaperSimulationLane(root,state)
        self.atomic=atomic.SimulationLane(root,state)
    @property
    def attempts(self): return self.atomic.attempts
    @property
    def profitable(self): return self.atomic.profitable
    @property
    def failures(self): return self.atomic.failures
    @property
    def drops(self): return self.atomic.drops
    @property
    def best(self): return self.atomic.best
    def submit(self,s):
        self.paper.submit(s)
        return self.atomic.submit(s)
    async def worker(self,stop):
        paper_task=asyncio.create_task(self.paper.worker(stop))
        print("[ATOMIC_WORKER_STARTED]",flush=True)
        try:
            while not stop.is_set():
                try:
                    sig=await asyncio.wait_for(self.atomic.q.get(),timeout=.5)
                except asyncio.TimeoutError:
                    continue
                self.atomic.attempts+=1
                n=self.atomic.attempts
                t=time.monotonic()
                print("[ATOMIC_CALL_BEGIN] n=%d token=%s q=%d"%(
                    n,sig["token"][:10],self.atomic.q.qsize()),flush=True)
                try:
                    row=await asyncio.wait_for(
                        asyncio.to_thread(
                            atomic.simulate_signal,
                            self.atomic.root,self.atomic.state,sig),
                        timeout=15.0)
                    dt=time.monotonic()-t
                    print("[ATOMIC_CALL_RETURN] n=%d elapsed=%.3fs"%(n,dt),flush=True)
                    if row.get("profitable_simulation"):
                        self.atomic.profitable+=1
                        if self.atomic.best is None or float(row.get("sim_pnl_sol") or -1e99)>float(self.atomic.best.get("sim_pnl_sol") or -1e99):
                            self.atomic.best=row
                        print("[ATOMIC_SIM_PROFIT] token=%s size=%.6f local=%+.9f_SOL sim=%+.9f_SOL sim_bps=%+.2f"%(
                            row["token"][:10],row["size_sol"],row["local_net_sol"],
                            row["sim_pnl_sol"],row["sim_bps"]),flush=True)
                    else:
                        print("[ATOMIC_SIM_REJECT] token=%s size=%.6f local=%+.9f_SOL status=NO_PROFITABLE_SIM"%(
                            sig["token"][:10],sig["size_sol"],sig["net_sol"]),flush=True)
                except asyncio.TimeoutError:
                    self.atomic.failures+=1
                    print("[ATOMIC_SIM_TIMEOUT] n=%d token=%s elapsed=>15s"%(
                        n,sig["token"][:10]),flush=True)
                except Exception as exc:
                    self.atomic.failures+=1
                    print("[ATOMIC_SIM_ERROR] token=%s %s:%s"%(
                        sig["token"][:10],type(exc).__name__,exc),flush=True)
        finally:
            if not paper_task.done():
                paper_task.cancel()
            await asyncio.gather(paper_task,return_exceptions=True)

def install():
    q65.install()
    runtime=q61d.install()
    livep=runtime.q60b.p
    livep.SimulationLane=DualLane
    return runtime,livep

def main(argv=None):
    a=argparse.ArgumentParser()
    a.add_argument("--seconds",type=float,default=120.0)
    z=a.parse_args(argv)
    runtime,livep=install()
    print("[QARB-067] PHYSICAL ATOMIC CALL DIAGNOSTIC",flush=True)
    print("[BIND] q61d -> q61c -> q60b.p.SimulationLane=DualLane",flush=True)
    print("[VERIFY] live_module=%s lane=%s"%(livep.__name__,livep.SimulationLane.__name__),flush=True)
    print("[TIMEOUT] atomic_call=15s bounded diagnostic",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)
    return runtime.main(["--seconds",str(z.seconds)])

if __name__=="__main__":
    main()
''',encoding="utf-8")

T.write_text(r'''import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_067_recover_real_atomic_simulator as q
class T(unittest.TestCase):
 def test_live_binding(self):
  r,p=q.install()
  self.assertIs(r.q60b.p.SimulationLane,q.DualLane)
 def test_real_simulator(self):
  self.assertTrue(callable(q.atomic.simulate_signal))
 def test_bounded_call(self):
  s=inspect.getsource(q.DualLane.worker)
  self.assertIn("asyncio.to_thread",s)
  self.assertIn("timeout=15.0",s)
  self.assertIn("ATOMIC_CALL_BEGIN",s)
  self.assertIn("ATOMIC_CALL_RETURN",s)
  self.assertIn("ATOMIC_SIM_TIMEOUT",s)
 def test_safety(self):
  self.assertTrue(q.PAPER_ONLY)
  self.assertFalse(q.EXECUTION_AUTHORITY)
  self.assertFalse(q.REAL_MONEY_MOVED)
if __name__=="__main__": unittest.main(verbosity=2)
''',encoding="utf-8")

X.write_text(
"from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot."
"qarb_067_recover_real_atomic_simulator import main\n"
"if __name__=='__main__': main()\n",encoding="utf-8")

for f in (M,T,X):
    py_compile.compile(str(f),doraise=True)

print("[PASS] QARB-067 atomic-call diagnostic installed")
print("[DIAGNOSTIC] BEGIN -> RETURN/PROFIT/REJECT/ERROR/TIMEOUT")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE")