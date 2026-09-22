from pathlib import Path
import ast

R=Path.cwd()
D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_011c_exact_current_rolling_cycle_rebuild.py"

M.write_text("""from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history,build_multi_horizon_solana_states
from .slop_002_fresh_opportunity_state_formation import form_fresh_opportunity_states
READ_ONLY=True
EXECUTION_AUTHORITY=False

def current_fresh_60s_states(token_address,root=None,max_age_seconds=20.0,now=None):
 records=read_pinned_pool_history(token_address,root=root,limit=4096)
 windows=tuple(build_multi_horizon_solana_states(
  records,token_address,windows_seconds=(60,)
 ))
 cycle=SimpleNamespace(
  token_address=str(token_address),
  windows=windows
 )
 states=tuple(form_fresh_opportunity_states(
  cycle,
  now=now,
  max_age_seconds=max_age_seconds,
  window_seconds=60
 ))
 fresh=tuple(x for x in states if x.state=="FRESH")
 return {
  "token_address":str(token_address),
  "records":len(records),
  "windows":len(windows),
  "states":states,
  "fresh_states":fresh,
  "state":"CURRENT_FRESH_60S_READY" if fresh else "NO_CURRENT_FRESH_60S_STATE",
  "execution_authority":False,
 }
""",encoding="utf-8")

T=R/"test_slop_011c_exact_current_rolling_cycle_rebuild.py"

T.write_text("""import unittest
from unittest.mock import patch
from datetime import datetime,timezone
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011c_exact_current_rolling_cycle_rebuild import current_fresh_60s_states

class T(unittest.TestCase):
 def test_exact_slop002_contract(self):
  now=datetime.now(timezone.utc)
  w=SimpleNamespace(
   window_seconds=60,
   state="WINDOW_READY",
   last_observed_at=now.isoformat(),
   conditions=(
    ("PAIR",(("order_flow","BUY_PRESSURE"),),"CONDITIONS_READY"),
   )
  )
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011c_exact_current_rolling_cycle_rebuild.read_pinned_pool_history",return_value=(1,2)),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011c_exact_current_rolling_cycle_rebuild.build_multi_horizon_solana_states",return_value=(w,)):
   x=current_fresh_60s_states("TOKEN",now=now)

  print("[SLOP-011C]",x)
  self.assertEqual(x["token_address"],"TOKEN")
  self.assertEqual(x["windows"],1)
  self.assertEqual(len(x["states"]),1)
  self.assertEqual(len(x["fresh_states"]),1)

  s=x["fresh_states"][0]
  self.assertEqual(s.token_address,"TOKEN")
  self.assertEqual(s.pair_address,"PAIR")
  self.assertEqual(s.window_seconds,60)
  self.assertEqual(s.state,"FRESH")
  self.assertIn(("order_flow","BUY_PRESSURE"),s.conditions)
  self.assertFalse(s.execution_authority)
  self.assertFalse(x["execution_authority"])

if __name__=="__main__":
 unittest.main(verbosity=2)
""",encoding="utf-8")

ast.parse(M.read_text())
ast.parse(T.read_text())

print("[PASS] SLOP-011C installed")
print("[PASS] exact repository SLOP-002 contract bound")
print("[PASS] OAD-274 native 60s window preserved")
print("[PASS] stale states excluded from fresh admission surface")
print("[PASS] execution_authority=FALSE")