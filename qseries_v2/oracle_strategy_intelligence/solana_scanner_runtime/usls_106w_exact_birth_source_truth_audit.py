from __future__ import annotations
import ast,json,re
from pathlib import Path

ULS="qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
SLS="qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"

def _funcs(src):
 try:t=ast.parse(src)
 except Exception:return []
 out=[]
 for n in ast.walk(t):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   out.append({"name":n.name,"args":[a.arg for a in n.args.args],
    "async":isinstance(n,ast.AsyncFunctionDef),"lineno":n.lineno})
 return out

def _interesting(src):
 keep=[]
 for i,line in enumerate(src.splitlines(),1):
  low=line.lower()
  if any(k in low for k in ("create_v2","discriminator","pump","birth","instruction","base58",
                              "decode","program_id","_birth(","is_birth(")):
   keep.append({"line":i,"text":line.rstrip()})
 return keep[:220]

def _scan(root,base,patterns):
 out=[]
 b=Path(root)/base
 for pat in patterns:
  for p in sorted(b.glob(pat)):
   src=p.read_text(encoding="utf-8",errors="ignore")
   out.append({"path":str(p.relative_to(root)),"functions":_funcs(src),
    "interesting":_interesting(src)})
 return out

def run(root):
 pump=_scan(root,ULS,["usls_020*.py","usls_021*.py","usls_022*.py","usls_023*.py","usls_024*.py"])
 meteora=_scan(root,SLS,["suls_067*.py","suls_067b*.py","suls_067c*.py"])
 pump_callable=[]
 for x in pump:
  for f in x["functions"]:
   if any(k in f["name"].lower() for k in ("birth","create","decode","exact","detect","match")):
    pump_callable.append({"path":x["path"],**f})
 meteora_callable=[]
 for x in meteora:
  for f in x["functions"]:
   if f["name"]=="_birth" or "birth" in f["name"].lower():
    meteora_callable.append({"path":x["path"],**f})
 return {"revision":"USLS_106W",
  "pump_source_count":len(pump),"meteora_source_count":len(meteora),
  "pump_candidate_callables":pump_callable,
  "meteora_candidate_callables":meteora_callable,
  "pump_sources":pump,"meteora_sources":meteora,
  "next_boundary":"EXACT_BIRTH_DISPATCH_USING_VERIFIED_EXISTING_SOURCE_CONTRACTS",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_exact_birth_source_truth_audit.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
