from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_003_profitability_intelligence import build as intelligence
STATE="runtime_state/solana_opportunities/profitability_runtime/runtime_state.json"
LED="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
def _load(root,rel):
 p=Path(root)/rel
 if not p.exists():return {}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}
def payload(root,path):
 root=Path(root);intel=intelligence(root);state=_load(root,STATE);led=_load(root,LED)
 if path=="/health":return {"service":"SOLANA_PROFITABILITY_SCANNER","status":state.get("status","OFFLINE"),"heartbeat_unix":state.get("heartbeat_unix"),"execution_authority":False}
 if path=="/live":return {"runtime":state,"profitability":intel,"execution_authority":False}
 if path=="/learning":return {"prospective_case_count":intel["prospective_case_count"],"family_groups":intel["family_groups"],"execution_authority":False}
 if path=="/reasoning":return {"money_question":intel["money_question"],"net_expectancy_status":intel["net_expectancy_status"],"play_state":intel["play_state"],"execution_authority":False}
 if path=="/plays":return {"state":intel["play_state"],"mean_net_forward_return":intel["mean_net_forward_return"],"friction_supported_case_count":intel["friction_supported_case_count"],"profitability_claimed":False,"execution_authority":False}
 if path=="/outcomes":return {"case_count":len(led.get("cases") or []),"cases":led.get("cases") or [],"execution_authority":False}
 return {"error":"NOT_FOUND","available":["/health","/live","/learning","/reasoning","/plays","/outcomes"]}
def serve(root,host="127.0.0.1",port=8766):
 root=Path(root)
 class H(BaseHTTPRequestHandler):
  def do_GET(self):
   d=payload(root,self.path.split("?",1)[0]);body=json.dumps(d,default=str).encode()
   self.send_response(200 if "error" not in d else 404);self.send_header("Content-Type","application/json")
   self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
  def log_message(self,*a):pass
 ThreadingHTTPServer((host,port),H).serve_forever()
def contract():
 return {"revision":"SSR_004","host_default":"127.0.0.1","port_default":8766,
  "endpoints":["/health","/live","/learning","/reasoning","/plays","/outcomes"],
  "execution_authority":False,"read_only":True}
