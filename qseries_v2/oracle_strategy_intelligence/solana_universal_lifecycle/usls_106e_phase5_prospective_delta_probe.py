from __future__ import annotations
import json,time
from pathlib import Path

def read(p): return json.loads(p.read_text(encoding="utf-8"))

def rows(d,key=None):
 if key and isinstance(d.get(key),list): return d[key]
 for k in ("events","rows","exact_rows","trades","births"):
  if isinstance(d.get(k),list): return d[k]
 return []

def sig(x): return str(x.get("signature")) if isinstance(x,dict) and x.get("signature") else None

def build(root):
 root=Path(root)
 bdir=root/"runtime_state/solana_opportunities/universal_lifecycle"
 boot=read(bdir/"phase5_prospective_shared_cohort_bootstrap.json")
 bp=root/boot["birth_source"]["path"]
 bd=read(bp); br=rows(bd,boot["birth_source"].get("list_key"))
 old_b=set(boot.get("birth_baseline_signatures") or [])
 new_b=[x for x in br if sig(x) and sig(x) not in old_b]
 trade=[]
 for src in boot["trade_sources"]:
  p=root/src["path"]
  if not p.exists():
   trade.append({"path":src["path"],"exists":False,"new_count":0,"rows":[]}); continue
  d=read(p); rs=rows(d,src.get("list_key")); old=set(src.get("signatures") or [])
  nr=[x for x in rs if sig(x) and sig(x) not in old]
  trade.append({"path":src["path"],"exists":True,"revision":d.get("revision"),
   "current_count":len(rs),"baseline_count":src.get("row_count",0),"new_count":len(nr),"rows":nr})
 return {"revision":"USLS_106E","probe_unix":time.time(),
  "birth_current_count":len(br),"birth_baseline_count":boot["birth_source"]["row_count"],
  "new_birth_count":len(new_b),"new_births":new_b,
  "trade_sources":trade,"new_trade_count":sum(x["new_count"] for x in trade),
  "shared_cohort_activity_present":bool(new_b and any(x["new_count"] for x in trade)),
  "state":"PROSPECTIVE_ACTIVITY_PRESENT" if (new_b or any(x["new_count"] for x in trade)) else "WAITING_FOR_POST_BOOTSTRAP_ACTIVITY",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_prospective_delta_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
