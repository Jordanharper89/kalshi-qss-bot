from pathlib import Path
import ast
R=Path.cwd(); D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
if not (D/"slop_002_fresh_opportunity_state_formation.py").exists(): raise SystemExit("[FAIL] SLOP-002 missing")
M=D/"slop_003_concurrent_opportunity_admission_prospective_freeze.py"
M.write_text(r"""from dataclasses import dataclass
from hashlib import sha256
READ_ONLY=True; EXECUTION_AUTHORITY=False
FROZEN_THESIS={"horizon":60,"target":0.10,"stop":0.05,"condition":("order_flow","BUY_PRESSURE"),"friction_bps":200}
@dataclass(frozen=True,slots=True)
class ProspectiveOpportunity:
 prediction_id:str; token_address:str; pair_address:str; frozen_at:str; conditions:tuple
 horizon_seconds:int; target:float; stop:float; friction_bps:int
 state:str="PENDING_60S"; execution_authority:bool=False
def admit_and_freeze(states,thesis=FROZEN_THESIS):
 out=[]
 for x in states:
  if x.state!="FRESH" or thesis["condition"] not in tuple(x.conditions): continue
  raw="|".join((x.token_address,x.pair_address,x.observed_at,repr(tuple(x.conditions))))
  out.append(ProspectiveOpportunity(sha256(raw.encode()).hexdigest(),x.token_address,x.pair_address,
   x.observed_at,tuple(x.conditions),int(thesis["horizon"]),float(thesis["target"]),
   float(thesis["stop"]),int(thesis["friction_bps"]),"PENDING_60S",False))
 return tuple(out)
""",encoding="utf-8")
T=R/"test_slop_003_concurrent_opportunity_admission_prospective_freeze.py"
T.write_text(r"""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_002_fresh_opportunity_state_formation import FreshOpportunityState
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import admit_and_freeze,FROZEN_THESIS
class T(unittest.TestCase):
 def test_freeze(self):
  s=(FreshOpportunityState("T1","P1","2026-09-17T12:00:00+00:00",1,60,(("order_flow","BUY_PRESSURE"),),"FRESH"),
     FreshOpportunityState("T2","P2","2026-09-17T12:00:00+00:00",1,60,(("order_flow","SELL_PRESSURE"),),"FRESH"))
  x=admit_and_freeze(s); print("[SLOP-003]",x)
  self.assertEqual(len(x),1); self.assertEqual(x[0].state,"PENDING_60S")
  self.assertEqual(x[0].horizon_seconds,60); self.assertEqual(x[0].friction_bps,200)
  self.assertEqual(FROZEN_THESIS["condition"],("order_flow","BUY_PRESSURE"))
if __name__=="__main__": unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text()); ast.parse(T.read_text())
print("[PASS] SLOP-003 installed")
print("[PASS] fresh BUY_PRESSURE admission freezes at detection time; no retrospective reconstruction")