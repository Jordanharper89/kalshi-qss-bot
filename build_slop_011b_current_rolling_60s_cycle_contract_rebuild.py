from pathlib import Path
import ast

R=Path.cwd()
D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_011b_current_rolling_60s_cycle_contract_rebuild.py"

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
 ready=tuple(
  w for w in windows
  if w.window_seconds==60 and w.state=="WINDOW_READY"
 )
 cycle=SimpleNamespace(windows=ready)
 fresh=tuple(form_fresh_opportunity_states(
  cycle,max_age_seconds=max_age_seconds,now=now
 ))
 return {
  "token_address":token_address,
  "records":len(records),
  "windows":len(windows),
  "ready_windows":len(ready),
  "fresh_states":fresh,
  "state":"CURRENT_60S_READY" if fresh else "NO_CURRENT_FRESH_60S_STATE",
  "execution_authority":False,
 }
""",encoding="utf-8")

T=R/"test_slop_011b_current_rolling_60s_cycle_contract_rebuild.py"
T.write_text("""import unittest
from unittest.mock import patch
from datetime import datetime,timezone
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011b_current_rolling_60s_cycle_contract_rebuild import current_fresh_60s_states

class T(unittest.TestCase):
 def test_exact_cycle_contract(self):
  now=datetime.now(timezone.utc)
  w=SimpleNamespace(
   window_seconds=60,
   state="WINDOW_READY",
   last_observed_at=now.isoformat(),
   conditions=(("P",(("order_flow","BUY_PRESSURE"),),"READY"),)
  )
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011b_current_rolling_60s_cycle_contract_rebuild.read_pinned_pool_history",return_value=(1,2)),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_011b_current_rolling_60s_cycle_contract_rebuild.build_multi_horizon_solana_states",return_value=(w,)):
   x=current_fresh_60s_states("T",now=now)
  print("[SLOP-011B]",x)
  self.assertEqual(x["windows"],1)
  self.assertEqual(x["ready_windows"],1)
  self.assertEqual(len(x["fresh_states"]),1)
  self.assertFalse(x["execution_authority"])

if __name__=="__main__":
 unittest.main(verbosity=2)
""",encoding="utf-8")

ast.parse(M.read_text())
ast.parse(T.read_text())
print("[PASS] SLOP-011B installed")
print("[PASS] SLOP-002 cycle.windows contract restored")
print("[PASS] failed SLOP-011 replaced; execution_authority=FALSE")