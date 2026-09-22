from __future__ import annotations
import json,time,urllib.request
from pathlib import Path
from .usls_006_verified_mainnet_program_registry import RPC

def _rpc(pid):
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress",
  "params":[pid,{"limit":3,"commitment":"confirmed"}]}).encode()
 req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=12) as r:
   d=json.loads(r.read());return d.get("result") or [],None
 except Exception as e:return [],type(e).__name__+":"+str(e)

def probe(root):
 reg=json.loads((Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/verified_mainnet_program_registry.json").read_text(encoding="utf-8"))
 now=time.time();rows=[]
 for x in reg["programs"]:
  sigs,err=_rpc(x["program_id"])
  bt=max((s.get("blockTime") or 0 for s in sigs),default=0)
  rows.append({"family":x["family"],"program_id":x["program_id"],"query_ok":err is None,
   "recent_signature_count":len(sigs),"latest_block_time":bt or None,
   "latest_age_seconds":(now-bt) if bt else None,"error":err})
 return {"revision":"USLS_007","program_count":len(rows),
  "query_success_count":sum(1 for x in rows if x["query_ok"]),
  "programs_with_recent_signatures":sum(1 for x in rows if x["recent_signature_count"]>0),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=probe(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/recent_program_activity.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
