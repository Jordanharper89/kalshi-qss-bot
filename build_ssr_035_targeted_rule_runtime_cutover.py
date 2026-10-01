from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_035_targeted_rule_runtime_worker.py";LAUNCH=ROOT/"run_solana_scanner_live.py";TEST=ROOT/"test_ssr_035_targeted_rule_runtime_cutover.py"
MOD_TEXT=r"""from __future__ import annotations
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
"""
LAUNCH_TEXT=r"""from pathlib import Path
import argparse,json,threading,time
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_035_targeted_rule_runtime_worker import run_forever,cycle
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_030_targeted_strategy_board import format_board
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_034_targeted_live_profit_gate import build as gate
ROOT=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--sleep",type=int,default=30)
 ap.add_argument("--dry-run",action="store_true")
 a=ap.parse_args();s=RuntimeState(ROOT);s.boot()
 if a.dry_run:
  print(json.dumps(cycle(ROOT,s,dry_run=True),indent=2))
  print(format_board(ROOT));return
 threading.Thread(target=run_forever,args=(ROOT,a.sleep),daemon=True).start()
 try:
  while True:
   print(format_board(ROOT))
   print("[LIVE_GATE]",json.dumps(gate(ROOT),sort_keys=True))
   time.sleep(15)
 except KeyboardInterrupt:s.stopping()
if __name__=="__main__":main()
"""
TEST_TEXT=r"""import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cutover(self):
  r=subprocess.run([sys.executable,str(ROOT/"run_solana_scanner_live.py"),"--dry-run"],
   cwd=ROOT,capture_output=True,text=True,timeout=30)
  print(r.stdout)
  self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("EVALUATE_TARGET",r.stdout)
  self.assertIn("TARGETED PUMP_SWAP STRATEGY HUNT",r.stdout)
  print("[PASS] SSR-035 targeted rule live runtime cutover")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
LAUNCH.write_text(LAUNCH_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] launcher replaced:",LAUNCH.name)
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")