from __future__ import annotations
import time,traceback
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162k_phase8_pump_fun_pumpswap_targeted_live_capture import write as capture_pumps
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162l_phase8_pump_targeted_freeze_extension import write as freeze_pumps
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162m_phase8_all14_multi_cohort_oos_follower import write as follow_oos
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162n_phase8_learning_net_intersection_checkpoint import write as evaluate_net
PIPE=("USLS_162K_CAPTURE","USLS_162L_FREEZE","USLS_162M_FOLLOW","USLS_162N_EVALUATE")
def cycle(root,state=None,dry_run=False):
 root=Path(root);state=state or RuntimeState(root)
 if dry_run:return {"dry_run":True,"pipeline":PIPE,"execution_authority":False}
 state.running(stage="CAPTURE_PUMP_FUN_AND_PUMPSWAP");_,a=capture_pumps(root)
 state.running(stage="FREEZE_LIVE_SETUPS",live_rows=a.get("strict_live_economic_row_count"));_,b=freeze_pumps(root)
 state.running(stage="FOLLOW_ALL14_PROSPECTIVE_OUTCOMES",freeze_count=b.get("freeze_count"));_,c=follow_oos(root)
 state.running(stage="EVALUATE_PROSPECTIVE_NET_EDGE",prospective_cases=c.get("case_count"));_,d=evaluate_net(root)
 s={"prospective_cases":d.get("prospective_oos_case_count"),"family_case_counts":d.get("family_case_counts"),
    "friction_supported_cases":d.get("friction_supported_case_count"),"mean_net_forward_return":d.get("mean_net_forward_return"),
    "net_expectancy_status":d.get("net_expectancy_status"),"learned_group_count":d.get("learned_group_count")}
 return {"capture":a,"freeze":b,"outcomes":c,"evaluation":d,"summary":s,"execution_authority":False,"read_only":True}
def run_forever(root,sleep_seconds=30):
 root=Path(root);state=RuntimeState(root);state.boot();n=0
 while True:
  try:
   r=cycle(root,state);n+=1;state.running(cycle_count=n,stage="IDLE_BETWEEN_CYCLES",**r["summary"])
  except KeyboardInterrupt:
   state.stopping();break
  except Exception as e:
   state.error(e);err=root/"runtime_state/solana_opportunities/profitability_runtime/last_error.txt";err.parent.mkdir(parents=True,exist_ok=True);err.write_text(traceback.format_exc(),encoding="utf-8")
  time.sleep(sleep_seconds)
def contract():
 return {"revision":"SSR_002","pipeline":PIPE,"continuous":True,"cycle_semantics":"CAPTURE_FREEZE_FOLLOW_EVALUATE_REPEAT","execution_authority":False,"read_only":True}
