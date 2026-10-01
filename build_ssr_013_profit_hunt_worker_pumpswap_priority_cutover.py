from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_013_profit_hunt_worker.py"
TEST=ROOT/"test_ssr_013_profit_hunt_worker_pumpswap_priority_cutover.py"
MOD_TEXT=r"""from __future__ import annotations
import time,traceback
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162k_phase8_pump_fun_pumpswap_targeted_live_capture import write as capture_pumps
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162l_phase8_pump_targeted_freeze_extension import write as freeze_pumps
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_012_pumpswap_money_follower import run as follow_pumpswap
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162n_phase8_learning_net_intersection_checkpoint import write as evaluate_net

PIPE=("CAPTURE_PUMPS","FREEZE_PUMPS","FOLLOW_PUMPSWAP_FIRST","EVALUATE_NET")

def cycle(root,state=None,dry_run=False):
 root=Path(root);state=state or RuntimeState(root)
 if dry_run:return {"dry_run":True,"pipeline":PIPE,"primary_family":"PUMP_SWAP","execution_authority":False}
 state.running(stage="CAPTURE_PUMP_FUN_AND_PUMPSWAP");_,a=capture_pumps(root)
 state.running(stage="FREEZE_PUMP_TARGETS",live_rows=a.get("strict_live_economic_row_count"));_,b=freeze_pumps(root)
 state.running(stage="FOLLOW_PUMPSWAP_FOR_NET_OUTCOME",pumpswap_freezes=b.get("pumpswap_freeze_count"));c=follow_pumpswap(root)
 state.running(stage="EVALUATE_NET_INTERSECTION",pumpswap_cases=c.get("total_pumpswap_case_count"));_,d=evaluate_net(root)
 return {"capture":a,"freeze":b,"pumpswap_follow":c,"evaluation":d,
  "summary":{"prospective_cases":d.get("prospective_oos_case_count"),
   "friction_supported_cases":d.get("friction_supported_case_count"),
   "mean_net_forward_return":d.get("mean_net_forward_return"),
   "net_expectancy_status":d.get("net_expectancy_status"),
   "pumpswap_case_count":c.get("total_pumpswap_case_count")},
  "execution_authority":False,"read_only":True}

def run_forever(root,sleep_seconds=30):
 root=Path(root);state=RuntimeState(root);state.boot();n=0
 while True:
  try:
   r=cycle(root,state);n+=1;state.running(cycle_count=n,stage="IDLE_BETWEEN_MONEY_HUNT_CYCLES",**r["summary"])
  except KeyboardInterrupt:state.stopping();break
  except Exception as e:
   state.error(e);err=root/"runtime_state/solana_opportunities/profitability_runtime/last_error.txt"
   err.parent.mkdir(parents=True,exist_ok=True);err.write_text(traceback.format_exc(),encoding="utf-8")
  time.sleep(sleep_seconds)
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_013_profit_hunt_worker import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cutover(self):
  d=cycle(ROOT,dry_run=True);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["primary_family"],"PUMP_SWAP");self.assertIn("FOLLOW_PUMPSWAP_FIRST",d["pipeline"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-013 PumpSwap-priority profit-hunt worker")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
