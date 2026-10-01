from __future__ import annotations
import time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162k_phase8_pump_fun_pumpswap_targeted_live_capture import write as capture
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162l_phase8_pump_targeted_freeze_extension import write as freeze
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_012_pumpswap_money_follower import run as follow
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_032_new_target_match_tracker import write as matches
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_034_targeted_live_profit_gate import write as gate
def cycle(root,state=None,dry_run=False):
 root=Path(root);state=state or RuntimeState(root)
 if dry_run:return {"pipeline":["CAPTURE","FREEZE","TRACK_TARGET","FOLLOW_PUMPSWAP","EVALUATE_TARGET"],"execution_authority":False}
 state.running(stage="TARGET_CAPTURE");_,a=capture(root)
 state.running(stage="TARGET_FREEZE");_,b=freeze(root)
 _,m=matches(root)
 state.running(stage="TARGET_FOLLOW",new_target_matches=m["new_live_match_count"]);f=follow(root)
 state.running(stage="TARGET_EVALUATE");_,g=gate(root)
 return {"capture":a,"freeze":b,"matches":m,"follow":f,"gate":g,"execution_authority":False}
def run_forever(root,sleep_seconds=30):
 root=Path(root);s=RuntimeState(root);s.boot();n=0
 while True:
  try:
   r=cycle(root,s);n+=1
   s.running(cycle_count=n,stage="IDLE",target_state=r["gate"]["state"],
    target_cases=r["gate"]["targeted_case_count"],
    post_activation_cases=r["gate"]["post_activation_case_count"])
  except KeyboardInterrupt:s.stopping();break
  except Exception as e:s.error(e)
  time.sleep(sleep_seconds)
