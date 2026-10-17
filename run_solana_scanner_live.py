from pathlib import Path
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
