from __future__ import annotations
import asyncio,inspect,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as qf
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_065_proven_profit_runtime_composition as q65
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
_NATIVE_SHADOW=p.SimulationLane
class CertificationLane:
 def __init__(self,root,state):
  self.paper=qf.PaperSimulationLane(root,state);self.shadow=_NATIVE_SHADOW(root,state);self.shadow_submitted=0
 @property
 def attempts(self):return self.paper.attempts
 @property
 def profitable(self):return getattr(self.shadow,"profitable",0)
 @property
 def best(self):return getattr(self.shadow,"best",None)
 @property
 def failures(self):return getattr(self.shadow,"failures",0)
 @property
 def drops(self):return getattr(self.shadow,"drops",0)
 def submit(self,r):
  self.paper.submit(r)
  age=r.get("event_to_decision_ms")
  if age is None or float(age)>750:return
  if r.get("buy_venue")!="PUMPSWAP" or r.get("sell_venue")!="METEORA_DLMM":return
  self.shadow_submitted+=1;self.shadow.submit(r)
 async def worker(self,stop):
  a=asyncio.create_task(self.paper.worker(stop));b=asyncio.create_task(self.shadow.worker(stop));last=time.monotonic()
  try:
   while not stop.is_set():
    if time.monotonic()-last>=p.HEARTBEAT_SECONDS:
     best=getattr(self.shadow,"best",None);bp=None if not best else best.get("sim_pnl_sol")
     print("[EXEC_SHADOW_SCORE] fresh_submitted=%d sim_profitable=%d sim_best=%s sim_failures=%d drops=%d"%(
      self.shadow_submitted,getattr(self.shadow,"profitable",0),str(bp),getattr(self.shadow,"failures",0),getattr(self.shadow,"drops",0)),flush=True);last=time.monotonic()
    try:await asyncio.wait_for(stop.wait(),timeout=.25)
    except asyncio.TimeoutError:pass
  finally:
   a.cancel();b.cancel();await asyncio.gather(a,b,return_exceptions=True)
def install():
 q65.install();p.SimulationLane=CertificationLane;return q65.q61d
def main(argv=None):
 runtime=install()
 print("[QARB-066] PAPER PROFIT + EXECUTION SHADOW CERTIFICATION",flush=True)
 print("[SHADOW] exact existing atomic transaction/simulation lane; fresh live-event signals only",flush=True)
 print("[PAPER] proven 026F outcomes remain active",flush=True)
 print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)
 return runtime.main(argv)
if __name__=="__main__":main()
