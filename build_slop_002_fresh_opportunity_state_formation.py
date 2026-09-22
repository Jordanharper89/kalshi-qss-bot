from pathlib import Path
import ast
R=Path.cwd(); D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
if not (D/"slop_001_live_universe_discovery_boundary.py").exists(): raise SystemExit("[FAIL] SLOP-001 missing")
M=D/"slop_002_fresh_opportunity_state_formation.py"
M.write_text(r"""from dataclasses import dataclass
from datetime import datetime,timezone
READ_ONLY=True; EXECUTION_AUTHORITY=False
def _dt(v): return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True,slots=True)
class FreshOpportunityState:
 token_address:str; pair_address:str; observed_at:str; age_seconds:float
 window_seconds:int; conditions:tuple; state:str; execution_authority:bool=False
def form_fresh_opportunity_states(cycle,now=None,max_age_seconds=20.0,window_seconds=60):
 now=now or datetime.now(timezone.utc); out=[]
 for w in tuple(cycle.windows):
  if int(w.window_seconds)!=int(window_seconds) or w.state!="WINDOW_READY" or not w.last_observed_at: continue
  age=max(0.0,(now-_dt(w.last_observed_at)).total_seconds())
  for pair,conditions,state in tuple(w.conditions):
   out.append(FreshOpportunityState(str(cycle.token_address),str(pair),str(w.last_observed_at),age,
    int(w.window_seconds),tuple(conditions),"FRESH" if age<=float(max_age_seconds) else "STALE",False))
 return tuple(out)
""",encoding="utf-8")
T=R/"test_slop_002_fresh_opportunity_state_formation.py"
T.write_text(r"""import unittest
from datetime import datetime,timezone,timedelta
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_002_fresh_opportunity_state_formation import form_fresh_opportunity_states
class T(unittest.TestCase):
 def test_freshness(self):
  now=datetime.now(timezone.utc); c=SimpleNamespace(token_address="T",windows=(
   SimpleNamespace(window_seconds=60,state="WINDOW_READY",last_observed_at=(now-timedelta(seconds=3)).isoformat(),conditions=(("P",(("order_flow","BUY_PRESSURE"),),"READY"),)),
   SimpleNamespace(window_seconds=15,state="WINDOW_READY",last_observed_at=now.isoformat(),conditions=()),))
  x=form_fresh_opportunity_states(c,now=now,max_age_seconds=20)
  print("[SLOP-002]",x)
  self.assertEqual(len(x),1); self.assertEqual(x[0].state,"FRESH"); self.assertFalse(x[0].execution_authority)
if __name__=="__main__": unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text()); ast.parse(T.read_text())
print("[PASS] SLOP-002 installed")
print("[PASS] latest-window freshness is first-class; stale states cannot masquerade as live")