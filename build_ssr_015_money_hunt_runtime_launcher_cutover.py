from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_015_launcher_contract.py"
LAUNCH=ROOT/"run_solana_scanner_live.py"
TEST=ROOT/"test_ssr_015_money_hunt_runtime_launcher_cutover.py"
MOD_TEXT=r"""from __future__ import annotations
def contract():
 return {"revision":"SSR_015","launcher":"run_solana_scanner_live.py",
  "primary_money_hunt_family":"PUMP_SWAP","continuous_pumpswap_exact_market_follow":True,
  "money_hunt_play_board":True,"execution_authority":False,"read_only":True}
"""
LAUNCH_TEXT=r"""from __future__ import annotations
import argparse,json,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_013_profit_hunt_worker import run_forever,cycle
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_014_money_hunt_play_board import build as board,format_board
ROOT=Path(__file__).resolve().parent
def serve(host,port):
 class H(BaseHTTPRequestHandler):
  def do_GET(self):
   path=self.path.split("?",1)[0];d=board(ROOT)
   if path=="/health":out={"service":"SOLANA_PROFITABILITY_SCANNER","status":"RUNNING","primary_family":d.get("primary_family"),"execution_authority":False}
   elif path=="/plays":out=d
   elif path=="/live":out={"money_hunt":d,"execution_authority":False}
   else:out={"error":"NOT_FOUND","available":["/health","/plays","/live"]}
   body=json.dumps(out,default=str).encode();self.send_response(200 if "error" not in out else 404)
   self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
  def log_message(self,*a):pass
 ThreadingHTTPServer((host,port),H).serve_forever()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--host",default="127.0.0.1");ap.add_argument("--port",type=int,default=8766)
 ap.add_argument("--sleep",type=int,default=30);ap.add_argument("--dry-run",action="store_true");args=ap.parse_args()
 state=RuntimeState(ROOT);state.boot()
 if args.dry_run:
  print(json.dumps(cycle(ROOT,state,dry_run=True),indent=2,sort_keys=True));print(format_board(ROOT));return
 threading.Thread(target=serve,args=(args.host,args.port),daemon=True).start()
 threading.Thread(target=run_forever,args=(ROOT,args.sleep),daemon=True).start()
 print(f"[API] http://{args.host}:{args.port}/plays")
 print("[RUNTIME] PumpSwap-first money hunt: capture -> freeze -> exact pool follow -> net evaluation")
 try:
  while True:print(format_board(ROOT));time.sleep(15)
 except KeyboardInterrupt:state.stopping();print("[STOPPED] Solana Profitability Scanner")
if __name__=="__main__":main()
"""
TEST_TEXT=r"""import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_launcher(self):
  p=ROOT/"run_solana_scanner_live.py";self.assertTrue(p.exists())
  r=subprocess.run([sys.executable,str(p),"--dry-run"],cwd=ROOT,capture_output=True,text=True,timeout=30)
  print(r.stdout);self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("PUMP_SWAP",r.stdout);self.assertIn("SOLANA MONEY HUNT",r.stdout);self.assertIn("execution_authority=FALSE",r.stdout)
  print("[PASS] SSR-015 PumpSwap-first money-hunt runtime launcher cutover")
  print("[RUN] python run_solana_scanner_live.py")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");LAUNCH.write_text(LAUNCH_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] launcher replaced:",LAUNCH.name);print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
