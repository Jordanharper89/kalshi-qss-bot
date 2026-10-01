from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_005_launcher_contract.py"
LAUNCH=ROOT/"run_solana_scanner_live.py"
TEST=ROOT/"test_ssr_005_solana_profitability_runtime_launcher.py"
MOD_TEXT=r"""from __future__ import annotations
def contract():
 return {"revision":"SSR_005","launcher":"run_solana_scanner_live.py","service":"SOLANA_PROFITABILITY_SCANNER",
  "standalone":True,"api_port_default":8766,"profit_hunt_worker":True,"native_api":True,
  "terminal_profitability_surface":True,"execution_authority":False,"read_only":True}
"""
LAUNCH_TEXT=r"""from __future__ import annotations
import argparse,json,threading,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_002_profit_hunt_worker import run_forever,cycle
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_003_profitability_intelligence import write as write_intel
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_004_native_api import serve
ROOT=Path(__file__).resolve().parent
def line(d):
 print("="*108);print(" SOLANA PROFITABILITY SCANNER | READ-ONLY | execution_authority=FALSE");print("="*108)
 print(" status=",d.get("play_state")," prospective_cases=",d.get("prospective_case_count")," friction_supported=",d.get("friction_supported_case_count"))
 print(" gross_mean=",d.get("gross_mean")," gross_positive_frequency=",d.get("gross_positive_frequency"))
 print(" mean_net_return=",d.get("mean_net_forward_return")," net_status=",d.get("net_expectancy_status"))
 print(" money_question=",d.get("money_question"));print("="*108)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--host",default="127.0.0.1");ap.add_argument("--port",type=int,default=8766)
 ap.add_argument("--sleep",type=int,default=30);ap.add_argument("--dry-run",action="store_true");args=ap.parse_args()
 state=RuntimeState(ROOT);state.boot()
 if args.dry_run:
  print(json.dumps(cycle(ROOT,state,dry_run=True),indent=2,sort_keys=True));_,d=write_intel(ROOT);line(d);return
 threading.Thread(target=serve,args=(ROOT,args.host,args.port),daemon=True).start()
 print(f"[API] http://{args.host}:{args.port}/health")
 print("[RUNTIME] continuous capture -> freeze -> exact-market follow -> learning -> net-edge evaluation")
 threading.Thread(target=run_forever,args=(ROOT,args.sleep),daemon=True).start()
 try:
  while True:
   _,d=write_intel(ROOT);line(d);time.sleep(15)
 except KeyboardInterrupt:
  state.stopping();print("[STOPPED] Solana Profitability Scanner")
if __name__=="__main__":main()
"""
TEST_TEXT=r"""import subprocess,sys,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_005_launcher_contract import contract
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_launcher(self):
  c=contract();p=ROOT/c["launcher"];self.assertTrue(p.exists())
  r=subprocess.run([sys.executable,str(p),"--dry-run"],cwd=ROOT,capture_output=True,text=True,timeout=30)
  print(r.stdout);self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("SOLANA PROFITABILITY SCANNER",r.stdout);self.assertIn("execution_authority",r.stdout);self.assertFalse(c["execution_authority"])
  print("[PASS] SSR-005 standalone Solana profitability runtime launcher")
  print("[RUN] python run_solana_scanner_live.py")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");LAUNCH.write_text(LAUNCH_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] launcher:",LAUNCH.name);print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")