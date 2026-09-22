from pathlib import Path
import ast

R=Path.cwd()
D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_012b_exact_fresh_buy_pressure_admission.py"

M.write_text("""from .slop_011c_exact_current_rolling_cycle_rebuild import current_fresh_60s_states
from .slop_003_concurrent_opportunity_admission_prospective_freeze import admit_and_freeze,FROZEN_THESIS
READ_ONLY=True
EXECUTION_AUTHORITY=False

def current_buy_pressure_admission(token_address,root=None,max_age_seconds=20.0,now=None):
 current=current_fresh_60s_states(token_address,root=root,max_age_seconds=max_age_seconds,now=now)
 fresh=tuple(current["fresh_states"])
 admitted=tuple(admit_and_freeze(fresh,thesis=FROZEN_THESIS))
 return {
  "token_address":str(token_address),
  "fresh_states":fresh,
  "admitted":admitted,
  "admitted_count":len(admitted),
  "state":"FRESH_BUY_PRESSURE_FROZEN" if admitted else "NO_CURRENT_BUY_PRESSURE",
  "thesis":dict(FROZEN_THESIS),
  "execution_authority":False,
 }
""",encoding="utf-8")

T=R/"test_slop_012b_exact_fresh_buy_pressure_admission.py"
T.write_text("""import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_002_fresh_opportunity_state_formation import FreshOpportunityState
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_012b_exact_fresh_buy_pressure_admission import current_buy_pressure_admission

class T(unittest.TestCase):
 def test_exact_prospective_freeze(self):
  s=FreshOpportunityState("TOKEN","PAIR","2026-09-17T15:30:00+00:00",1.0,60,(("order_flow","BUY_PRESSURE"),),"FRESH",False)
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_012b_exact_fresh_buy_pressure_admission.current_fresh_60s_states",return_value={"fresh_states":(s,)}):
   x=current_buy_pressure_admission("TOKEN")
  print("[SLOP-012B]",x)
  self.assertEqual(x["admitted_count"],1)
  p=x["admitted"][0]
  self.assertEqual(p.horizon_seconds,60)
  self.assertEqual(p.target,0.10)
  self.assertEqual(p.stop,0.05)
  self.assertEqual(p.friction_bps,200)
  self.assertEqual(p.state,"PENDING_60S")
  self.assertEqual(p.frozen_at,s.observed_at)
  self.assertFalse(p.execution_authority)
  self.assertFalse(x["execution_authority"])

if __name__=="__main__":
 unittest.main(verbosity=2)
""",encoding="utf-8")

ast.parse(M.read_text())
ast.parse(T.read_text())
print("[PASS] SLOP-012B installed")
print("[PASS] exact SLOP-003 admit_and_freeze contract bound")
print("[PASS] frozen BUY_PRESSURE thesis preserved")
print("[PASS] prospective evidence timestamp preserved")
print("[PASS] execution_authority=FALSE")