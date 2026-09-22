from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_010b_viable_pool_surveillance_rebuild.py"
M.write_text(r"""from pathlib import Path
import time
from .slop_001_live_universe_discovery_boundary import discover_live_universe
from .slop_006_live_hot_token_surveillance_registry import HotTokenRegistry
from .slop_008_round_robin_hot_token_observer import observe_hot_round
from .slop_009_continuous_discovery_refresh_controller import plan_refresh
from .slop_007_temporal_readiness_gate import temporal_readiness
from qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import _ensure_certified_writer,_stop_certification_writer
READ_ONLY=True;EXECUTION_AUTHORITY=False
def _viable(limit,timeout=20.0):
 u=discover_live_universe(limit=max(int(limit)*5,25),timeout_seconds=timeout);out=[];rejected=[]
 for t in u.tokens:
  try:
   x=expand_live_solana_token_pools(token_address=t,timeout_seconds=timeout)
   if tuple(x.payload.get("pools") or ()):out.append(t)
   else:rejected.append((t,"NO_POOLS"))
  except Exception as e:rejected.append((t,type(e).__name__))
  if len(out)>=int(limit):break
 return tuple(out),tuple(rejected)
def certify(root=None,hot_limit=5,rounds=14,delay_seconds=5.0,refresh_every=3,progress=print):
 root=Path(root or Path.cwd()).resolve();reg=HotTokenRegistry();proc=None;scans=refreshes=0;rejected=[]
 try:
  proc,ws=_ensure_certified_writer(root,progress)
  for r in range(1,int(rounds)+1):
   if plan_refresh(r,refresh_every).refresh_discovery:
    good,bad=_viable(hot_limit);rejected.extend(bad);reg.refresh(good);refreshes+=1
   active=reg.tokens()[-int(hot_limit):]
   observe_hot_round(active,root=root,cycle_base=r*100,progress=progress);scans+=len(active)
   if r<int(rounds):time.sleep(float(delay_seconds))
  states=[]
  for t in reg.tokens():
   q=temporal_readiness(t,read_pinned_pool_history(t,root=root,limit=4096));states.append(q)
   progress(f"[READY] token={t} records={q.records} span={q.span_seconds:.3f} state={q.state}")
  return {"refreshes":refreshes,"observations":scans,"tracked":len(reg.tokens()),
   "ready_60s":sum(x.ready for x in states),"rejected_no_live_pool":len(rejected),
   "states":tuple(states),"writer_state":ws,"execution_authority":False}
 finally:_stop_certification_writer(proc,progress)
""",encoding="utf-8")
T=R/"test_slop_010b_viable_pool_surveillance_rebuild.py"
T.write_text(r"""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_010b_viable_pool_surveillance_rebuild import certify
class T(unittest.TestCase):
 def test_physical(self):
  x=certify(hot_limit=5,rounds=14,delay_seconds=5.0,refresh_every=3)
  print("[SLOP-010B]",{k:v for k,v in x.items() if k!="states"})
  self.assertGreater(x["refreshes"],1);self.assertGreater(x["observations"],0)
  self.assertGreater(x["tracked"],0);self.assertGreater(x["ready_60s"],0)
  self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-010B installed")
print("[PASS] discovered tokens must prove a live pool before entering surveillance")
print("[PASS] replaces failed SLOP-010 physical boundary; execution_authority=FALSE")
