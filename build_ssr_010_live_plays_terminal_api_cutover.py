from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_010_live_plays_surface.py"
LAUNCH=ROOT/"run_solana_scanner_live.py"
TEST=ROOT/"test_ssr_010_live_plays_terminal_api_cutover.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_003_profitability_intelligence import build as profitability
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_009_play_gate import build as live_plays
def snapshot(root):
 return {"profitability":profitability(root),"plays":live_plays(root),"execution_authority":False,"read_only":True}
def format_terminal(root,limit=6):
 s=snapshot(root);p=s["profitability"];plays=s["plays"];lines=[]
 lines+=["="*118," SOLANA PROFITABILITY SCANNER | LIVE PLAYS | READ-ONLY | execution_authority=FALSE","="*118]
 lines.append(f" prospective_cases={p.get('prospective_case_count')}  friction_supported={p.get('friction_supported_case_count')}  gross_mean={p.get('gross_mean')}  gross_positive_frequency={p.get('gross_positive_frequency')}")
 lines.append(f" mean_net_return={p.get('mean_net_forward_return')}  net_status={p.get('net_expectancy_status')}")
 lines.append(f" READY={plays.get('ready_count')}  OBSERVE={plays.get('observe_count')}  ABSTAIN={plays.get('abstain_count')}")
 lines.append("-"*118)
 if not plays.get("plays"):
  lines.append(" NO LIVE PLAYS YET — waiting for the next live decoded capture.")
 else:
  for x in plays["plays"][:limit]:
   net=x.get("estimated_net_edge_from_family_oos");gross=x.get("historical_mean_gross_return")
   lines.append(f" #{x.get('rank','?')} {x['play_state']} | {x['family']} | pool={x['market_address']}")
   lines.append(f"    pair={x.get('input_asset')} -> {x.get('output_asset')} | live_trades={x.get('live_trade_count')} | age={x.get('age_seconds',0):.1f}s")
   lines.append(f"    live_move={x.get('current_capture_move')} | OOS_n={x.get('historical_oos_sample_size')} | OOS_mean_gross={gross} | OOS_positive_freq={x.get('historical_positive_frequency')}")
   lines.append(f"    friction={x.get('modeled_round_trip_friction')} | estimated_net_edge={net} | reason={x.get('play_reason')}")
   lines.append("-"*118)
 lines.append("="*118);return "\n".join(lines)
"""
LAUNCH_TEXT=r"""from __future__ import annotations
import argparse,json,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_002_profit_hunt_worker import run_forever,cycle
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_010_live_plays_surface import snapshot,format_terminal
ROOT=Path(__file__).resolve().parent
def serve(host,port):
 class H(BaseHTTPRequestHandler):
  def do_GET(self):
   s=snapshot(ROOT);path=self.path.split("?",1)[0]
   if path=="/health":d={"service":"SOLANA_PROFITABILITY_SCANNER","status":"RUNNING","execution_authority":False}
   elif path=="/live":d=s
   elif path=="/plays":d=s["plays"]
   elif path=="/learning":d={"family_groups":s["profitability"].get("family_groups"),"prospective_case_count":s["profitability"].get("prospective_case_count"),"execution_authority":False}
   elif path=="/reasoning":d={"money_question":s["profitability"].get("money_question"),"net_expectancy_status":s["profitability"].get("net_expectancy_status"),"execution_authority":False}
   else:d={"error":"NOT_FOUND","available":["/health","/live","/plays","/learning","/reasoning"]}
   body=json.dumps(d,default=str).encode();self.send_response(200 if "error" not in d else 404);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
  def log_message(self,*a):pass
 ThreadingHTTPServer((host,port),H).serve_forever()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--host",default="127.0.0.1");ap.add_argument("--port",type=int,default=8766);ap.add_argument("--sleep",type=int,default=30);ap.add_argument("--dry-run",action="store_true");args=ap.parse_args()
 state=RuntimeState(ROOT);state.boot()
 if args.dry_run:
  print(json.dumps(cycle(ROOT,state,dry_run=True),indent=2,sort_keys=True));print(format_terminal(ROOT));return
 threading.Thread(target=serve,args=(args.host,args.port),daemon=True).start()
 threading.Thread(target=run_forever,args=(ROOT,args.sleep),daemon=True).start()
 print(f"[API] http://{args.host}:{args.port}/plays")
 print("[RUNTIME] live plays will refresh automatically while profit-hunt worker runs")
 try:
  while True:print(format_terminal(ROOT));time.sleep(15)
 except KeyboardInterrupt:state.stopping();print("[STOPPED] Solana Profitability Scanner")
if __name__=="__main__":main()
"""
TEST_TEXT=r"""import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cutover(self):
  p=ROOT/"run_solana_scanner_live.py";self.assertTrue(p.exists())
  r=subprocess.run([sys.executable,str(p),"--dry-run"],cwd=ROOT,capture_output=True,text=True,timeout=30)
  print(r.stdout);self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("LIVE PLAYS",r.stdout);self.assertIn("READY=",r.stdout);self.assertIn("OBSERVE=",r.stdout)
  self.assertIn("execution_authority=FALSE",r.stdout)
  print("[PASS] SSR-010 live plays terminal + /plays API cutover")
  print("[RUN] python run_solana_scanner_live.py")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");LAUNCH.write_text(LAUNCH_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] launcher replaced:",LAUNCH.name);print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
